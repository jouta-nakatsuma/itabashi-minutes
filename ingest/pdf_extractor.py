
#!/usr/bin/env python3
import argparse, json, sys, logging
from pathlib import Path
from datetime import datetime

EXTRACTOR_VERSION = "0.1.0"

def setup_logger(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)

def extract_pages_with_pypdf(pdf_path: Path):
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError(
            "pypdf が見つからないか読み込みに失敗しました。`poetry add pypdf` を実行してください。"
        ) from e
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({"page": i + 1, "text": text})
    return pages

def main():
    p = argparse.ArgumentParser(description="PDF をページごとにテキスト抽出して JSON 出力します。")
    p.add_argument("pdf", help="入力PDFパス")
    p.add_argument("-o","--output", help="出力JSONパス（未指定なら <pdf名>.json）")
    p.add_argument("--stdout", action="store_true", help="標準出力にJSONを出す（ファイルは書かない）")
    p.add_argument("-v","--verbose", action="store_true", help="詳細ログ")
    args = p.parse_args()

    setup_logger(args.verbose)

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logging.error("PDFが見つかりません: %s", pdf_path)
        return 2

    logging.info("抽出開始: %s", pdf_path)
    pages = extract_pages_with_pypdf(pdf_path)
    num_pages = len(pages)
    logging.info("抽出完了: %dページ", num_pages)

    result = {
        "source_pdf": str(pdf_path),
        "num_pages": num_pages,
        "pages": pages,
        "extractor_version": EXTRACTOR_VERSION,
        "extracted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    if args.stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        out_path = Path(args.output) if args.output else pdf_path.with_suffix(".json")
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.info("JSONを書き出しました: %s", out_path)

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.exception("抽出中にエラー: %s", e)
        sys.exit(1)


# --- Glyph patch: add extract_text_per_page() for CLI/tests compatibility ---
from typing import List, Union

def extract_text_per_page(pdf_path: Union[str, Path]) -> List[str]:
    """
    Return a list of page texts extracted from the PDF.
    This function is kept simple for CLI/tests compatibility.
    """
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError(
            "pypdf が必要です。`poetry add pypdf` を実行してください。"
        ) from e

    p = Path(pdf_path)
    reader = PdfReader(str(p))
    texts: List[str] = []
    for pg in reader.pages:
        try:
            t = pg.extract_text() or ""
        except Exception:
            t = ""
        texts.append(t)
    return texts

# 既存の JSON 出力用関数がある場合は、それをこの関数で内包できるように軽いエイリアスも用意
def _extract_pages_with_pypdf_compat(pdf_path: Union[str, Path]):
    pages = extract_text_per_page(pdf_path)
    return [{"page": i+1, "text": txt} for i, txt in enumerate(pages)]
# --- end patch ---


# --- Glyph patch: provider-aware extract_text_per_page (auto/pypdf/pdfminer) ---
from typing import List, Union, Iterator

# テストで monkeypatch しやすいようフックを用意
try:
    from pypdf import PdfReader as _DefaultPdfReader
except Exception:
    _DefaultPdfReader = None
PYPDF_READER = _DefaultPdfReader

try:
    from pdfminer.high_level import extract_pages as _default_extract_pages
    from pdfminer.layout import LTTextContainer as _default_lt
except Exception:
    _default_extract_pages = None
    _default_lt = None
PDFMINER_EXTRACT_PAGES = _default_extract_pages
PDFMINER_LT = _default_lt

def _via_pypdf(path: Union[str, Path]) -> List[str]:
    if PYPDF_READER is None:
        raise RuntimeError("pypdf not available")
    r = PYPDF_READER(str(path))
    out: List[str] = []
    for pg in getattr(r, "pages", []):
        try:
            out.append(pg.extract_text() or "")
        except Exception:
            out.append("")
    return out

def _via_pdfminer(path: Union[str, Path]) -> List[str]:
    if PDFMINER_EXTRACT_PAGES is None or PDFMINER_LT is None:
        raise RuntimeError("pdfminer not available")
    out: List[str] = []
    for page in PDFMINER_EXTRACT_PAGES(str(path)):
        buf: List[str] = []
        for elem in page:
            if isinstance(elem, PDFMINER_LT):
                try:
                    buf.append(elem.get_text())
                except Exception:
                    pass
        out.append("".join(buf))
    return out

def extract_text_per_page(pdf_path: Union[str, Path], provider: str = "auto") -> List[str]:
    prov = (provider or "auto").lower()
    if prov == "pypdf":
        return _via_pypdf(pdf_path)
    if prov == "pdfminer":
        return _via_pdfminer(pdf_path)
    # auto: pypdf → 失敗時 pdfminer
    try:
        return _via_pypdf(pdf_path)
    except Exception:
        return _via_pdfminer(pdf_path)
# --- end patch ---
