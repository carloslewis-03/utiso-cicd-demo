# syntax=docker/dockerfile:1

# Slim, regularly-patched official base image keeps the attack surface small.
FROM python:3.12-slim

# Don't write .pyc files; don't buffer stdout/stderr (better container logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached when only app code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY app/ ./app/

# Run as an unprivileged user instead of root (defense in depth).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080

# Lightweight liveness check against the /healthz endpoint.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status==200 else 1)"

# Gunicorn is a production-grade WSGI server (the Flask dev server is not).
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app.main:app"]
