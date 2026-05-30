from pydantic import BaseModel, EmailStr, Field
from datetime import date

class RegisterRequest(BaseModel):

    tipo_documento: str = Field(
        min_length=2,
        max_length=10
    )

    numero_documento: str = Field(
        min_length=5,
        max_length=20
    )

    nombres: str = Field(
        min_length=3,
        max_length=120
    )

    apellidos: str = Field(
        min_length=3,
        max_length=120
    )

    fecha_nacimiento: date

    sexo_biologico: str = Field(
        min_length=1,
        max_length=20
    )

    grupo_sanguineo: str = Field(
        min_length=2,
        max_length=5
    )

    telefono: str = Field(
        min_length=7,
        max_length=20
    )

    email: EmailStr

class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128
    )


class TokenResponse(BaseModel):

    access_token: str

    token_type: str

    requires_mfa: bool = False

    requires_password_change: bool = False

    password_expired: bool = False

