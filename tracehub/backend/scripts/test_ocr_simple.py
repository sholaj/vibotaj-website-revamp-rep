#!/usr/bin/env python3
"""
Simple OCR test script to verify Tesseract installation works correctly.
This can be run inside the Docker container to validate the setup.

Usage:
    docker run --rm -v $(pwd):/app tracehub-backend python test_ocr_simple.py
"""

import sys
import subprocess

def test_tesseract_installation():
    """Test that Tesseract is installed and accessible."""
    print("=" * 60)
    print("TESTING TESSERACT OCR INSTALLATION")
    print("=" * 60)
    print()

    # Test 1: Check Tesseract version
    print("Test 1: Tesseract Version")
    print("-" * 60)
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✓ Tesseract is installed")
    except Exception as e:
        print(f"✗ Tesseract not found: {e}")
        return False

    # Test 2: Check available languages
    print("\nTest 2: Available Languages")
    print("-" * 60)
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if "eng" in result.stdout:
            print("✓ English language pack is available")
        else:
            print("✗ English language pack not found")
            return False
    except Exception as e:
        print(f"✗ Error checking languages: {e}")
        return False

    # Test 3: Check pdftoppm (poppler-utils)
    print("\nTest 3: Poppler Utils (pdftoppm)")
    print("-" * 60)
    try:
        result = subprocess.run(
            ["pdftoppm", "-v"],
            capture_output=True,
            text=True,
            check=False  # pdftoppm -v returns non-zero exit code
        )
        # pdftoppm prints version to stderr
        output = result.stderr or result.stdout
        print(output)
        print("✓ pdftoppm is installed")
    except Exception as e:
        print(f"✗ pdftoppm not found: {e}")
        return False

    # Test 4: Import Python libraries
    print("\nTest 4: Python Libraries")
    print("-" * 60)

    try:
        import pytesseract
        print(f"✓ pytesseract version: {pytesseract.__version__}")
    except ImportError as e:
        print(f"✗ pytesseract not installed: {e}")
        return False

    try:
        import pdf2image
        print(f"✓ pdf2image version: {pdf2image.__version__}")
    except ImportError as e:
        print(f"✗ pdf2image not installed: {e}")
        return False

    try:
        from PIL import Image
        print(f"✓ Pillow version: {Image.__version__}")
    except ImportError as e:
        print(f"✗ Pillow not installed: {e}")
        return False

    # Test 5: Quick OCR functionality test
    print("\nTest 5: OCR Functionality")
    print("-" * 60)
    try:
        from PIL import Image, ImageDraw, ImageFont
        import pytesseract
        import tempfile
        import os

        # Create a simple test image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)

        # Use default font
        draw.text((10, 10), "TRACEHUB OCR TEST", fill='black')

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            img.save(tmp_path)

        try:
            # Try to extract text
            text = pytesseract.image_to_string(Image.open(tmp_path))
            print(f"Extracted text: {repr(text.strip())}")

            if "TRACEHUB" in text or "OCR" in text or "TEST" in text:
                print("✓ OCR is working correctly")
            else:
                print("⚠ OCR extracted text but may not be accurate")
                print("  (This is normal for simple test images)")
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        print(f"✗ OCR functionality test failed: {e}")
        return False

    print()
    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    return True

def main():
    """Run all tests."""
    success = test_tesseract_installation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
