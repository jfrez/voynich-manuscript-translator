#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract simple English glosses from Whitaker WORDS DICTLINE.GEN.")
    ap.add_argument("--dictline", default="data/lexicon/latin_dictline.gen", help="DICTLINE.GEN file")
    ap.add_argument("--out", default="data/lexicon/latin_whitaker_gloss.json", help="Output JSON lemma->gloss")
    args = ap.parse_args(argv)

    src = pathlib.Path(args.dictline)
    if not src.exists():
        print("Missing DICTLINE.GEN. Run: python scripts/download_latin_wordlist.py", file=sys.stderr)
        return 2

    text = src.read_bytes().decode("latin-1", errors="replace")
    out = {}
    for ln in text.splitlines():
        m = re.match(r"^([A-Za-z]+)\s+", ln)
        if not m:
            continue
        lemma = m.group(1).lower()
        # English definitions are after ';' in DICTLINE lines
        if ";" not in ln:
            continue
        gloss = ln.split(";", 1)[1].strip()
        # keep the first clause
        gloss = gloss.split(";", 1)[0].strip()
        gloss = gloss[:160]
        if lemma and lemma not in out:
            out[lemma] = gloss

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(out)} lemma glosses -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
