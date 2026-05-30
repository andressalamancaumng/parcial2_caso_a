from src.db.session import SessionLocal
from src.db.models import User
from src.services.auth_service import AuthService

def main():
    db = SessionLocal()
    try:
        auth = AuthService()
        password = "P@ssw0rd"
        password_hash = auth.hash_password(password)  # adapta si el método se llama distinto
        user = User(email="test@example.com", document_number="12345678", password_hash=password_hash, role="paciente", mfa_enabled=False)
        db.add(user)
        db.commit()
        print("Usuario creado:", user.email)
    finally:
        db.close()

if name == "main":
    main()