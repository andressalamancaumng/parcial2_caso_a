from fastapi import APIRouter, Depends, HTTPException
from src.auth.rbac import verify_role
import sqlite3
import bleach

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
from pydantic import BaseModel
import os, asyncio
from src.services.auth_service import AuthService

auth_svc = AuthService()

class LoginPayload(BaseModel):
    document_number: str
    password: str

@router.post("/login")
async def login(payload: LoginPayload):
    user = await auth_svc.authenticate_user(payload.document_number, payload.password)
    if not user:
        await auth_svc.log_failed_login(payload.document_number)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if user.get("mfa_enabled"):
        token = auth_svc.create_partial_token(user["id"])
        return {"session_token": token, "mfa_required": True, "expires_in": int(os.getenv("PARTIAL_TOKEN_EXPIRE_SECONDS", "300"))}
    access_token = auth_svc.create_access_token(user["id"], user["role"])
    return {"access_token": access_token, "token_type": "bearer", "mfa_required": False}