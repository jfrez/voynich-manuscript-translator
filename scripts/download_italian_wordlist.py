#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


DEFAULT_URL = "https://raw.githubusercontent.com/napolux/paroleitaliane/main/paroleitaliane/60000_parole_italiane.txt"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download an Italian wordlist (modern Italian; best-effort proxy for older forms).")
    ap.add_argument("--url", default=DEFAULT_URL, help="Wordlist URL (one word per line).")
    ap.add_argument("--out", default="data/lexicon/italian_words.txt", help="Output path.")
    ap.add_argument("--force", action="store_true", help="Re-download even if file exists.")
    args = ap.parse_args(argv)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not args.force:
        print(f"Exists: {out_path}", file=sys.stderr)
        return 0

    cmd = [
        "curl",
        "-L",
        "-f",
        "-A",
        "voynich-recipe-research-bot/0.1",
        "-o",
        str(out_path),
        args.url,
    ]
    subprocess.run(cmd, check=True)
    print(f"Downloaded wordlist -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
