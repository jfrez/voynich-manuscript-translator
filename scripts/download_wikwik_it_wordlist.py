#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request


BASE = "https://it.wikwik.org/"
UA = "voynich-recipe-research-bot/0.1"


HREF_RE = re.compile(r'href=/(?!tutteleparole|liste\\.htm|cercare\\.htm|p1\\.png|o1\\.png|rnd/)([A-Za-z%\\-_.]+)', re.I)


def fetch(path: str) -> str:
    url = urllib.parse.urljoin(BASE, path)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8", errors="replace")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download a large Italian wordlist by scraping it.wikwik.org (Wiktionary-derived).")
    ap.add_argument("--out", default="data/lexicon/wikwik_it_words.txt", help="Output path.")
    ap.add_argument("--pages", type=int, default=1409, help="How many pagination pages to scrape (default 1409).")
    ap.add_argument("--sleep", type=float, default=0.2, help="Sleep between requests (seconds).")
    args = ap.parse_args(argv)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    words = set()

    for i in range(1, args.pages + 1):
        page = "tutteleparole.htm" if i == 1 else f"tutteleparolepagina{i}.htm"
        try:
            html = fetch(page)
        except Exception as e:
            print(f"FAILED page {i}: {e}", file=sys.stderr)
            continue

        for m in HREF_RE.finditer(html):
            slug = urllib.parse.unquote(m.group(1))
            w = slug.strip().lower()
            # Filter: keep alphabetic-ish entries only
            if not re.fullmatch(r"[a-zàèéìòù]+", w):
                continue
            # strip accents for downstream compatibility
            w = (
                w.replace("à", "a")
                .replace("è", "e")
                .replace("é", "e")
                .replace("ì", "i")
                .replace("ò", "o")
                .replace("ù", "u")
            )
            if re.fullmatch(r"[a-z]+", w):
                words.add(w)

        if i % 50 == 0:
            print(f"scraped pages {i}/{args.pages}, unique words={len(words)}", file=sys.stderr)
        time.sleep(args.sleep)

    out_path.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    print(f"Wrote {len(words)} words -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

