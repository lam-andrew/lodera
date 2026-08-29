# Lodera backend — Python 3.12 + FastAPI
FROM python:3.12-slim

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

EXPOSE 8000

# Reload is enabled via compose for local dev; the image default is a plain server.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
