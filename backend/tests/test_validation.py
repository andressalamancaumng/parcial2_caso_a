"""
Tests de validación de entradas — completar en el Parcial 2 Parte 1
Los estudiantes deben implementar los casos de prueba marcados con TODO
"""
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_cedula_invalida_letras():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/auth/register", json={
            "cedula": "ABCD1234",
            "nombre": "Test",
            "email": "test@test.com",
            "password": "Password1!"
        })
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_buscar_pacientes_sin_autenticacion():
    # TODO: verificar que el endpoint retorne 401 sin token
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/pacientes/buscar?nombre=Juan")
    # ACTUALMENTE RETORNA 200 — este test FALLA (vulnerabilidad intencional)
    # Después de corregir debe retornar 401
    assert resp.status_code == 401  # este assert fallará antes de la corrección

@pytest.mark.asyncio
async def test_nota_xss_sanitizada():
    # TODO: verificar que un contenido con <script> sea sanitizado antes de guardarse
    pass
