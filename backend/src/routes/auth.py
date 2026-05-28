router = APIRouter()
auth_svc = AuthService()
mfa_svc = MFAService()
rate_limiter = RateLimiter(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class LoginIn(BaseModel):
    document_number: str
    password: str

class PartialTokenIn(BaseModel):
    session_token: str
    otp_code: str

@router.post("/login")
async def login(payload: LoginIn):
    user = await auth_svc.authenticate_user(payload.document_number, payload.password)
    if not user:
        await auth_svc.log_failed_login(payload.document_number)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if user.get("mfa_enabled"):
        token = auth_svc.create_partial_token(user["id"])
        return {"session_token": token, "mfa_required": True, "expires_in": int(os.getenv("PARTIAL_TOKEN_EXPIRE_SECONDS", "300"))}
    access_token = auth_svc.create_access_token(user["id"], user["role"])
    return {"access_token": access_token, "token_type": "bearer", "mfa_required": False}

@router.post("/mfa/setup/totp")
async def mfa_setup_topt(token: str = Body(...), current_user=Depends(auth_svc.get_current_user)):
    if current_user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA already enabled")
    secret = mfa_svc.generate_secret()
    qr_png = mfa_svc.generate_qr_png(current_user["email"], secret)
    auth_svc.store_encrypted_totp_secret(current_user["id"], secret)
    return {"qr_base64": base64.b64encode(qr_png).decode(), "note": "QR shown once. Confirm with first OTP."}

@router.post("/mfa/verify")
async def mfa_verify(payload: PartialTokenIn):
    if await rate_limiter.is_blocked(payload.session_token):
        raise HTTPException(status_code=429, detail="Too many attempts, try later")
    session = auth_svc.verify_partial_token(payload.session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    user_id = session["sub"]
    secret = auth_svc.get_encrypted_totp_secret(user_id)
    if not secret:
        raise HTTPException(status_code=400, detail="MFA not setup")
    if not mfa_svc.verify_otp(secret, payload.otp_code):
        await rate_limiter.register_failure(payload.session_token)
        raise HTTPException(status_code=401, detail="Invalid OTP")
    await rate_limiter.reset(payload.session_token)
    user = auth_svc.get_user_by_id(user_id)
    access_token = auth_svc.create_access_token(user_id, user["role"])
    if not user.get("mfa_enabled"):
        auth_svc.set_mfa_enabled(user_id, True)
    return {"access_token": access_token, "token_type": "bearer"}