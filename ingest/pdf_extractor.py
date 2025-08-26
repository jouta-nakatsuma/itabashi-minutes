
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
