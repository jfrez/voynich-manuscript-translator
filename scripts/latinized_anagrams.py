#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

def romanize_eva(word: str) -> str:
    """
    Reuse the same heuristic mapping as italianized_anagrams.py.
    This is not linguistics; it's a practical mapping for anagram signatures.
    """
    w = word.lower()
    w = w.replace("dy", "__DY__")
    w = w.replace("d", "p")
    w = w.replace("y", "")
    w = w.replace("__DY__", "dy")

    for pat in ("cth", "ckh", "cph", "cfh"):
        w = w.replace(pat, "c")
    w = w.replace("ch", "c")
    w = w.replace("sh", "s")

    w = w.replace("q", "c")
    w = w.replace("k", "c")
    w = w.replace("x", "s")
    w = w.replace("v", "u")

    w = re.sub(r"[^a-z]", "", w)
    return w


def signature(s: str) -> str:
    return "".join(sorted(s))


def load_wordlist(path: pathlib.Path) -> list[str]:
    words = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        w = ln.strip().lower()
        if not w:
            continue
        if re.fullmatch(r"[a-z]+", w):
            words.append(w)
    return words


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Find Latin lemma anagrams after romanizing EVA basewords (heuristic).")
    ap.add_argument("--basewords-sections", default="data/base_words_by_section.json", help="Output of scripts/base_words_by_section.py")
    ap.add_argument("--wordlist", default="data/lexicon/latin_words_whitaker.txt", help="Latin wordlist (one word per line)")
    ap.add_argument("--min-dominance", type=float, default=0.0, help="Min fraction of occurrences in top section to consider")
    ap.add_argument("--min-total", type=int, default=5, help="Min total occurrences to consider")
    ap.add_argument("--max-candidates", type=int, default=20, help="Max anagram candidates to keep per baseword")
    ap.add_argument("--out", default="data/base_words_latin_anagrams_whitaker.json", help="Output JSON path")
    args = ap.parse_args(argv)

    src = pathlib.Path(args.basewords_sections)
    if not src.exists():
        print("Missing base words by section. Run: python scripts/base_words_by_section.py --top 500", file=sys.stderr)
        return 2

    wl_path = pathlib.Path(args.wordlist)
    if not wl_path.exists():
        print("Missing Latin wordlist. Run: python scripts/download_latin_wordlist.py", file=sys.stderr)
        return 2

    payload = json.loads(src.read_text(encoding="utf-8"))
    sections: list[str] = payload["sections"]
    rows: list[dict] = payload["rows"]

    words = load_wordlist(wl_path)
    sig_index: dict[str, list[str]] = defaultdict(list)
    for w in words:
        sig_index[signature(w)].append(w)

    out_rows = []
    for row in rows:
        w = row["word"]
        total = int(row["total"])
        if total < args.min_total:
            continue
        sec_counts = {sec: int(row.get(sec, 0)) for sec in sections}
        top_sec = max(sec_counts, key=lambda k: sec_counts[k])
        top_count = sec_counts[top_sec]
        dominance = (top_count / total) if total else 0.0
        if dominance < args.min_dominance:
            continue

        lat = romanize_eva(w)
        if len(lat) < 3:
            continue
        sig = signature(lat)
        cands = sig_index.get(sig, [])
        if not cands:
            continue
        out_rows.append(
            {
                "baseword": w,
                "total": total,
                "top_section": top_sec,
                "top_section_count": top_count,
                "dominance": round(dominance, 4),
                "romanized": lat,
                "latin_candidates": cands[: args.max_candidates],
            }
        )

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"source_wordlist": str(wl_path), "rows": out_rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Matched {len(out_rows)} basewords -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
