# syntax=docker/dockerfile:1.7

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/ragmu \
    HF_HOME=/home/ragmu/.cache/huggingface

WORKDIR /app

# Keep compilers and development headers out of the final runtime filesystem.
COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        git \
        libpq-dev \
        poppler-utils \
        libreoffice \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && python -m pip install --upgrade pip \
    && python -m pip install --requirement requirements.txt \
    && apt-get purge -y --auto-remove gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ARG APP_UID=10001
ARG APP_GID=10001
RUN groupadd --gid "${APP_GID}" ragmu \
    && useradd --uid "${APP_UID}" --gid ragmu --create-home --shell /usr/sbin/nologin ragmu \
    && mkdir -p /app/temp_uploads /app/chroma_db "${HF_HOME}" \
    && chown -R ragmu:ragmu /app /home/ragmu

COPY --chown=ragmu:ragmu . .

USER ragmu

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=5)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
