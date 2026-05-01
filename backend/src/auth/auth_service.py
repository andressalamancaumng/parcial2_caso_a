import sqlite3
import os
import jwt
import uuid
import re
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Configuración segura
DATABASE = "clinica.db"
SECRET_KEY = os.getenv("JWT_SECRET")  # ← ya no hardcodeado
ALGORITHM = "HS256"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# ---------------------------
# VALIDACIÓN DE PASSWORD
# ---------------------------
def validar_password(password: str):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


# ---------------------------
# REGISTRO
# ---------------------------
def registrar_paciente(cedula, nombre, email, password, diagnostico):

    if not validar_password(password):
        return {"error": "Datos inválidos"}

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Verificar unicidad (sin revelar info)
    cursor.execute("SELECT cedula FROM pacientes WHERE email = ?", (email,))
    existente = cursor.fetchone()

    if existente:
        conn.close()
        return {"mensaje": "No se pudo completar el registro"}

    password_hash = pwd_context.hash(password)

    cursor.execute("""
        INSERT INTO pacientes (cedula, nombre, email, password, diagnostico)
        VALUES (?, ?, ?, ?, ?)
    """, (cedula, nombre, email, password_hash, diagnostico))

    conn.commit()
    conn.close()

    # Log seguro
    print({
        "timestamp": str(datetime.utcnow()),
        "evento": "registro",
        "user": cedula[:3] + "***"
    })

    return {"mensaje": "Paciente registrado correctamente"}


# ---------------------------
# LOGIN
# ---------------------------
def login_paciente(cedula: str, password: str, ip: str = "unknown"):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT cedula, password, role FROM pacientes WHERE cedula = ?", (cedula,))
    user = cursor.fetchone()

    # Hash dummy para evitar timing attack
    fake_hash = pwd_context.hash("fake_password")

    if user:
        stored_hash = user[1]
    else:
        stored_hash = fake_hash

    # SIEMPRE verifica (timing attack mitigado)
    valid = pwd_context.verify(password, stored_hash)

    if not user or not valid:
        registrar_intento_fallido(cedula)
        return {"error": "Credenciales inválidas"}

    if usuario_bloqueado(cedula):
        return {"error": "Cuenta temporalmente bloqueada"}

    reset_intentos(cedula)

    payload = {
        "sub": str(user[0]),
        "role": user[2],
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "jti": str(uuid.uuid4())
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    print({
        "timestamp": str(datetime.utcnow()),
        "ip": ip,
        "user": cedula[:3] + "***",
        "resultado": "LOGIN_OK"
    })

    return {"token": token}


# ---------------------------
# LOGIN ATTEMPTS
# ---------------------------
def registrar_intento_fallido(cedula):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO login_attempts (cedula, attempts, last_attempt)
        VALUES (?, 1, ?)
        ON CONFLICT(cedula) DO UPDATE SET
        attempts = attempts + 1,
        last_attempt = ?
    """, (cedula, datetime.utcnow(), datetime.utcnow()))

    conn.commit()
    conn.close()


def usuario_bloqueado(cedula):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT attempts, last_attempt FROM login_attempts WHERE cedula = ?", (cedula,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    attempts, last_attempt = row

    if attempts >= 5:
        delta = datetime.utcnow() - datetime.fromisoformat(last_attempt)
        return delta < timedelta(minutes=15)

    return False


def reset_intentos(cedula):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM login_attempts WHERE cedula = ?", (cedula,))
    conn.commit()
    conn.close()


# ---------------------------
# BLACKLIST (LOGOUT)
# ---------------------------
BLACKLIST = set()

def logout(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    BLACKLIST.add(payload["jti"])