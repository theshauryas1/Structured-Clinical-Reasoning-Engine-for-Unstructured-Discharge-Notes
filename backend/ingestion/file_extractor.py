import io
import os
import shutil
import requests
from typing import Tuple

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    # Check if tesseract executable exists
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None
    Image = None
    TESSERACT_AVAILABLE = False

from backend.groq_guardrails import load_groq_settings


def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF dependency is not installed on the server.")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    # If the PDF is scanned (contains no text metadata), run OCR fallback
    if len(text.strip()) < 100:
        if not TESSERACT_AVAILABLE:
            raise RuntimeError(
                "PDF contains no text and Tesseract OCR is not installed or available on this host. "
                "Unable to parse scanned PDF."
            )
        ocr_text = ""
        for page in doc:
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            ocr_text += pytesseract.image_to_string(img) + "\n"
        if ocr_text.strip():
            text = ocr_text

    return text


def extract_text_from_image(file_bytes: bytes) -> str:
    if not TESSERACT_AVAILABLE:
        raise RuntimeError(
            "Tesseract OCR is not installed or available on this host. Scanned images cannot be parsed."
        )
    img = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(img)


def transcribe_audio(file_bytes: bytes, file_name: str) -> str:
    # Try Groq Speech-to-Text first (Whisper-large-v3)
    groq_settings = load_groq_settings()
    if groq_settings.api_key:
        headers = {"Authorization": f"Bearer {groq_settings.api_key}"}
        files = {
            "file": (file_name, file_bytes),
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "json"
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("text", "")
        else:
            raise RuntimeError(f"Groq Whisper transcription API failed (status {response.status_code}): {response.text}")

    # Try OpenAI Speech-to-Text fallback (Whisper-1)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        headers = {"Authorization": f"Bearer {openai_key}"}
        files = {
            "file": (file_name, file_bytes),
        }
        data = {
            "model": "whisper-1",
            "response_format": "json"
        }
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("text", "")
        else:
            raise RuntimeError(f"OpenAI Whisper transcription API failed (status {response.status_code}): {response.text}")

    raise RuntimeError("No Speech-to-Text API key configured (neither GROQ_API_KEY nor OPENAI_API_KEY is set).")


def extract_content(file_bytes: bytes, file_name: str, content_type: str) -> Tuple[str, str]:
    """
    Extracts plain text content from uploaded file bytes depending on the content type / filename.
    Returns:
        (extracted_text, warnings)
    """
    ext = os.path.splitext(file_name.lower())[1]
    text = ""
    warnings = []

    # Handle text files
    if content_type == "text/plain" or ext == ".txt":
        text = file_bytes.decode("utf-8", errors="ignore")

    # Handle PDF files
    elif content_type == "application/pdf" or ext == ".pdf":
        text = extract_text_from_pdf(file_bytes)

    # Handle image files
    elif content_type.startswith("image/") or ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
        text = extract_text_from_image(file_bytes)
        warnings.append("Note: Image OCR extraction results may be imperfect. Handwritten notes are not supported.")

    # Handle audio files
    elif content_type.startswith("audio/") or ext in {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac"}:
        text = transcribe_audio(file_bytes, file_name)

    else:
        raise ValueError(f"Unsupported file format: {file_name} ({content_type})")

    if not text.strip():
        raise ValueError("Could not extract any readable text from the uploaded file.")

    return text, ", ".join(warnings) if warnings else ""
