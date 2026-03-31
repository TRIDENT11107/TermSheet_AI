"""
Document extraction utilities for TermSheet AI.

This module normalizes text extraction across supported input formats and
returns structured metadata that the API can include in responses.
"""

from __future__ import annotations

import io
import os
from typing import Dict, List, Tuple

import pandas as pd

from .ocr_utils import extract_text_from_image
from .pdf_utils import extract_text_from_pdf


ERROR_PREFIXES = (
    "error processing",
    "ocr processing not available",
    "pdf processing not available",
    "the file does not appear to be a valid pdf",
    "no text could be extracted from the pdf",
)


SUPPORTED_EXTENSIONS = {
    "pdf",
    "txt",
    "csv",
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "tiff",
    "docx",
    "xls",
    "xlsx",
}


def _decode_text_bytes(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="ignore")


def _is_extraction_error(text: str) -> bool:
    normalized = text.lower().strip()
    return any(normalized.startswith(prefix) for prefix in ERROR_PREFIXES)


def _extract_text_from_txt_or_csv(file_stream) -> str:
    file_stream.seek(0)
    raw_bytes = file_stream.read()
    return _decode_text_bytes(raw_bytes)


def _extract_text_from_docx(file_stream) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError(
            "DOCX support requires python-docx. Install with: pip install python-docx"
        ) from exc

    file_stream.seek(0)
    data = io.BytesIO(file_stream.read())
    document = Document(data)
    lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(lines)


def _extract_text_from_excel(file_stream, extension: str) -> str:
    file_stream.seek(0)
    data = io.BytesIO(file_stream.read())

    engine = None
    if extension == "xlsx":
        engine = "openpyxl"
    elif extension == "xls":
        engine = "xlrd"

    try:
        workbook = pd.ExcelFile(data, engine=engine)
    except ImportError as exc:
        package_hint = "openpyxl" if extension == "xlsx" else "xlrd"
        raise RuntimeError(
            f"{extension.upper()} support requires {package_hint}. Install with: pip install {package_hint}"
        ) from exc

    lines: List[str] = []
    for sheet_name in workbook.sheet_names:
        sheet_df = workbook.parse(sheet_name, dtype=str).fillna("")
        lines.append(f"Sheet: {sheet_name}")
        for _, row in sheet_df.iterrows():
            row_values = [str(value).strip() for value in row.tolist() if str(value).strip()]
            if row_values:
                lines.append(" | ".join(row_values))
    return "\n".join(lines)


def extract_text_from_upload(file_storage) -> Tuple[str, Dict[str, object]]:
    filename = file_storage.filename or ""
    extension = os.path.splitext(filename.lower())[1].lstrip(".")
    if not extension:
        raise ValueError("Uploaded file has no extension.")

    if extension == "doc":
        raise ValueError("DOC is not supported directly. Please upload DOCX, PDF, or TXT.")

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    warnings: List[str] = []
    stream = file_storage.stream

    if extension in {"png", "jpg", "jpeg", "bmp", "tiff"}:
        text = extract_text_from_image(stream)
        source_type = "image_ocr"
    elif extension == "pdf":
        text = extract_text_from_pdf(stream)
        source_type = "pdf"
    elif extension in {"txt", "csv"}:
        text = _extract_text_from_txt_or_csv(stream)
        source_type = "text"
    elif extension == "docx":
        text = _extract_text_from_docx(stream)
        source_type = "docx"
    elif extension in {"xls", "xlsx"}:
        text = _extract_text_from_excel(stream, extension)
        source_type = "spreadsheet"
    else:
        raise ValueError(
            f"Unsupported file type: {extension}. Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    text = (text or "").strip()
    if not text:
        raise ValueError("No readable text was extracted from the uploaded file.")
    if _is_extraction_error(text):
        raise ValueError(text)

    if len(text) < 150:
        warnings.append("Extracted text is short; structure validation confidence may be low.")

    metadata = {
        "filename": filename,
        "extension": extension,
        "source_type": source_type,
        "text_length": len(text),
        "warnings": warnings,
    }
    return text, metadata
