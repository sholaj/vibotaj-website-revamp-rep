# Docker OCR Configuration

## Overview
The TraceHub backend Docker container now includes Tesseract OCR and related dependencies to enable document processing capabilities, particularly for extracting text from scanned PDF documents.

## Installed Packages

### Core Dependencies
- **tesseract-ocr** (v5.x): Open-source OCR engine for text extraction from images
- **tesseract-ocr-eng**: English language training data for Tesseract
- **poppler-utils**: PDF rendering utilities, includes `pdftoppm` for PDF to image conversion

### Supporting Libraries
- **libjpeg-dev**: JPEG image format support
- **zlib1g-dev**: Compression library for image processing

## Dockerfile Changes

The following system packages were added to the base `python:3.11-slim` image:

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
```

## Testing the Build

### Manual Testing
To build and test the Docker image:

```bash
# Build the image
docker build -t tracehub-backend .

# Verify Tesseract installation
docker run --rm tracehub-backend tesseract --version

# Verify poppler-utils installation
docker run --rm tracehub-backend pdftoppm -v

# Check available languages
docker run --rm tracehub-backend tesseract --list-langs
```

### Automated Testing
Use the provided test script:

```bash
cd /Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend
./test_docker_ocr.sh
```

This script will:
1. Build the Docker image
2. Verify Tesseract is installed and working
3. Verify poppler-utils is installed
4. Check language data availability
5. Display the final image size

## Usage in Application

The installed packages enable the following Python libraries to work properly:

### pytesseract
```python
import pytesseract
from PIL import Image

# Extract text from an image
text = pytesseract.image_to_string(Image.open('document.jpg'))
```

### pdf2image
```python
from pdf2image import convert_from_path

# Convert PDF to images (requires poppler-utils)
images = convert_from_path('document.pdf')
```

### Combined OCR Workflow
```python
from pdf2image import convert_from_path
import pytesseract

# Convert PDF pages to images
images = convert_from_path('scanned_document.pdf')

# Extract text from each page
for i, image in enumerate(images):
    text = pytesseract.image_to_string(image)
    print(f"Page {i+1}:\n{text}\n")
```

## Image Size Considerations

The additions increase the image size but are necessary for OCR functionality:
- Base `python:3.11-slim`: ~125 MB
- With OCR packages: ~220-250 MB (estimated)

### Optimization Notes
- Uses `--no-cache-dir` for pip to reduce layer size
- Removes apt cache with `rm -rf /var/lib/apt/lists/*`
- Only installs English language pack (additional languages can be added as needed)
- Uses slim Python base image instead of full Debian

## Adding Additional Languages

To support more languages, add the corresponding Tesseract language packs:

```dockerfile
RUN apt-get update && apt-get install -y \
    # ... existing packages ...
    tesseract-ocr-deu \  # German
    tesseract-ocr-fra \  # French
    tesseract-ocr-spa \  # Spanish
    && rm -rf /var/lib/apt/lists/*
```

Common language codes:
- `eng`: English
- `deu`: German
- `fra`: French
- `spa`: Spanish
- `por`: Portuguese
- `chi_sim`: Simplified Chinese
- `ara`: Arabic

## Troubleshooting

### Issue: "tesseract: command not found"
**Solution**: Rebuild the Docker image to ensure Tesseract is installed

### Issue: "Error opening data file"
**Solution**: Verify language packs are installed:
```bash
docker run --rm tracehub-backend tesseract --list-langs
```

### Issue: "pdftoppm: command not found"
**Solution**: Ensure poppler-utils is installed in the Dockerfile

### Issue: Large image size
**Solution**: If image size is a concern, consider:
1. Using multi-stage builds (not necessary for current setup)
2. Removing unnecessary language packs
3. Using Alpine-based images (more complex due to library differences)

## Dependencies in requirements.txt

Ensure your Python requirements include:

```
pytesseract>=0.3.10
pdf2image>=1.16.0
Pillow>=10.0.0
```

These Python packages work with the system-level Tesseract and Poppler installations.

## Related Files
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/Dockerfile` - Main Dockerfile
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/test_docker_ocr.sh` - Test script
- `/Users/shola/Documents/vibotaj-website-revamp-rep/tracehub/backend/requirements.txt` - Python dependencies
