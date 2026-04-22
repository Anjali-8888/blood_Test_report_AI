"""
PDF text extraction using PyMuPDF.
Only text-based PDFs are supported.
"""

from __future__ import annotations

import re

import fitz


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract and clean text from a multi-page PDF."""
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Could not open PDF: {exc}") from exc

    try:
        pages: list[str] = []
        for page in document:
            text = _extract_page_text(page)
            if text and text.strip():
                pages.append(text)
    finally:
        document.close()

    if not pages:
        raise ValueError(
            "Could not extract text. PDF may be scanned. Please use a text-based PDF."
        )

    combined = "\n\n".join(pages)
    cleaned = _clean_extracted_text(combined)
    if not cleaned:
        raise ValueError(
            "Could not extract text. PDF may be scanned. Please use a text-based PDF."
        )
    return cleaned


def _clean_extracted_text(text: str) -> str:
    text = text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_page_text(page: fitz.Page) -> str:
    """
    Try a few extraction strategies because some lab PDFs expose text to copy
    but return sparse output for a single mode.
    """
    attempts = [
        page.get_text("text"),
        page.get_text("blocks"),
        page.get_text("words"),
    ]

    text_candidate = _normalize_extraction_attempts(attempts)
    if _looks_like_meaningful_text(text_candidate):
        return text_candidate
    return ""


def _normalize_extraction_attempts(attempts: list) -> str:
    parts: list[str] = []

    for attempt in attempts:
        if isinstance(attempt, str):
            if attempt.strip():
                parts.append(attempt)
            continue

        if isinstance(attempt, list):
            for item in attempt:
                if isinstance(item, (list, tuple)) and item:
                    text_value = item[4] if len(item) > 4 else item[-1]
                    if isinstance(text_value, str) and text_value.strip():
                        parts.append(text_value)

    deduped = "\n".join(dict.fromkeys(part.strip() for part in parts if part.strip()))
    return _clean_extracted_text(deduped)


def _looks_like_meaningful_text(text: str) -> bool:
    if not text:
        return False

    alnum_count = len(re.findall(r"[A-Za-z0-9]", text))
    word_count = len(re.findall(r"\b[A-Za-z0-9]{2,}\b", text))
    return alnum_count >= 30 and word_count >= 6
