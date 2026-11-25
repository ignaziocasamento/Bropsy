from __future__ import annotations

from pathlib import Path

from .store import ALLOWED_SUFFIXES


class ExtractionError(Exception):
    pass


def extract(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ExtractionError(f"Unsupported format: {suffix}")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            sections = []
            for page_number, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    sections.append({"locator": f"p{page_number}", "text": text.strip()})
            if not sections:
                raise ExtractionError("PDF has no extractable text; OCR is not supported")
            return sections
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"PDF extraction failed: {exc}") from exc

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeError as exc:
        raise ExtractionError("Text must be UTF-8") from exc
    if not any(line.strip() for line in lines):
        raise ExtractionError("Source has no readable text")
    sections = []
    for start in range(0, len(lines), 25):
        block = "\n".join(lines[start:start + 25]).strip()
        if block:
            end = min(start + 25, len(lines))
            sections.append({"locator": f"L{start + 1}-L{end}", "text": block})
    return sections
