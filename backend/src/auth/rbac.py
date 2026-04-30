from fastapi import HTTPException, Depends
import jwt
import os
from .auth_service import BLACKLIST

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

def verify_role(roles: list):
    def wrapper(token: str):

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except:
            raise HTTPException(status_code=401, detail="Token invalido")

        if payload["jti"] in BLACKLIST:
            raise HTTPException(status_code=401, detail="Token revocado")

        if payload["role"] not in roles:
            raise HTTPException(status_code=403, detail="No autorizado")

        return payload

    return wrapper
