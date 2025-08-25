from __future__ import annotations
import argparse
import glob as _glob
import json
import logging
import os
from typing import Dict, List

from .pdf_extractor import extract_text_per_page


def _collect_inputs(single: str | None, pattern: str | None) -> List[str]:
    if single and pattern:
        raise SystemExit("--input and --glob are mutually exclusive")
    if not single and not pattern:
        raise SystemExit("either --input or --glob is required")
    if single:
        return [single]
    return sorted(_glob.glob(pattern or "", recursive=True))


def main() -> None:
    # Basic logging setup (optional)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Itabashi Minutes PDF Ingest CLI")
    parser.add_argument("--input", help="Single PDF file path")
    parser.add_argument("--glob", help="Glob pattern to match multiple PDFs (e.g., 'data/**/*.pdf')")
    parser.add_argument("--out", help="Output file path (JSON or NDJSON when --ndjson)", required=True)
    parser.add_argument("--ndjson", action="store_true", help="Write NDJSON (one document per line)")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to parse per file")
    parser.add_argument(
        "--provider",
        choices=["auto", "pypdf", "pdfminer"],
        default="auto",
        help="Extraction provider",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    args = parser.parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    inputs = _collect_inputs(args.input, args.glob)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    docs: List[Dict] = []
    for path in inputs:
        try:
            pages = extract_text_per_page(path, max_pages=args.max_pages, provider=args.provider)
            doc = {"path": path, "num_pages": len(pages), "pages": pages}
            docs.append(doc)
            logging.info("ingested: path=%s pages=%d", path, len(pages))
        except Exception as e:
            logging.warning("failed to ingest %s: %s", path, e)

    if args.ndjson:
        with open(args.out, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    else:
        # single doc => object, multiple => array
        out_obj = docs[0] if len(docs) == 1 else docs
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

