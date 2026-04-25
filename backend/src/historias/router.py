"""
Router de historias clínicas — con vulnerabilidades intencionales
"""
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text
import sqlite3
from src.auth.service import decode_token
import bleach  # importado pero no usado — los estudiantes deben usarlo

router = APIRouter()

@router.get("/historia/{cedula_paciente}")
async def obtener_historia(cedula_paciente: str, authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(401, "Token requerido")
    try:
        payload = decode_token(authorization)
    except Exception as e:
        # ← VULNERABLE: expone detalles del error
        raise HTTPException(401, f"Token inválido: {str(e)}")

    # ← VULNERABLE: cualquier médico ve cualquier paciente (sin verificar asignación)
    if payload.get("role") not in ["ROLE_MEDICO", "ROLE_ADMIN"]:
        raise HTTPException(403, "Sin permisos")

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
