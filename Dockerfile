# ──────────────────────────────────────────────────────────────────────────────
# RAGMU - Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client libraries
    libpq-dev \
    # Build tools
    gcc \
    g++ \
    # PDF processing (poppler for docling/docx2pdf)
    poppler-utils \
    # LibreOffice for .docx -> .pdf conversion
    libreoffice \
    # Git (some HuggingFace downloads need it)
    git \
    # Image processing
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code
COPY . .

# Create required directories
RUN mkdir -p /app/temp_uploads /app/chroma_db

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
