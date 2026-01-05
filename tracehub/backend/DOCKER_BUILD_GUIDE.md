# Docker Build & Deployment Guide

## Quick Start

### Build the Image
```bash
cd /Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend
docker build -t tracehub-backend .
```

### Run Tests
```bash
# Test OCR installation
./test_docker_ocr.sh

# Or manually test inside container
docker run --rm tracehub-backend python test_ocr_simple.py
```

### Run the Container
```bash
# Development mode (with env file)
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  tracehub-backend

# With environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  tracehub-backend
```

## Docker Compose (Recommended)

If you have a `docker-compose.yml` file, use:

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
```

## Image Details

### Size Estimate
- Base image (python:3.11-slim): ~125 MB
- With all dependencies: ~220-250 MB
- Final image with app code: ~250-280 MB

### Installed System Packages
- gcc (C compiler for building Python packages)
- libpq-dev (PostgreSQL development libraries)
- tesseract-ocr (OCR engine)
- tesseract-ocr-eng (English language pack)
- poppler-utils (PDF utilities)
- libjpeg-dev (JPEG support)
- zlib1g-dev (Compression library)

### Python Packages for OCR
- pytesseract>=0.3.10
- pdf2image>=1.16.0
- Pillow>=10.0.0
- PyMuPDF>=1.23.0

## Verification Commands

### Inside Container
```bash
# Check Tesseract
docker run --rm tracehub-backend tesseract --version

# List available languages
docker run --rm tracehub-backend tesseract --list-langs

# Check pdftoppm
docker run --rm tracehub-backend pdftoppm -v

# Run Python OCR test
docker run --rm tracehub-backend python test_ocr_simple.py
```

### Image Management
```bash
# List images
docker images tracehub-backend

# Remove old images
docker image prune -f

# Tag for registry
docker tag tracehub-backend:latest your-registry/tracehub-backend:v1.0
```

## Multi-Stage Build (Optional Future Enhancement)

For production, consider a multi-stage build to reduce image size:

```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libjpeg62 \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Ensure scripts use local packages
ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Build Fails
```bash
# Clear Docker cache and rebuild
docker builder prune -a
docker build --no-cache -t tracehub-backend .
```

### Permission Issues with Uploads
```bash
# Create uploads directory with correct permissions
mkdir -p uploads
chmod 777 uploads  # or use proper user/group ownership

# Run container with volume
docker run -v $(pwd)/uploads:/app/uploads tracehub-backend
```

### OCR Not Working
```bash
# Test Tesseract inside container
docker run --rm -it tracehub-backend /bin/bash
tesseract --version
tesseract --list-langs

# Test Python libraries
docker run --rm tracehub-backend python -c "import pytesseract, pdf2image; print('OK')"
```

## Production Deployment

### Using Docker Hub
```bash
# Build
docker build -t your-username/tracehub-backend:latest .

# Push
docker login
docker push your-username/tracehub-backend:latest

# Pull on server
docker pull your-username/tracehub-backend:latest
```

### Using GitHub Container Registry
```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag
docker tag tracehub-backend ghcr.io/your-org/tracehub-backend:latest

# Push
docker push ghcr.io/your-org/tracehub-backend:latest
```

### Health Checks
Add to Dockerfile for production:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

Or in docker-compose.yml:
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Environment Variables

Required environment variables for the container:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/tracehub

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Optional: API Keys
VIZION_API_KEY=your-vizion-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Next Steps

1. Test the build: `./test_docker_ocr.sh`
2. Run the container locally
3. Test OCR functionality with real PDFs
4. Deploy to staging/production
5. Set up CI/CD pipeline for automatic builds

## Related Files
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/Dockerfile` - Main Dockerfile
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/test_docker_ocr.sh` - Build test script
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/test_ocr_simple.py` - OCR functionality test
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/DOCKER_OCR_SETUP.md` - Technical documentation
