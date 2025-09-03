# Usa una imagen base ligera de Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copiamos dependencias primero para aprovechar la cache de Docker
COPY requirements.txt .

# Instalamos dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalamos Node.js v20 y npm para poder instalar gemini-cli.
# Luego limpiamos la caché de apt para mantener la imagen ligera.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g @google/gemini-cli

# Copiamos el resto del código
COPY . .

# Puerto del servidor HTTP (ajusta si es distinto)
EXPOSE 8000

ENV AZURE_ORG=""
ENV AZURE_PROJECT=""
ENV AZURE_ITERATION_PATH=""
ENV AZURE_PAT=""
ENV GEMINI_API_KEY=""

# Comando por defecto: correr tu script principal
CMD ["python", "main.py"]