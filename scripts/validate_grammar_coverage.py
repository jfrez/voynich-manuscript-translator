#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.recipe_model import interpret_text


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate procedural grammar coverage on an EVA/IVTFF snippet.")
    ap.add_argument("--file", default="", help="Read EVA text from a file (optional)")
    ap.add_argument("--text", default="", help="EVA text snippet (optional)")
    ap.add_argument("--top", type=int, default=40, help="Top unknown tokens/words to show")
    args = ap.parse_args()

    if args.file:
        eva_text = open(args.file, "r", encoding="utf-8", errors="replace").read()
    else:
        eva_text = args.text

    if not eva_text.strip():
        print("No input text. Use --text or --file.")
        return 2

    words = re.findall(r"[A-Za-z]+", eva_text)
    interps = interpret_text(eva_text)

    unknown_tok_counts = Counter()
    unmodeled_word_counts = Counter()
    fully_modeled = 0
    has_any_compound = 0

    for w in interps:
        if w.compounds:
            has_any_compound += 1
        if not w.unknown_tokens:
            fully_modeled += 1
        else:
            unmodeled_word_counts[w.word] += 1
            unknown_tok_counts.update(w.unknown_tokens)

    print("== Grammar coverage report ==")
    print(f"word tokens: {len(words)}")
    print(f"words with any compound marker: {has_any_compound} ({has_any_compound/len(words)*100:.1f}%)" if words else "words with any compound marker: 0")
    print(f"fully modeled words (no unknown tokens): {fully_modeled} ({fully_modeled/len(words)*100:.1f}%)" if words else "fully modeled words: 0")
    print(f"words containing unmodeled tokens: {len(words)-fully_modeled} ({(len(words)-fully_modeled)/len(words)*100:.1f}%)" if words else "words containing unmodeled tokens: 0")
    print("")

    print(f"Top unmodeled tokens (n={args.top}):")
    for tok, cnt in unknown_tok_counts.most_common(args.top):
        print(f"- {tok}: {cnt}")
    print("")

    print(f"Top words containing unmodeled tokens (n={args.top}):")
    for word, cnt in unmodeled_word_counts.most_common(args.top):
        print(f"- {word}: {cnt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
