from __future__ import annotations
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Optional provider aliases (resolved at import time)
try:
    from pypdf import PdfReader as PYPDF_READER  # type: ignore[assignment]
except Exception:  # pragma: no cover - environment without pypdf
    PYPDF_READER = None  # type: ignore[assignment]

try:
    from pdfminer.high_level import extract_pages as PDFMINER_EXTRACT_PAGES  # type: ignore[assignment]
    from pdfminer.layout import LTTextContainer as PDFMINER_LT  # type: ignore[assignment]
except Exception:  # pragma: no cover - environment without pdfminer.six
    PDFMINER_EXTRACT_PAGES = None  # type: ignore[assignment]
    PDFMINER_LT = None  # type: ignore[assignment]


def _extract_with_pypdf(path: str, max_pages: Optional[int] = None) -> List[str]:
    if PYPDF_READER is None:
        raise RuntimeError("pypdf is not available")
    reader = PYPDF_READER(path)  # type: ignore[operator]
    texts: List[str] = []
    for i, page in enumerate(reader.pages):
        if max_pages is not None and i >= max_pages:
            break
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        texts.append(txt.strip())
    return texts


def _extract_with_pdfminer(path: str, max_pages: Optional[int] = None) -> List[str]:
    if PDFMINER_EXTRACT_PAGES is None or PDFMINER_LT is None:
        raise RuntimeError("pdfminer.six is not available")
    texts: List[str] = []
    for i, page_layout in enumerate(PDFMINER_EXTRACT_PAGES(path)):  # type: ignore[misc]
        if max_pages is not None and i >= max_pages:
            break
        parts: List[str] = []
        try:
            for element in page_layout:
                if isinstance(element, PDFMINER_LT):  # type: ignore[arg-type]
                    parts.append(element.get_text() or "")
        except Exception:
            # レイアウト走査で例外が出てもそのページは空文字扱い
            parts = []
        texts.append("".join(parts).strip())
    return texts


def extract_text_per_page(
    path: str, max_pages: Optional[int] = None, provider: str = "auto"
) -> List[str]:
    """
    Extract per-page text as list[str].
    provider:
      - "auto": try pypdf then fallback to pdfminer on failure
      - "pypdf": use pypdf only
      - "pdfminer": use pdfminer only
    """
    if provider not in ("auto", "pypdf", "pdfminer"):
        raise ValueError(f"unknown provider: {provider}")

    if provider in ("auto", "pypdf"):
        try:
            texts = _extract_with_pypdf(path, max_pages=max_pages)
            logger.info("extracted with pypdf: pages=%d path=%s", len(texts), path)
            return texts
        except Exception as e:
            if provider == "pypdf":
                raise
            logger.warning("pypdf failed (%s). fallback to pdfminer: %s", type(e).__name__, path)

    # fallback or explicit pdfminer
    texts = _extract_with_pdfminer(path, max_pages=max_pages)
    logger.info("extracted with pdfminer: pages=%d path=%s", len(texts), path)
    return texts


def is_scanned_heuristic(path: str, sample_pages: int = 5) -> bool:
    """
    Heuristic: consider as scanned if >= 50% of sampled pages have zero-length text.
    """
    try:
        texts = extract_text_per_page(path, max_pages=sample_pages, provider="auto")
    except Exception:
        return False
    if not texts:
        return False
    zero = sum(1 for t in texts if not t.strip())
    return (zero / len(texts)) >= 0.5


def ocr_pages_stub(path: str, lang: str = "jpn"):
    """
    Placeholder for future OCR integration (e.g., Tesseract/Cloud OCR).
    """
    raise NotImplementedError("OCR not implemented yet; this is a stub.")

