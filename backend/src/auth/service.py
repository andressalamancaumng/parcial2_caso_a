"""
Servicio de autenticación — VERSIÓN CON VULNERABILIDADES INTENCIONALES
para el Parcial 2 Parte 1. Los estudiantes deben identificar y corregir
las fallas marcadas con # ← VULNERABLE
"""
import hashlib
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

# ← VULNERABLE: clave hardcodeada — debe venir de variable de entorno
JWT_SECRET = "clinica_secret_2024"
ALGORITHM = "HS256"

# ← VULNERABLE: MD5 sin sal — debe usarse bcrypt con pwd_context
def hash_password_inseguro(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Correcto (comentado — los estudiantes deben activar esto)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def verify_password(plain: str, hashed: str) -> bool:
    # ← VULNERABLE: compara MD5 — debe usar pwd_context.verify
    return hashlib.md5(plain.encode()).hexdigest() == hashed

def create_access_token(data: dict) -> str:
    payload = data.copy()
    # ← VULNERABLE: sin expiración (exp) ni jti
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except Exception as e:
        # ← VULNERABLE: expone el error interno
        raise ValueError(f"Token inválido: {str(e)}")
