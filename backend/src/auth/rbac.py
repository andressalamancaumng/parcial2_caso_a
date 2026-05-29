from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import get_db

from src.security.jwt_manager import decode_token
from src.security.blacklist import is_blacklisted

security = HTTPBearer(auto_error=False)


def require_role(allowed_roles: list):

    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ):

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticación requerida"
            )

        payload = decode_token(
            credentials.credentials
        )

        if payload.get("mfa_pending"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA requerido"
            )

        blacklisted = await is_blacklisted(
            db,
            payload["jti"]
        )

        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        if payload["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado"
            )

        return payload

    return role_checker


RequireAdmin = require_role(["admin_clinica"])
RequireDoctor = require_role(["medico"])
RequirePatient = require_role(["paciente"])
RequireMedicalStaff = require_role([
    "medico",
    "enfermero",
    "admin_clinica"
])
