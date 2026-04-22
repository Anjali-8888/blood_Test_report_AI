"""
Optional OCR helpers for scanned/image-heavy PDFs.

This module uses Hugging Face InferenceClient when a token is configured.
"""

from __future__ import annotations

import io
import os

import fitz
from PIL import Image
from huggingface_hub import InferenceClient


def extract_text_with_huggingface_ocr(file_bytes: bytes) -> str:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is not set.")

    model_name = os.getenv("HF_OCR_MODEL", "microsoft/trocr-base-printed").strip()
    page_limit = int(os.getenv("HF_OCR_MAX_PAGES", "3"))

    client = InferenceClient(token=token)
    document = fitz.open(stream=file_bytes, filetype="pdf")

    try:
        page_texts: list[str] = []
        for index, page in enumerate(document):
            if index >= page_limit:
                break
            image_bytes = _render_page_to_png(page)
            output = client.image_to_text(image=image_bytes, model=model_name)
            text = getattr(output, "generated_text", None) or str(output)
            if text and text.strip():
                page_texts.append(text.strip())
    finally:
        document.close()

    combined = "\n\n".join(page_texts).strip()
    if not combined:
        raise RuntimeError("Hugging Face OCR could not extract readable text from this document.")
    return combined


def _render_page_to_png(page: fitz.Page) -> bytes:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
