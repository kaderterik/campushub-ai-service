FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=8005 \
    APP_ENV=development

WORKDIR /app

# HEALTHCHECK curl kullandığı için slim imaja eklenir.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# torch CPU wheel'i kullanılır; varsayılan Linux wheel'i GB'larca CUDA kütüphanesi getirir.
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY app ./app

RUN useradd --create-home appuser
USER appuser

EXPOSE 8005

# Model lifespan içinde bloklayarak yüklenir; start-period bu süreyi tolere eder.
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8005}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT}"]
