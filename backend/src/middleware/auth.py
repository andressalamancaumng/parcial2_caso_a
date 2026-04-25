"""
Middleware de autenticación y autorización.
Versión con vulnerabilidades — los estudiantes deben corregir.
"""
from fastapi import Header, HTTPException
from src.auth.service import decode_token

# ← VULNERABLE: acepta roles como strings sin lista autorizada
def require_role(*roles: str):
    async def dependency(authorization: str = Header(None)):
        if authorization is None:
            raise HTTPException(401, "Token requerido")
        # ← VULNERABLE: no verifica prefijo "Bearer "
        token = authorization
        try:
            payload = decode_token(token)
        except ValueError as e:
            raise HTTPException(401, str(e))
        # ← VULNERABLE: comparación de string directo sin normalizar
        if payload.get("role") not in roles:
            raise HTTPException(403, "Sin permisos")
        return payload
    return dependency
