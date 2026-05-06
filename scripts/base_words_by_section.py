#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.recipe_model import normalize_word  # noqa: E402

def load_basewords(path: pathlib.Path, top: int = 0) -> list[str]:
    words = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    if top:
        return words[:top]
    return words


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Associate EVA base words with manuscript sections where they appear.")
    ap.add_argument("--pages-dir", default="data/pages", help="Directory produced by scripts/build_pages.py")
    ap.add_argument("--basewords", default="data/base_words.txt", help="Baseword list (one word per line)")
    ap.add_argument("--top", type=int, default=500, help="How many basewords to analyze from the list")
    ap.add_argument("--out-json", default="data/base_words_by_section.json", help="Output JSON path")
    ap.add_argument("--out-csv", default="data/base_words_by_section.csv", help="Output CSV path")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    idx_path = pages_dir / "index.json"
    if not idx_path.exists():
        print("Missing data/pages/index.json. Run: python scripts/build_pages.py", file=sys.stderr)
        return 2

    base_path = pathlib.Path(args.basewords)
    if not base_path.exists():
        print("Missing baseword list. Run: python scripts/base_words.py", file=sys.stderr)
        return 2

    basewords = load_basewords(base_path, top=args.top)
    base_set = set(w.lower() for w in basewords)

    index = json.loads(idx_path.read_text(encoding="utf-8"))
    sections = sorted({(m.get("section") or "unknown") for m in index})

    # word -> section -> token count
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    totals: Counter[str] = Counter()

    for meta in index:
        folio = meta["folio"]
        section = (meta.get("section") or "unknown")
        eva_path = pages_dir / f"{folio}.eva.txt"
        if not eva_path.exists():
            continue
        text = eva_path.read_text(encoding="utf-8", errors="replace")
        words = re.findall(r"[A-Za-z]+", text)
        for w in words:
            wl = normalize_word(w)
            if wl in base_set:
                counts[wl][section] += 1
                totals[wl] += 1

    rows = []
    for w in basewords:
        wl = w.lower()
        row = {"word": wl, "total": int(totals.get(wl, 0))}
        for sec in sections:
            row[sec] = int(counts[wl].get(sec, 0))
        rows.append(row)

    out_json = pathlib.Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"sections": sections, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out_csv = pathlib.Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "total", *sections])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} basewords with section counts -> {out_json} and {out_csv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
