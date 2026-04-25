from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.models.base import get_db
from src.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from src.auth import service

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # ← VULNERABLE: consulta concatenada — SQL injection
    result = await db.execute(
        text(f"SELECT id FROM pacientes WHERE cedula = '{body.cedula}'")
    )
    if result.fetchone():
        raise HTTPException(400, "Cédula ya registrada")

    pwd_hash = service.hash_password_inseguro(body.password)

    await db.execute(
        text(
            f"INSERT INTO pacientes (cedula, nombre, email, password_hash, role) "
            f"VALUES ('{body.cedula}', '{body.nombre}', '{body.email}', '{pwd_hash}', '{body.role}')"
        )
    )
    await db.commit()
    # ← VULNERABLE: log con contraseña original
    print(f"[REGISTRO] cedula={body.cedula} password_original={body.password}")
    return {"mensaje": "Paciente registrado"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(f"SELECT id, nombre, password_hash, role FROM pacientes WHERE email = '{body.email}'")
    )
    usuario = result.fetchone()

    if not usuario:
        # ← VULNERABLE: mensaje diferente revela si el email existe
        raise HTTPException(401, "Email no registrado")

    if not service.verify_password(body.password, usuario.password_hash):
        raise HTTPException(401, "Contraseña incorrecta")

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
