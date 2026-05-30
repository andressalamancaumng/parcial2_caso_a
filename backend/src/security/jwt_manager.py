import os
import jwt
import uuid
from datetime import datetime, timmezone, timedelta
from fastapi import HTTPException, status

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY no configurada")


def create_access_token(data: dict, expires_minutes: int = 60):

    now = datetime.now(timezone.utc)

    payload = {
        "sub": data["sub"],
        "role": data["role"],
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid.uuid4())
    }

    if data.get("mfa_pending"):
        payload["mfa_pending"] = True

    if data.get("password_change_required"):
        payload["password_change_required"] = True

    if data.get("password_expired"):
        payload["password_expired"] = True

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def decode_token(token: str):

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        required_claims = [
            "sub",
            "role",
            "iat",
            "exp",
            "jti"
        ]

        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autorizado"
                )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

