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
import os
# ← VULNERABLE: clave hardcodeada — debe venir de variable de entorno
#JWT_SECRET = "clinica_secret_2024"
#ALGORITHM = "HS256"

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET_KEY no configurada en variables de entorno")

ALGORITHM = "HS256"


# ← VULNERABLE: MD5 sin sal — debe usarse bcrypt con pwd_context
#def hash_password_inseguro(password: str) -> str:
#    return hashlib.md5(password.encode()).hexdigest()

# Correcto (comentado — los estudiantes deben activar esto)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

from passlib.context import CryptContext

# Configurar bcrypt con costo 12
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    """Genera hash seguro de contraseña usando bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verifica contraseña contra hash bcrypt - tiempo constante"""
    return pwd_context.verify(plain, hashed)




def verify_password(plain: str, hashed: str) -> bool:
    # ← VULNERABLE: compara MD5 — debe usar pwd_context.verify
    return hashlib.md5(plain.encode()).hexdigest() == hashed




#def create_access_token(data: dict) -> str:
#    payload = data.copy()
#    # ← VULNERABLE: sin expiración (exp) ni jti
#    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
#    return token

import uuid
from datetime import datetime, timedelta

def create_access_token(data: dict) -> str:
    payload = data.copy()
    # Agregar campos de seguridad
    payload["exp"] = datetime.utcnow() + timedelta(hours=1)  # Expira en 1 hora
    payload["iat"] = datetime.utcnow()  # Tiempo de emisión
    payload["jti"] = str(uuid.uuid4())  # Identificador único para blacklist
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token

import logging

logger = logging.getLogger(__name__)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Intento de uso de token expirado")
        raise ValueError("Token expirado")
    except jwt.InvalidTokenError:
        logger.warning("Intento de token inválido")
        raise ValueError("Token inválido")
    except Exception as e:
        logger.error(f"Error inesperado en decode_token: {type(e)._name_}")
        raise ValueError("Error interno en autenticación")


#def decode_token(token: str) -> dict:
#    try:
#        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
#    except Exception as e:
#        # ← VULNERABLE: expone el error interno
#        raise ValueError(f"Token inválido: {str(e)}")
