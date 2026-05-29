from datetime import datetime, timedelta

import random
import secrets
import string

from fastapi import HTTPException, status

from passlib.context import CryptContext

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import RegisterRequest

from src.auth.validation import (
    validate_password_policy
)

from src.security.jwt_manager import (
    create_access_token,
    decode_token
)

from src.security.blacklist import (
    add_token_to_blacklist
)

from src.security.audit import register_audit_event

from src.services.service import (
    send_initial_credentials_email
)

import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

MAX_LOGIN_ATTEMPTS = 5
BLOCK_MINUTES = 10


# =========================================================
# HASH PASSWORD
# =========================================================
def hash_password(password: str):

    validate_password_policy(password)

    return pwd_context.hash(password)


# =========================================================
# VERIFY PASSWORD
# =========================================================
def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# =========================================================
# GENERAR PASSWORD TEMPORAL
# =========================================================
def generate_temporary_password(
    length: int = 12
):

    if length < 8:
        length = 8

    uppercase = secrets.choice(
        string.ascii_uppercase
    )
    
    lowercase = secrets.choice(
        string.ascii_lowercase
    )

    number = secrets.choice(
        string.digits
    )

    special = secrets.choice(
        "@$!%*?&"
    )

    remaining_length = length - 4

    all_characters = (
        string.ascii_letters
        + string.digits
        + "@$!%*?&"
    )

    remaining = [
        secrets.choice(all_characters)
        for _ in range(remaining_length)
    ]

    password_list = [
        uppercase,
        lowercase,
        number,
        special
    ] + remaining

    random.SystemRandom().shuffle(
        password_list
    )

    temporary_password = "".join(
        password_list
    )

    validate_password_policy(
        temporary_password
    )

    return temporary_password


# =========================================================
# REGISTRAR PACIENTE
# =========================================================
async def register_patient_user(
    db: AsyncSession,
    data: RegisterRequest,
    created_by: int,
    ip_address: str
):

    existing_result = await db.execute(
        text("""
            SELECT id
            FROM usuarios
            WHERE email = :email
               OR numero_documento = :numero_documento
            LIMIT 1
        """),
        {
            "email": data.email,
            "numero_documento": data.numero_documento
        }
    )

    existing_user = existing_result.fetchone()

    if existing_user:
        return None

    role_result = await db.execute(
        text("""
            SELECT id
            FROM roles
            WHERE nombre = 'paciente'
            LIMIT 1
        """)
            )

    role = role_result.fetchone()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rol paciente no configurado"
        )

    temporary_password = generate_temporary_password()

    password_hash = hash_password(
        temporary_password
    )

    user_result = await db.execute(
        text("""
            INSERT INTO usuarios
            (
                tipo_documento,
                numero_documento,
                nombres,
                apellidos,
                fecha_nacimiento,
                sexo_biologico,
                grupo_sanguineo,
                telefono,
                email,
                password_hash,
                rol_id,
                activo,
                debe_cambiar_password,
                password_temporal_expira,
                created_at
            )
            VALUES
            (
                :tipo_documento,
                :numero_documento,
                :nombres,
                :apellidos,
                :fecha_nacimiento,
                :sexo_biologico,
                :grupo_sanguineo,
                :telefono,
                :email,
                :password_hash,
                :rol_id,
                true,
                true,
                NOW() + INTERVAL '48 hours',
                NOW()
            )
            RETURNING id
        """),
        {
            "tipo_documento": data.tipo_documento,
            "numero_documento": data.numero_documento,
            "nombres": data.nombres,
            "apellidos": data.apellidos,
            "fecha_nacimiento": data.fecha_nacimiento,
            "sexo_biologico": data.sexo_biologico,
            "grupo_sanguineo": data.grupo_sanguineo,
            "telefono": data.telefono,
            "email": data.email,
            "password_hash": password_hash,
            "rol_id": role.id
        }
    )

    user = user_result.fetchone()

    patient_result = await db.execute(
        text("""
            INSERT INTO pacientes
            (
                usuario_id,
                numero_historia,
                fecha_apertura,
                estado
            )
            VALUES
            (
                             :usuario_id,
                :numero_historia,
                NOW(),
                'ACTIVA'
            )
            RETURNING id
        """),
        {
            "usuario_id": user.id,
            "numero_historia": f"HC-{user.id}"
        }
    )

    patient = patient_result.fetchone()

    await db.execute(
        text("""
            INSERT INTO historias_clinicas
            (
                paciente_id,
                created_at,
                created_by,
                ip_creacion
            )
            VALUES
            (
                :paciente_id,
                NOW(),
                :created_by,
                :ip_address
            )
        """),
        {
            "paciente_id": patient.id,
            "created_by": created_by,
            "ip_address": ip_address
        }
    )

    await db.commit()

    try:

        send_initial_credentials_email(
            recipient_email=data.email,
            full_name=(
                f"{data.nombres} "
                f"{data.apellidos}"
            ),

        )

        await register_audit_event(
            db=db,
            usuario_id=user.id,
            action="SEND_INITIAL_CREDENTIALS",
            result="SUCCESS",
            ip_address=ip_address
        )

    except Exception as e:

        logger.error(
            f"EMAIL_ERROR: {str(e)}"
        )

        await register_audit_event(
            db=db,
            usuario_id=user.id,
            action="SEND_INITIAL_CREDENTIALS",
            result="FAILED",
            details=str(e),
            ip_address=ip_address
        )

    return {
        "message": "Paciente registrado",
        "detail": "Las credenciales fueron enviadas al correo registrado."
    }

# =========================================================
# VALIDAR BLOQUEO LOGIN
# =========================================================
async def check_login_block(
    db: AsyncSession,
    user_id: int
):

    result = await db.execute(
        text("""
            SELECT
                attempts,
                bloqueado_hasta
            FROM login_attempts
            WHERE usuario_id = :user_id
            LIMIT 1
        """),
        {
            "user_id": user_id
        }
    )

    row = result.fetchone()

    if not row:
        return

    if (
        row.bloqueado_hasta
        and row.bloqueado_hasta > datetime.utcnow()
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Cuenta temporalmente bloqueada"
            )
        )


# =========================================================
# REGISTRAR INTENTO FALLIDO
# =========================================================
async def register_failed_attempt(
    db: AsyncSession,
    user_id: int,
    ip_address: str
):

    result = await db.execute(
        text("""
            SELECT attempts
            FROM login_attempts
            WHERE usuario_id = :user_id
            LIMIT 1
        """),
        {
            "user_id": user_id
        }
    )

    row = result.fetchone()

    if not row:

        await db.execute(
            text("""
                INSERT INTO login_attempts
                (
                    usuario_id,
                    attempts,
                    ultimo_intento,
                    bloqueado_hasta,
                    ip_address
                )
                VALUES
                (
                    :usuario_id,
                    1,
                    NOW(),
                    NULL,
                    :ip_address
                )
            """),
            {
                "usuario_id": user_id,
                "ip_address": ip_address
                            }
        )

    else:

        new_attempts = row.attempts + 1

        blocked_until = None

        if new_attempts >= MAX_LOGIN_ATTEMPTS:

            blocked_until = (
                datetime.utcnow()
                + timedelta(minutes=BLOCK_MINUTES)
            )

        await db.execute(
            text("""
                UPDATE login_attempts
                SET
                    attempts = :attempts,
                    ultimo_intento = NOW(),
                    bloqueado_hasta = :blocked_until,
                    ip_address = :ip_address
                WHERE usuario_id = :user_id
            """),
            {
                "attempts": new_attempts,
                "blocked_until": blocked_until,
                "ip_address": ip_address,
                "user_id": user_id
            }
        )

    await db.commit()


# =========================================================
# RESET LOGIN ATTEMPTS
# =========================================================
async def reset_login_attempts(
    db: AsyncSession,
    user_id: int
):

    await db.execute(
        text("""
            DELETE FROM login_attempts
            WHERE usuario_id = :user_id
        """),
        {
            "user_id": user_id
        }
    )

    await db.commit()


# =========================================================
# LOGIN
# =========================================================
async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: str
):

    result = await db.execute(
        text("""
            SELECT
                u.id,
                u.password_hash,
                u.mfa_habilitado,
                u.debe_cambiar_password,
                u.password_temporal_expira,
                r.nombre AS role
            FROM usuarios u
            INNER JOIN roles r
                ON r.id = u.rol_id
            WHERE u.email = :email
              AND u.activo = true
            LIMIT 1
        """),
                {
            "email": email
        }
    )

    user = result.fetchone()

    fake_hash = pwd_context.hash(
        "fake_password"
    )

    stored_hash = (
        user.password_hash
        if user
        else fake_hash
    )

    valid_password = verify_password(
        password,
        stored_hash
    )

    if user:

        await check_login_block(
            db,
            user.id
        )

    # =====================================================
    # CREDENCIALES INVALIDAS
    # =====================================================
    if not user or not valid_password:

        if user:

            await register_failed_attempt(
                db,
                user.id,
                ip_address
            )

        return {
            "success": False,
            "password_expired": False
        }

    await reset_login_attempts(
        db,
        user.id
    )

    # =====================================================
    # PASSWORD TEMPORAL EXPIRADO
    # =====================================================
    if (
        user.debe_cambiar_password
        and user.password_temporal_expira
        and datetime.utcnow()
            > user.password_temporal_expira
    ):

        return {
            "success": False,
            "password_expired": True
        }

    # =====================================================
    # CAMBIO OBLIGATORIO PASSWORD
    # =====================================================
    if user.debe_cambiar_password:

        temporary_token = create_access_token(
            {
                "sub": str(user.id),
                "role": user.role,
                "password_change_required": True
            },
            expires_minutes=15
        )

        return {
            "success": True,
            "token": temporary_token,
                 "requires_password_change": True,
            "requires_mfa": False,
            "password_expired": False
        }

    # =====================================================
    # MFA
    # =====================================================
    if user.mfa_habilitado:

        mfa_token = create_access_token(
            {
                "sub": str(user.id),
                "role": user.role,
                "mfa_pending": True
            },
            expires_minutes=5
        )

        return {
            "success": True,
            "token": mfa_token,
            "requires_mfa": True,
            "requires_password_change": False,
            "password_expired": False
        }

    # =====================================================
    # LOGIN NORMAL
    # =====================================================
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role
        }
    )

    await audit_login_success(
        db=db,
        usuario_id=str(user.id),
        ip_address=ip_address
    )

    return {
        "success": True,
        "token": access_token,
        "requires_mfa": False,
        "requires_password_change": False,
        "password_expired": False
    }


# =========================================================
# LOGOUT
# =========================================================
async def logout_user(
    db: AsyncSession,
    token: str
):

    payload = decode_token(
        token
    )

    await add_token_to_blacklist(
        db,
        payload["jti"]
    )