"""
Router de historias clínicas — con vulnerabilidades intencionales
"""
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text
import sqlite3
from src.auth.service import decode_token
import bleach  # importado pero no usado — los estudiantes deben usarlo
from fastapi import APIRouter, Depends, HTTPException, Header

router = APIRouter()

@router.get("/historia/{cedula_paciente}")
async def obtener_historia(cedula_paciente: str, authorization: str = Header(None)):
   
   if authorization is None:
    raise HTTPException(401, "Token requerido")

    # Validar formato Bearer
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Formato de token inválido. Use 'Bearer {token}'")

    token = authorization.split(" ")[1]  # Extrae solo el token
    if not token:
        raise HTTPException(401, "Token vacío")

        try:
         payload = decode_token(token)
        except ValueError as e:
         raise HTTPException(401, str(e))
   
   
    #if authorization is None:
    #    raise HTTPException(401, "Token requerido")
    #try:
    #    payload = decode_token(authorization)
    #except Exception as e:
        # ← VULNERABLE: expone detalles del error
     #   raise HTTPException(401, f"Token inválido: {str(e)}")

# historias/router.py - función obtener_historia()
# Usar dependency injection con roles definidos en constante
ROLES_AUTORIZADOS = {"ROLE_MEDICO", "ROLE_ADMIN", "ROLE_AUDITOR"}

def require_role(*roles: str):
    async def dependency(authorization: str = Header(None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Token requerido")
        
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        
        # Normalizar y verificar rol
        user_role = payload.get("role", "").upper()
        if user_role not in roles and user_role not in ROLES_AUTORIZADOS:
            raise HTTPException(403, "Sin permisos")
        
        return payload
    return dependency

# Uso en endpoint:
@router.get("/historia/{cedula_paciente}")
async def obtener_historia(
    cedula_paciente: str,
    current_user: dict = Depends(require_role("ROLE_MEDICO", "ROLE_ADMIN"))
):
    
    # ← VULNERABLE: cualquier médico ve cualquier paciente (sin verificar asignación)
   # if payload.get("role") not in ["ROLE_MEDICO", "ROLE_ADMIN"]:
    #    raise HTTPException(403, "Sin permisos")

    conn = sqlite3.connect("clinica.db")
    cursor = conn.cursor()
    # ← VULNERABLE: SQL injection por concatenación
    cursor.execute(
        f"SELECT * FROM historias_clinicas WHERE cedula_paciente = '{cedula_paciente}'"
    )
    historia = cursor.fetchall()
    conn.close()
    return {"historia": historia}


@router.post("/historia/{cedula_paciente}/nota")
async def agregar_nota(cedula_paciente: str, nota: dict,
                       authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(401, "No autorizado")

    contenido = nota.get("contenido", "")
    # ← VULNERABLE: contenido HTML no sanitizado antes de guardar (XSS almacenado)
    # Corrección esperada: contenido = bleach.clean(contenido, tags=[...], strip=True)

    conn = sqlite3.connect("clinica.db")
    cursor = conn.cursor()
    # ← VULNERABLE: SQL injection
    cursor.execute(
        f"INSERT INTO notas_clinicas (cedula_paciente, contenido) "
        f"VALUES ('{cedula_paciente}', '{contenido}')"
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Nota agregada"}


@router.get("/pacientes/buscar")
async def buscar_pacientes(nombre: str = "", diagnostico: str = ""):
    # ← VULNERABLE: endpoint sin autenticación expone datos de pacientes
    conn = sqlite3.connect("clinica.db")
    cursor = conn.cursor()
    cursor.execute(     
        f"SELECT cedula, nombre, email, diagnostico FROM pacientes "
        f"WHERE nombre LIKE '%{nombre}%' AND diagnostico LIKE '%{diagnostico}%'"
    )
    return {"pacientes": cursor.fetchall()}
