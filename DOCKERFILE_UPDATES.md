# Dockerfile Updates Summary

## Changes Made

### ✅ Security Improvements
1. **Non-root user**: Added `appuser` to run the application without root privileges
2. **Environment variables**: Added `PYTHONUNBUFFERED` and `PYTHONDONTWRITEBYTECODE` for better Python behavior

### ✅ Performance & Best Practices
1. **Layer caching**: Copy requirements.txt first to optimize Docker layer caching
2. **Pip upgrade**: Upgrade pip before installing dependencies
3. **Health check**: Added healthcheck endpoint for container monitoring

### ✅ Port Configuration
1. **Changed default port**: From 80 to 8000 (non-root users can't bind to port 80)
2. **Configurable port**: Can override via `PORT` environment variable
3. **Port mapping**: For production, map external port 80 to internal 8000:
   ```bash
   docker run -p 80:8000 calculator-api
   ```

### ✅ .dockerignore Updates
Added exclusions for:
- Documentation files (*.md)
- Test files (tests/, test_*.py)
- Backup files (*.backup, *.bk, main.py.old)
- Progress tracking files

## Key Changes

### Before:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

### After:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

## Usage

### Build the image:
```bash
docker build -t calculator-api .
```

### Run with default port (8000):
```bash
docker run -p 8000:8000 calculator-api
```

### Run with custom port:
```bash
docker run -p 8080:8080 -e PORT=8080 calculator-api
```

### Run with port 80 mapping (production):
```bash
docker run -p 80:8000 calculator-api
```

### Run with environment variables:
```bash
docker run -p 8000:8000 \
  -e ENVIRONMENT=Production \
  -e API_TITLE="Calculator API" \
  calculator-api
```

## Health Check

The container includes a healthcheck that monitors the `/health` endpoint:
- Checks every 30 seconds
- 10 second timeout
- 5 second start period
- 3 retries before marking as unhealthy

Check health status:
```bash
docker ps  # Shows health status
docker inspect <container-id> | grep Health
```

## Security Notes

1. **Non-root user**: Application runs as `appuser` (UID 1000) instead of root
2. **Port 80**: If you need port 80, use port mapping or a reverse proxy (nginx/traefik)
3. **Environment variables**: Sensitive data should be passed via environment variables or secrets

## Production Recommendations

1. **Use a reverse proxy** (nginx/traefik) in front of the container for:
   - SSL/TLS termination
   - Port 80/443 access
   - Load balancing
   - Rate limiting

2. **Use Docker secrets** or environment files for sensitive configuration

3. **Monitor health checks** in your orchestration platform (Kubernetes, Docker Swarm, etc.)

4. **Use multi-stage builds** if you need to optimize image size further
