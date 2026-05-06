#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.recipe_model import normalize_word  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Extract a list of 'base words' from EVA transliteration. "
            "Default: unique EVA word types sorted by frequency (token count)."
        )
    )
    ap.add_argument("--pages-dir", default="data/pages", help="Directory produced by scripts/build_pages.py")
    ap.add_argument("--top", type=int, default=500, help="How many most frequent word types to output")
    ap.add_argument("--min-count", type=int, default=1, help="Minimum token frequency to include")
    ap.add_argument("--out", default="data/base_words.txt", help="Output text file path")
    ap.add_argument("--json-out", default="data/base_words.json", help="Output JSON file path")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    index_path = pages_dir / "index.json"
    if not index_path.exists():
        print("Missing data/pages/index.json. Run: python scripts/build_pages.py", file=sys.stderr)
        return 2

    index = json.loads(index_path.read_text(encoding="utf-8"))
    counter: Counter[str] = Counter()

    for meta in index:
        folio = meta["folio"]
        eva_path = pages_dir / f"{folio}.eva.txt"
        if not eva_path.exists():
            continue
        text = eva_path.read_text(encoding="utf-8", errors="replace")
        words = re.findall(r"[A-Za-z]+", text)
        counter.update(normalize_word(w) for w in words if w.strip())

    items = [(w, c) for w, c in counter.most_common() if c >= args.min_count]
    if args.top:
        items = items[: args.top]

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(w for w, _c in items) + "\n", encoding="utf-8")

    json_out = pathlib.Path(args.json_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(
            [{"word": w, "count": c, "rank": i + 1} for i, (w, c) in enumerate(items)],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(items)} base words -> {out_path} and {json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
