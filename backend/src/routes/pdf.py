from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import hashlib
import bleach
import sqlite3
import os
import datetime
import json
import jwt

router = APIRouter()
security = HTTPBearer()

def get_current_user_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    secret = os.getenv("JWT_SECRET", "")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("partial"):
        raise HTTPException(status_code=401, detail="Partial token not allowed")
    # payload must contain sub and role
    user = {"sub": payload.get("sub"), "role": payload.get("role"), "email": payload.get("email", "")}
    return user

def pdf_bytes_from_text_lines(title: str, lines: list[str], metadata: dict | None = None) -> bytes:
    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    if metadata:
        if metadata.get("title"):
            p.setTitle(metadata.get("title"))
        if metadata.get("author"):
            p.setAuthor(metadata.get("author"))
    width, height = A4
    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, title)
    p.setFont("Helvetica", 10)
    y -= 30
    for line in lines:
        if y < 60:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)
        # ensure line is str
        p.drawString(50, y, str(line))
        y -= 14
    p.showPage()
    p.save()
    buf.seek(0)
    return buf.getvalue()

@router.get("/pacientes/me/resumen-pdf")
def resumen_historia_pdf(user=Depends(get_current_user_from_header)):
    if user["role"] != "paciente":
        raise HTTPException(status_code=403, detail="Forbidden")
    patient_id = str(user["sub"])
    conn = sqlite3.connect("clinica.db")
    cur = conn.cursor()
    cur.execute("SELECT nombre, tipo_doc, numero_doc, fecha_nacimiento FROM pacientes WHERE id = ?", (patient_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    nombre, tipo_doc, numero_doc, fnac = row
    cur.execute("SELECT fecha, medico_id, diagnostico FROM atenciones WHERE paciente_id = ? ORDER BY fecha DESC", (patient_id,))
    atenciones = cur.fetchall()
    conn.close()
    lines = [
        f"Nombre: {bleach.clean(str(nombre))}",
        f"Documento: {bleach.clean(str(tipo_doc))} {bleach.clean(str(numero_doc))}",
        f"Fecha de nacimiento: {bleach.clean(str(fnac))}",
        "",
        "Atenciones (más recientes primero):"
    ]
    for fecha, medico_id, diagnostico in atenciones:
        lines.append(f"- {bleach.clean(str(fecha))} | Médico ID: {bleach.clean(str(medico_id))} | Diagnóstico: {bleach.clean(str(diagnostico))}")
    metadata = {"author": "Clínica Multimedia Salud S.A.", "title": "Resumen Historia Clínica"}
    pdf_bytes = pdf_bytes_from_text_lines("Resumen Historia Clínica", lines, metadata)
    # log event (simple)
    try:
        with open("pdf_generation.log", "a", encoding="utf-8") as lf:
             lf.write(f"{datetime.datetime.utcnow().isoformat()} | paciente_id={patient_id} | evento=generar_resumen\n")
    except Exception:
        pass

