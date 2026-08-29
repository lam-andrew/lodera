# Lodera backend — Python 3.12 + FastAPI
FROM python:3.14-slim

# - PYTHONDONTWRITEBYTECODE: no .pyc files in the image
# - PYTHONUNBUFFERED: stream logs straight to the container output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (leverages Docker layer caching): copy only the project
# metadata, install, then copy the source.
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir ".[dev]"

COPY . .

# Install the app itself (so `import app` resolves) without re-resolving dependencies.
RUN pip install --no-cache-dir --no-deps -e .

# Run as a non-root user (defense in depth; Trivy DS-0002).
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Report container health via the API's own /health endpoint (Trivy DS-0026).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode()==200 else 1)"

# Reload is enabled via compose for local dev; the image default is a plain server.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
