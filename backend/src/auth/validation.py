import re

from fastapi import HTTPException, status


def validate_password_policy(password: str):

    pattern = (
        r"^(?=.*[a-z])"
        r"(?=.*[A-Z])"
        r"(?=.*\d)"
        r"(?=.*[@$!%*?&])"
        r"[A-Za-z\d@$!%*?&]{8,}$"
    )

    if not re.match(pattern, password):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña inválida"
        )