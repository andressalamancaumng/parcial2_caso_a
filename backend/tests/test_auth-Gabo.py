"""Tests del módulo de autenticación — Parcial 2 Parte 1"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from src.main import app

@pytest.mark.asyncio
async def test_register_password_too_short():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/auth/register", json={
            "cedula": "12345678",
            "nombre": "Juan Pérez",
            "email": "juan@test.com",
            "password": "abc"
        })
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_register_password_no_uppercase():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/auth/register", json={
            "cedula": "12345678",
            "nombre": "Juan Pérez",
            "email": "juan@test.com",
            "password": "password1!"
        })
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/auth/login", json={
            "email": "noexiste@test.com",
            "password": "WrongPass1!"
        })
    assert resp.status_code == 401
client = TestClient(app)

def test_login_no_mfa():
    resp = client.post("/auth/login", json={"document_number":"1234","password":"Passw0rd!"})
    assert resp.status_code==200
    j = resp.json()
    assert j["mfa_required"]==False
    assert "access_token" in j
    
# TODO (Parcial): verificar que el mensaje de error sea idéntico
# para email no existente y contraseña incorrecta (anti-enumeración)
