# Usa una imagen base ligera de Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copiamos dependencias primero para aprovechar la cache de Docker
COPY requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Puerto del servidor HTTP (ajusta si es distinto)
EXPOSE 8000

ENV AZURE_ORG=""
ENV AZURE_PROJECT=""
ENV AZURE_ITERATION_PATH=""
ENV AZURE_PAT=""
ENV OPENAI_API_KEY=""

# Comando por defecto: correr tu script principal
CMD ["python", "get-hist.py"]