# --- Stage 1: build dependencies ---
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# --- Stage 2: runtime ---
FROM python:3.12-slim

# don't run as root
RUN useradd --create-home appuser

WORKDIR /app

# install deps from pre-built wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# copy application code
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser models/ models/

# switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
