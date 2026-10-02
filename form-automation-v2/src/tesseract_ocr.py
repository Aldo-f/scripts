"""
Tesseract OCR Fallback for Image CAPTCHA
Lightweight image-to-text for simple visual CAPTCHAs
"""
import logging
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger("form_automation.tesseract_ocr")


def solve_image_captcha(image_path: str, config: str = "--psm 7 --oem 3") -> str:
    """Extract text from CAPTCHA image using Tesseract OCR."""
    try:
        import pytesseract
    except ImportError:
        logger.warning("pytesseract not installed, skipping OCR")
        return ""

    try:
        img = Image.open(image_path)

        # Preprocess: convert to grayscale, increase contrast
        img = img.convert("L")  # grayscale
        # Could add thresholding here if needed

        text = pytesseract.image_to_string(img, config=config).strip()

        # Clean up - only alphanumeric
        cleaned = "".join(c for c in text if c.isalnum() or c.isspace())
        logger.info(f"Tesseract OCR result: '{cleaned}'")

        return cleaned

    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return ""


def preprocess_captcha_image(image_path: str) -> str:
    """Enhance CAPTCHA image for better OCR accuracy."""
    try:
        img = Image.open(image_path)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Resize if too small (minimum 100px height)
        if img.height < 100:
            scale = 100 / img.height
            new_size = (int(img.width * scale), 100)
            img = img.resize(new_size, Image.LANCZOS)

        processed_path = str(Path(image_path).with_suffix(".processed.png"))
        img.save(processed_path)

        return processed_path

    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}")
        return image_path