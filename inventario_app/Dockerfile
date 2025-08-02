# Dockerfile
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Expone el puerto donde correrá la app
EXPOSE 5001

# Comando para ejecutar la app
CMD ["python", "app.py"]
