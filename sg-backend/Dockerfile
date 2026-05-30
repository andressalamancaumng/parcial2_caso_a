FROM python:3.11-slim

WORKDIR /app

# Copiar requirements.txt e instalar dependencias
COPY ../backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY ../backend/src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]