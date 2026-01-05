#!/bin/bash
# Test script to verify Tesseract OCR and dependencies are installed in Docker container

echo "Building Docker image..."
docker build -t tracehub-backend:test .

if [ $? -ne 0 ]; then
    echo "Docker build failed!"
    exit 1
fi

echo "Docker build successful!"
echo ""

echo "Testing Tesseract OCR installation..."
docker run --rm tracehub-backend:test tesseract --version

if [ $? -ne 0 ]; then
    echo "Tesseract not found in container!"
    exit 1
fi

echo ""
echo "Testing poppler-utils (pdftoppm) installation..."
docker run --rm tracehub-backend:test pdftoppm -v

if [ $? -ne 0 ]; then
    echo "pdftoppm (poppler-utils) not found in container!"
    exit 1
fi

echo ""
echo "Testing Tesseract language data..."
docker run --rm tracehub-backend:test tesseract --list-langs

if [ $? -ne 0 ]; then
    echo "Tesseract language data not properly installed!"
    exit 1
fi

echo ""
echo "All OCR dependencies verified successfully!"
echo ""
echo "Image size:"
docker images tracehub-backend:test --format "{{.Size}}"
