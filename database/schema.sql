-- Esquema de base de datos — Clínica Multimedia Salud S.A.#
-- Ejecutar como usuario postgres en la instancia sg-db

CREATE DATABASE clinica_db;
\c clinica_db;

CREATE TABLE pacientes (
    id            SERIAL PRIMARY KEY,
    cedula        VARCHAR(20) UNIQUE NOT NULL,
    nombre        VARCHAR(120) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(30) DEFAULT 'ROLE_PACIENTE',
    estado        VARCHAR(20) DEFAULT 'activo',
    created_at    TIMESTAMP DEFAULT NOW(),
    last_login    TIMESTAMP
);

CREATE TABLE medicos (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(120) NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(30) DEFAULT 'ROLE_MEDICO',
    especialidad  VARCHAR(100),
    estado        VARCHAR(20) DEFAULT 'activo',
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Asignación de pacientes a médicos (un médico solo ve sus pacientes)
CREATE TABLE medico_paciente (
    medico_id   INT REFERENCES medicos(id),
    paciente_id INT REFERENCES pacientes(id),
    PRIMARY KEY (medico_id, paciente_id)
);

CREATE TABLE historias_clinicas (
    id                SERIAL PRIMARY KEY,
    cedula_paciente   VARCHAR(20) REFERENCES pacientes(cedula),
    diagnostico       TEXT,
    medicamentos      TEXT,
    alergias          TEXT,
    antecedentes      TEXT,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notas_clinicas (
    id              SERIAL PRIMARY KEY,
    cedula_paciente VARCHAR(20) REFERENCES pacientes(cedula),
    medico_id       INT REFERENCES medicos(id),
    contenido       TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE login_attempts (
    id         SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    success    BOOLEAN DEFAULT FALSE,
    timestamp  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE token_blacklist (
    id         SERIAL PRIMARY KEY,
    jti        VARCHAR(36) UNIQUE NOT NULL,
    expired_at TIMESTAMP NOT NULL
);

-- Usuario de aplicación con mínimo privilegio
CREATE USER clinica_app WITH PASSWORD 'CHANGE_ME_APP_PASSWORD';
GRANT CONNECT ON DATABASE clinica_db TO clinica_app;
GRANT USAGE ON SCHEMA public TO clinica_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO clinica_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO clinica_app;
