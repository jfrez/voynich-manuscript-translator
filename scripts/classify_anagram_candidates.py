#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


ITALIAN_FUNCTION_WORDS = {
    "a",
    "ad",
    "al",
    "allo",
    "alla",
    "alle",
    "agli",
    "ai",
    "da",
    "dal",
    "dallo",
    "dalla",
    "delle",
    "dei",
    "del",
    "dell",
    "di",
    "e",
    "ed",
    "il",
    "lo",
    "la",
    "i",
    "gli",
    "le",
    "in",
    "nel",
    "nello",
    "nella",
    "nei",
    "sul",
    "sullo",
    "sulla",
    "su",
    "per",
    "tra",
    "fra",
    "con",
    "o",
    "un",
    "una",
    "uno",
    "che",
    "non",
    "si",
    "no",
    "piu",
    "meno",
    "ma",
}


def is_generic_candidate(w: str) -> bool:
    if w in ITALIAN_FUNCTION_WORDS:
        return True
    if len(w) <= 3:
        return True
    # very common-looking short words
    if len(w) == 4 and re.fullmatch(r"[a-z]{4}", w):
        return True
    return False


def classify_row(row: dict, max_candidates_generic: int, min_len_nongeneric: int) -> dict:
    cands = row.get("anagram_candidates") or []
    cands = [c.lower() for c in cands]
    # If the first candidate is generic, treat as generic
    first = cands[0] if cands else ""

    generic = False
    reasons = []

    if not cands:
        generic = True
        reasons.append("no_candidates")
    else:
        if is_generic_candidate(first):
            generic = True
            reasons.append("first_candidate_generic_or_short")

        if len(cands) >= max_candidates_generic:
            generic = True
            reasons.append("too_many_candidates")

        if row.get("italianized") and len(str(row["italianized"])) < min_len_nongeneric:
            generic = True
            reasons.append("italianized_too_short")

    return {
        **row,
        "generic": generic,
        "generic_reasons": reasons,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Classify anagram matches into generic vs non-generic (heuristic).")
    ap.add_argument("--in", dest="inp", default="data/base_words_wikwik_anagrams_unrestricted.json", help="Input JSON from scripts/italianized_anagrams.py")
    ap.add_argument("--out", default="data/base_words_wikwik_anagrams_unrestricted_classified.json", help="Output JSON path")
    ap.add_argument("--max-cands-generic", type=int, default=25, help="If >= this many candidates, label generic")
    ap.add_argument("--min-len-nongeneric", type=int, default=5, help="Minimum italianized length to allow non-generic")
    args = ap.parse_args(argv)

    inp = pathlib.Path(args.inp)
    obj = json.loads(inp.read_text(encoding="utf-8"))
    rows = obj.get("rows", [])

    out_rows = [classify_row(r, args.max_cands_generic, args.min_len_nongeneric) for r in rows]

    generic = [r for r in out_rows if r["generic"]]
    nongeneric = [r for r in out_rows if not r["generic"]]

    out_obj = {
        "source": str(inp),
        "params": {"max_cands_generic": args.max_cands_generic, "min_len_nongeneric": args.min_len_nongeneric},
        "counts": {"total": len(out_rows), "generic": len(generic), "non_generic": len(nongeneric)},
        "rows": out_rows,
    }

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote classified file -> {out}", file=sys.stderr)
    print(f"Total={len(out_rows)} generic={len(generic)} non_generic={len(nongeneric)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
