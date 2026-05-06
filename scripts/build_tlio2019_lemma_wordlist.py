#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


LEMMA_RE = re.compile(
    r"^([A-Z][A-Z'·\\- ]{2,})\\s+((s|agg|v|prep|cong|avv|pron|art|interj)\\.)",
    re.IGNORECASE,
)


def normalize_lemma(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("’", "'").replace("·", "").replace("-", " ")
    s = re.sub(r"\\s+", " ", s).strip()
    return s


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract a TLIO 2019 lemma wordlist from downloaded PDFs (best-effort).")
    ap.add_argument("--pdf-dir", default="data/lexicon/tlio2019_pdfs", help="Directory containing TLIO 2019 PDFs.")
    ap.add_argument("--out", default="data/lexicon/tlio2019_lemmas.txt", help="Output lemma list path.")
    ap.add_argument("--keep-txt", action="store_true", help="Keep intermediate .txt files next to PDFs.")
    args = ap.parse_args(argv)

    pdf_dir = pathlib.Path(args.pdf_dir)
    if not pdf_dir.exists():
        print(f"Missing PDF dir: {pdf_dir}. Run: python scripts/download_tlio2019_from_urls.py", file=sys.stderr)
        return 2

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}", file=sys.stderr)
        return 2

    lemmas = set()
    txt_dir = pdf_dir / "_txt"
    txt_dir.mkdir(parents=True, exist_ok=True)

    for pdf in pdfs:
        txt = txt_dir / (pdf.stem + ".txt")
        if not txt.exists():
            subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
        for ln in txt.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LEMMA_RE.match(ln.strip())
            if not m:
                continue
            lemma = normalize_lemma(m.group(1))
            # avoid extremely short artifacts
            if len(lemma) < 2:
                continue
            lemmas.add(lemma)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(sorted(lemmas)) + "\n", encoding="utf-8")

    if not args.keep_txt:
        # keep the folder (may contain useful debug), but files can be large; user can delete manually.
        pass

    print(f"Wrote {len(lemmas)} lemmas -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

