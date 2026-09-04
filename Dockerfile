FROM python:3.10-slim

WORKDIR /app

# Copiar requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY main.py .

# Copiar el motor de pruebas Locust
COPY locustfile.py .

# Exponer el puerto
EXPOSE 8080

# Ejecutar TrafficLab
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
