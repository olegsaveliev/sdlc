# Docker Run Fix

## Issues Found

1. **Missing Dependencies**: `jinja2`, `python-dotenv`, and `pydantic-settings` were missing from requirements.txt
2. **Port Mapping Mismatch**: Container runs on port 8000, but you mapped to port 80

## Fixed

✅ Added missing dependencies to `requirements.txt`
✅ Updated port mapping instructions

## Correct Commands

### 1. Rebuild the image (after fixing requirements.txt):
```bash
docker build -t calculator-api .
```

### 2. Run with correct port mapping:
```bash
# Map host port 8001 to container port 8000
docker run -p 8001:8000 -d --name calculator-api calculator-api
```

### 3. Or use port 80 externally (map to container's 8000):
```bash
docker run -p 80:8000 -d --name calculator-api calculator-api
```

### 4. Check if it's running:
```bash
docker ps
docker logs calculator-api
```

### 5. Test the application:
```bash
# Web UI
curl http://localhost:8001/

# Health check
curl http://localhost:8001/health

# API endpoint
curl "http://localhost:8001/add?a=10&b=5"
```

## Port Explanation

- **Container internal port**: 8000 (set in Dockerfile)
- **Host port**: Your choice (8001, 80, etc.)
- **Mapping format**: `-p HOST_PORT:CONTAINER_PORT`

Example: `-p 8001:8000` means:
- Access from host on port 8001
- Container listens on port 8000
