import os
from dotenv import load_dotenv


load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.router import router as auth_router
from src.historias.router import router as historia_router

app = FastAPI(title="Clínica Multimedia Salud S.A. API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(historia_router, prefix="/api", tags=["historias"])

@app.get("/health")
def health():
    return {"status": "ok"}
