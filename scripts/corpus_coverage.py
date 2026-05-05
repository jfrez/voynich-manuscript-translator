#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.recipe_model import CONNECTORS, COMPOUNDS, longest_tokenize, normalize_word  # noqa: E402


STATE_TOKENS = {"e", "ee", "eee", "i", "ii", "iii", "a"}
SUFFIX_TOKENS = {"dy", "iin", "aiin"}
ALLOWED = set(COMPOUNDS.keys()) | set(CONNECTORS) | STATE_TOKENS | SUFFIX_TOKENS


def is_covered(word: str) -> bool:
    tokens = longest_tokenize(word)
    return all(t in ALLOWED for t in tokens)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Estimate how many EVA words are fully covered by the current token grammar.")
    ap.add_argument("--pages-dir", default="data/pages", help="Directory produced by scripts/build_pages.py")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    index = json.loads((pages_dir / "index.json").read_text(encoding="utf-8"))

    token_total = 0
    token_covered = 0

    types: set[str] = set()
    covered_types: set[str] = set()

    for meta in index:
        folio = meta["folio"]
        eva_path = pages_dir / f"{folio}.eva.txt"
        if not eva_path.exists():
            continue
        text = eva_path.read_text(encoding="utf-8", errors="replace")
        words = re.findall(r"[A-Za-z]+", text)
        for w in words:
            token_total += 1
            types.add(w)
            if is_covered(w):
                token_covered += 1
                covered_types.add(w)

    res = {
        "tokens_total": token_total,
        "tokens_covered": token_covered,
        "token_coverage": (token_covered / token_total) if token_total else 0.0,
        "types_total": len(types),
        "types_covered": len(covered_types),
        "type_coverage": (len(covered_types) / len(types)) if types else 0.0,
        "notes": [
            "This is a strict token-coverage metric: a word is 'covered' only if tokenization yields only known markers.",
            "It is not a linguistic or semantic coverage metric and does not validate any hypothesis about Voynich meaning.",
        ],
    }

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"Token coverage: {res['tokens_covered']}/{res['tokens_total']} = {res['token_coverage']:.3%}")
        print(f"Type coverage:  {res['types_covered']}/{res['types_total']} = {res['type_coverage']:.3%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

