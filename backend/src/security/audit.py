import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(
    "security.audit"
)

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    )
)


# -----------------------------------
# REGISTRAR EVENTO AUDITORIA
# -----------------------------------
async def register_audit_event(
    db: AsyncSession,
    action: str,
    result: str,
    ip_address: str,
    usuario_id: int | None = None,
    details: str | None = None
):

    usuario_id_int = None

    if usuario_id is not None:
        usuario_id_int = int(usuario_id)

    logger.info(
        (
            f"AUDIT "
            f"user={usuario_id} "
            f"action={action} "
            f"result={result} "
            f"ip={ip_address}"
        )
    )

    await db.execute(
        text("""
            INSERT INTO audit_logs
            (
                usuario_id,
                accion,
                resultado,
                detalle,
                ip_address,
                fecha
            )
            VALUES
            (
                :usuario_id,
                :action,
                :result,
                :details,
                :ip_address,
                NOW()
            )
        """),
        {
            "usuario_id": usuario_id_int,
            "action": action,
            "result": result,
            "details": details,
            "ip_address": ip_address
        }
    )

    await db.commit()

# -----------------------------------
# EVENTO LOGIN EXITOSO
# -----------------------------------
async def audit_login_success(
    db: AsyncSession,
    usuario_id: str,
    ip_address: str
):

    await register_audit_event(
        db=db,
        usuario_id=usuario_id,
        action="LOGIN_SUCCESS",
        result="SUCCESS",
        ip_address=ip_address
    )

# -----------------------------------
# EVENTO LOGIN FALLIDO
# -----------------------------------
async def audit_login_failure(
    db: AsyncSession,
    ip_address: str,
    details: str = "INVALID_CREDENTIALS"
):

    await register_audit_event(
        db=db,
        usuario_id=None,
        action="LOGIN_FAILURE",
        result="FAILED",
        details=details,
        ip_address=ip_address
    )

# -----------------------------------
# EVENTO MFA
# -----------------------------------
async def audit_mfa_event(
    db: AsyncSession,
    usuario_id: str,
    ip_address: str,
    result: str
):

    await register_audit_event(
        db=db,
        usuario_id=usuario_id,
        action="MFA_VALIDATION",
        result=result,
        ip_address=ip_address
    )

# -----------------------------------
# EVENTO LOGOUT
# -----------------------------------
async def audit_logout(
    db: AsyncSession,
    usuario_id: str,
    ip_address: str
):

    await register_audit_event(
        db=db,
        usuario_id=usuario_id,
        action="LOGOUT",
        result="SUCCESS",
        ip_address=ip_address
    )

# -----------------------------------
# EVENTO ACCESO DENEGADO
# -----------------------------------
async def audit_access_denied(
    db: AsyncSession,
    usuario_id: str,
    ip_address: str,
    details: str
):

    await register_audit_event(
        db=db,
        usuario_id=usuario_id,
        action="ACCESS_DENIED",
        result="FAILED",
        details=details,
        ip_address=ip_address
    )