# 🏥 Caso A — Clínica Multimedia Salud S.A.
## Seguridad Informática · UMNG · 2026-I

### Stack
- **Backend:** Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Angular 17 + TypeScript
- **Infraestructura:** AWS Lightsail (4 instancias)

### Instancias AWS Lightsail
| Instancia | Rol | IP privada |
|-----------|-----|-----------|
| sg-frontend | Nginx + Angular | 10.0.0.10 |
| sg-backend | FastAPI | 10.0.0.11 |
| sg-db | PostgreSQL | 10.0.0.12 |
| sg-security | Wazuh + SonarQube + ZAP | 10.0.0.13 |

### Instalación local
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar variables
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
ng serve
```

### Ramas Git
- `main` — código estable
- `parcial2-parte1` — entregas del parcial
