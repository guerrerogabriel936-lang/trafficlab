FROM python:3.10-slim

WORKDIR /app

# Copiar requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY main.py .

# Exponer el puerto por defecto
EXPOSE 8080

# Comando único de ejecución
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
