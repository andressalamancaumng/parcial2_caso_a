from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import get_db

from src.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse
)

from src.auth.service import (
    register_patient_user,
    login_user,
    logout_user
)

from src.auth.rbac import (
    RequireAdmin,
    RequireMedicalStaff
)

from src.security.audit import (
    register_audit_event
)

from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer(auto_error=False)

# ---------------------------
# REGISTRO SEGURO
# ---------------------------
@router.post(
    "/admin/register-patient",
    status_code=status.HTTP_201_CREATED
)
async def register_patient(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RequireAdmin)
):

    result = await register_patient_user(
        db=db,
        data=body,
        created_by=int(current_user["sub"]),
        ip_address=request.client.host
    )

    if not result:

        await register_audit_event(
            db=db,
            usuario_id=int(current_user["sub"]),
                        action="REGISTER_PATIENT",
            result="FAILED",
            details="DUPLICATE_EMAIL_OR_DOCUMENT",
            ip_address=request.client.host
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo completar la solicitud"
        )

    return result

# ---------------------------
# LOGIN SEGURO
# ---------------------------
@router.post(
    "/login",
    response_model=TokenResponse
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    result = await login_user(
        db,
        body.email,
        body.password,
        request.client.host
    )

    if not result["success"]:
        
        await register_audit_event(
            db=db,
            usuario_id="None",
            action="LOGIN",
            result="FAILED",
            ip_address=request.client.host
        )

        if result.get("password_expired"):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "La contraseña temporal expiró. "
                    "Debe solicitar una nueva."
                )
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    return TokenResponse(
        access_token=result["token"],
        token_type="bearer",
        requires_mfa=result["requires_mfa"],
        requires_password_change=result["requires_password_change"],
        password_expired=result["password_expired"]
    )

# ---------------------------
# LOGOUT
# ---------------------------
@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RequireMedicalStaff)
):

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido"
        )

    await logout_user(
        db,
        credentials.credentials
    )

    return {
        "message": "Sesión finalizada"
    }