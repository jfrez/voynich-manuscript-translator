#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import urllib.request


DICTLINE_URL = "https://raw.githubusercontent.com/mk270/whitakers-words/master/DICTLINE.GEN"
UA = "voynich-recipe-research-bot/0.1"


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download a Latin wordlist (Whitaker's WORDS DICTLINE.GEN) and extract lemmas.")
    ap.add_argument("--out-dir", default="data/lexicon", help="Output directory")
    ap.add_argument("--force", action="store_true", help="Re-download even if files exist")
    args = ap.parse_args(argv)

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / "latin_dictline.gen"
    lemmas_path = out_dir / "latin_words_whitaker.txt"

    if (not raw_path.exists()) or args.force:
        data = download(DICTLINE_URL)
        raw_path.write_bytes(data)
        print(f"Downloaded -> {raw_path}", file=sys.stderr)

    # Extract lemma at line start; keep simple ASCII a-z
    # DICTLINE.GEN is Latin-1-ish; decode permissively.
    text = raw_path.read_bytes().decode("latin-1", errors="replace")
    lemmas = set()
    for ln in text.splitlines():
        m = re.match(r"^([A-Za-z]+)", ln)
        if not m:
            continue
        w = m.group(1).lower()
        if re.fullmatch(r"[a-z]+", w):
            lemmas.add(w)

    lemmas_sorted = sorted(lemmas)
    lemmas_path.write_text("\n".join(lemmas_sorted) + "\n", encoding="utf-8")
    print(f"Wrote {len(lemmas_sorted)} Latin lemmas -> {lemmas_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

