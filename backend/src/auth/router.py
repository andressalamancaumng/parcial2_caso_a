from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import hashlib
import time
import logging
# Imports internos del proyecto
from src.models.base import get_db
from src.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from src.auth import service
from src.auth.service import verify_password  # Asegúrate de que la ruta sea correcta

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Verificación de cédula con parámetros seguros (Evita SQL Injection)
    result = await db.execute(
        text("SELECT id FROM pacientes WHERE cedula = :cedula"),
        {"cedula": body.cedula}
    )

    # --- CÓDIGO ANTERIOR COMENTADO (REQUERIMIENTO) ---
    # #result = await db.execute(
    # #    text(f"SELECT id FROM pacientes WHERE cedula = '{body.cedula}'")
    # #)
    
    if result.fetchone():
        raise HTTPException(400, "Cédula ya registrada")

    pwd_hash = service.hash_password_inseguro(body.password)

    # Inserción segura
    await db.execute(
        text("""
            INSERT INTO pacientes (cedula, nombre, email, password_hash, role)
            VALUES (:cedula, :nombre, :email, :password_hash, :role)
        """),
        {
            "cedula": body.cedula,
            "nombre": body.nombre,
            "email": body.email,
            "password_hash": pwd_hash,
            "role": body.role
        }
    )

    # #await db.execute(
    # #    text(
    # #        f"INSERT INTO pacientes (cedula, nombre, email, password_hash, role) "
    # #        f"VALUES ('{body.cedula}', '{body.nombre}', '{body.email}', '{pwd_hash}', '{body.role}')"
    # #    )
    # #)

    await db.commit()
    
    # ← VULNERABLE: log con contraseña original (Se deja para el ejercicio)
    
    
    logger = logging.getLogger(__name__)
    #print(f"[REGISTRO] cedula={body.cedula} password_original={body.password}")
    return {"mensaje": "Paciente registrado"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Búsqueda de usuario segura
    result = await db.execute(
        text("SELECT id, nombre, password_hash, role FROM pacientes WHERE email = :email"),
        {"email": body.email}
    )
    
    # #result = await db.execute(
    # #   text(f"SELECT id, nombre, password_hash, role FROM pacientes WHERE email = '{body.email}'")
    # #)
    
    usuario = result.fetchone()

    # --- INICIO DE LÓGICA DE VALIDACIÓN (DENTRO DE LA FUNCIÓN) ---
    
    # Tiempo de respuesta constante para evitar enumeración de usuarios
    if not usuario:
        # Simulación de hash para mantener tiempo de respuesta igual
        dummy_hash = hashlib.sha256(body.password.encode()).hexdigest()
        time.sleep(0.1)  
        raise HTTPException(401, "Credenciales inválidas")

    # Verificación de contraseña
    if not verify_password(body.password, usuario.password_hash):
        raise HTTPException(401, "Credenciales inválidas")

    # --- CÓDIGO ANTERIOR COMENTADO (REQUERIMIENTO) ---
    # # if not usuario:
    # #     # ← VULNERABLE: mensaje diferente revela si el email existe
    # #     raise HTTPException(401, "Email no registrado")

    # # if not service.verify_password(body.password, usuario.password_hash):
    # #     raise HTTPException(401, "Contraseña incorrecta")

    # Generación de token si las credenciales son correctas
    token = service.create_access_token({
        "user_id": usuario.id,
        "nombre": usuario.nombre,
        "role": usuario.role,
    })
    
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout():
    # ← VULNERABLE: no invalida el token (sin blacklist)
    return {"mensaje": "Sesión cerrada"}