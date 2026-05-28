import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
FERNET_KEY = os.getenv("FERNET_KEY", "")
if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY not set in env")
fernet = Fernet(FERNET_KEY.encode())

_users = {
    "1": {"id":"1","email":"doc1@example.com","document_number":"1234","password_hash":pwd_context.hash("Passw0rd!"),"role":"medico","mfa_enabled":True}
}

class AuthService:
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET","secret")
        self.access_exp = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","60"))
        self.partial_exp = int(os.getenv("PARTIAL_TOKEN_EXPIRE_SECONDS","600"))
    async def authenticate_user(self, document_number, password):
        for u in _users.values():
            if u["document_number"]==document_number:
                if pwd_context.verify(password, u["password_hash"]):
                    return u
        return None
    def create_access_token(self, user_id, role):
        payload = {"sub": user_id, "role": role, "exp": datetime.utcnow() + timedelta(minutes=self.access_exp)}
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    def create_partial_token(self, user_id):
        payload = {"sub": user_id, "partial": True, "exp": datetime.utcnow() + timedelta(seconds=self.partial_exp)}
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    def verify_partial_token(self, token):
        try:
            data = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            if data.get("partial"):
                return data
            return None
        except Exception:
            return None
    def log_failed_login(self, identifier):
        print(f"[AUTH] failed login for {identifier} at {datetime.utcnow().isoformat()}")
    def get_user_by_id(self, user_id):
        return _users.get(str(user_id))
    def store_encrypted_totp_secret(self, user_id, secret):
        token = fernet.encrypt(secret.encode()).decode()
        _users[str(user_id)]["totp_secret_enc"] = token
    def get_encrypted_totp_secret(self, user_id):
        t = _users.get(str(user_id), {}).get("totp_secret_enc")
        if not t:
            return None
        return fernet.decrypt(t.encode()).decode()
    def set_mfa_enabled(self, user_id, v=True):
        _users[str(user_id)]["mfa_enabled"]=v
    security = HTTPBearer()

async def get_current_user_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        if payload.get("partial"):
            raise HTTPException(status_code=401, detail="Partial token not allowed")
        user = AuthService().get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")