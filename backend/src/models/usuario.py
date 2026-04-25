from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from src.models.base import Base

class Paciente(Base):
    __tablename__ = "pacientes"
    id            = Column(Integer, primary_key=True)
    cedula        = Column(String(20), unique=True, nullable=False)
    nombre        = Column(String(120), nullable=False)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(30), default="ROLE_PACIENTE")
    estado        = Column(String(20), default="activo")
    created_at    = Column(DateTime, server_default=func.now())

class Medico(Base):
    __tablename__ = "medicos"
    id            = Column(Integer, primary_key=True)
    nombre        = Column(String(120), nullable=False)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(30), default="ROLE_MEDICO")
    estado        = Column(String(20), default="activo")
    created_at    = Column(DateTime, server_default=func.now())

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id         = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    success    = Column(Boolean, default=False)
    timestamp  = Column(DateTime, server_default=func.now())

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id         = Column(Integer, primary_key=True)
    jti        = Column(String(36), unique=True, nullable=False)
    expired_at = Column(DateTime, nullable=False)
