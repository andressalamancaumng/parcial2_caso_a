from pydantic import BaseModel, EmailStr, field_validator
import re

class RegisterRequest(BaseModel):
    cedula: str
    nombre: str
    email: EmailStr
    password: str
    role: str = "ROLE_PACIENTE"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Mínimo 8 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("Debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Debe contener al menos un carácter especial")
        return v

    @field_validator("cedula")
    @classmethod
    def cedula_format(cls, v: str) -> str:
        if not re.match(r"^\d{7,10}$", v):
            raise ValueError("Cédula inválida")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
