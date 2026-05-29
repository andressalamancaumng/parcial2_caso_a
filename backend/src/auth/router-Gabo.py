from fastapi import APIRouter, Depends, HTTPException, Body
from src.auth.rbac import verify_role
import sqlite3
import bleach
from pydantic import BaseModel
import os
import asyncio

router = APIRouter()
DATABASE = "clinica.db"

# ---------------------------
# OBTENER HISTORIA CLÍNICA
# ---------------------------
@router.get("/historia/{cedula_paciente}")
def obtener_historia(
    cedula_paciente: str,
    user=Depends(verify_role(["ROLE_MEDICO", "ROLE_ADMIN"]))
):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 🔐 Verificar que el médico tenga asignado el paciente
    cursor.execute("""
        SELECT 1 FROM asignaciones
        WHERE medico_id = ? AND paciente_id = ?
    """, (user["sub"], cedula_paciente))

    autorizado = cursor.fetchone()

    if not autorizado and user["role"] != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="No autorizado")

    # ✅ Consulta segura (sin SQL injection)
    cursor.execute("""
        SELECT contenido, fecha FROM historias_clinicas
        WHERE cedula_paciente = ?
    """, (cedula_paciente,))

    historia = cursor.fetchall()
    conn.close()

    return {"historia": historia}


# ---------------------------
# AGREGAR NOTA (SANITIZADA)
# ---------------------------
@router.post("/historia/{cedula_paciente}/nota")
def agregar_nota(
    cedula_paciente: str,
    nota: dict,
    user=Depends(verify_role(["ROLE_MEDICO"]))
):

    contenido = nota.get("contenido", "")
    fecha = nota.get("fecha", "")

    # 🛡 Sanitización contra XSS
    contenido_seguro = bleach.clean(contenido)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 🔐 Validar asignación médico-paciente
    cursor.execute("""
        SELECT 1 FROM asignaciones
        WHERE medico_id = ? AND paciente_id = ?
    """, (user["sub"], cedula_paciente))

    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="No autorizado")

    # ✅ Query segura
    cursor.execute("""
        INSERT INTO notas_clinicas (cedula_paciente, contenido, fecha)
        VALUES (?, ?, ?)
    """, (cedula_paciente, contenido_seguro, fecha))

    conn.commit()
    conn.close()

    return {"mensaje": "Nota agregada correctamente"}


# ---------------------------
# BÚSQUEDA SEGURA
# ---------------------------
@router.get("/pacientes/buscar")
def buscar_pacientes(
    nombre: str = "",
    user=Depends(verify_role(["ROLE_ADMIN", "ROLE_MEDICO"]))
):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cedula, nombre
        FROM pacientes
        WHERE nombre LIKE ?
    """, (f"%{nombre}%",))

    resultados = cursor.fetchall()
    conn.close()

    return {"pacientes": resultados}

from fastapi import Body
from src.services.auth_service import AuthService

auth_svc = AuthService()

class LoginPayload(BaseModel):
    document_number: str
    password: str

@router.post("/login")
def login(payload: LoginPayload):
    user = asyncio.run(auth_svc.authenticate_user(payload.document_number, payload.password))
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    # si el usuario tiene MFA activado emite token parcial (para flujo MFA)
    if user.get("mfa_enabled"):
        token = auth_svc.create_partial_token(user["id"])
        return {"session_token": token, "mfa_required": True, "expires_in": int(os.getenv("PARTIAL_TOKEN_EXPIRE_SECONDS","300"))}
    access_token = auth_svc.create_access_token(user["id"], user["role"])
    return {"access_token": access_token, "token_type": "bearer", "mfa_required": False}

from base64 import b64encode
from src.services.mfa_service import MFAService
from src.services.rate_limit import RateLimiter

mfa_svc = MFAService()
rate_limiter = RateLimiter(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class MfaTokenBody(BaseModel):
    token: str

class MfaVerifyBody(BaseModel):
    session_token: str
    otp_code: str

@router.post("/mfa/setup/totp")
def mfa_setup_totp(body: MfaTokenBody = Body(...)):
    # requiere token full (demo usa token en body). Decodifica y valida:
    try:
        user = asyncio.run(auth_svc.get_current_user(body.token))
    except HTTPException as e:
        raise HTTPException(status_code=401, detail="Token inválido o faltante")
    if user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA ya activado")
    secret = mfa_svc.generate_secret()
    qr_png = mfa_svc.generate_qr_png(user["email"], secret)
    # almacenar secreto cifrado
    auth_svc.store_encrypted_totp_secret(user["id"], secret)
    return {"qr_base64": b64encode(qr_png).decode(), "note": "QR mostrado una sola vez. Verifícalo con el primer OTP."}

@router.post("/mfa/verify")
async def mfa_verify(body: MfaVerifyBody):
    # rate-limit por session_token
    if await rate_limiter.is_blocked(body.session_token):
        raise HTTPException(status_code=429, detail="Demasiados intentos, intente luego")
    session = auth_svc.verify_partial_token(body.session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Session token inválido o expirado")
    user_id = session["sub"]
    secret = auth_svc.get_encrypted_totp_secret(user_id)
    if not secret:
        raise HTTPException(status_code=400, detail="MFA no configurado")
    if not mfa_svc.verify_otp(secret, body.otp_code):
        await rate_limiter.register_failure(body.session_token)
        raise HTTPException(status_code=401, detail="OTP inválido")
    await rate_limiter.reset(body.session_token)
    user = auth_svc.get_user_by_id(user_id)
    access_token = auth_svc.create_access_token(user_id, user["role"])
    if not user.get("mfa_enabled"):
        auth_svc.set_mfa_enabled(user_id, True)
    return {"access_token": access_token, "token_type": "bearer"}