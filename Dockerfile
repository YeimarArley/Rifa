# ==================== ETAPA 1: BUILD ====================
FROM python:3.11-slim as builder

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt

# ==================== ETAPA 2: RUNTIME ====================
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    ENVIRONMENT=production

# Instalar solo librerías runtime (no compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root ANTES de copiar archivos
USER appuser

# Cambiar a directorio de trabajo
WORKDIR /app

# Copiar dependencias instaladas desde builder
COPY --from=builder --chown=appuser:appuser /install /home/appuser/.local

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/ || exit 1

    
# Comando de inicio (Railway usa $PORT en vez de 8080 fijo)
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 4 --threads 2 --timeout 120 --access-logfile - --error-logfile - server:app