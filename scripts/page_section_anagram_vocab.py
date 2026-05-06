#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict


def load_baseword_classification(path: pathlib.Path) -> dict[str, bool]:
    """
    Returns baseword -> generic(bool)
    """
    obj = json.loads(path.read_text(encoding="utf-8"))
    mapping = {}
    for r in obj.get("rows", []):
        bw = (r.get("baseword") or "").strip().lower()
        if not bw:
            continue
        mapping[bw] = bool(r.get("generic"))
    return mapping


def iter_page_words(page_obj: dict) -> list[str]:
    words = []
    for loc in page_obj.get("loci", []):
        eva = (loc.get("eva") or "").strip()
        if not eva:
            continue
        words.extend(w.lower() for w in re.findall(r"[A-Za-z]+", eva))
    return words


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="For each folio+section, list matched basewords split into generic vs non-generic.")
    ap.add_argument("--pages-dir", default="data/pages", help="Directory produced by scripts/build_pages.py")
    ap.add_argument(
        "--classified",
        default="data/base_words_wikwik_anagrams_unrestricted_classified.json",
        help="Classification file from scripts/classify_anagram_candidates.py",
    )
    ap.add_argument("--out-pages", default="data/page_anagram_vocab.json", help="Output JSON (per page)")
    ap.add_argument("--out-sections", default="data/section_anagram_vocab.json", help="Output JSON (per section)")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    idx_path = pages_dir / "index.json"
    if not idx_path.exists():
        print("Missing data/pages/index.json. Run: python scripts/build_pages.py", file=sys.stderr)
        return 2

    class_path = pathlib.Path(args.classified)
    if not class_path.exists():
        print("Missing classification file. Run: python scripts/classify_anagram_candidates.py", file=sys.stderr)
        return 2

    base_generic = load_baseword_classification(class_path)
    base_set = set(base_generic.keys())

    index = json.loads(idx_path.read_text(encoding="utf-8"))

    pages_out = []
    sections_out: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"generic": set(), "non_generic": set()})

    for m in index:
        folio = m["folio"]
        section = (m.get("section") or "unknown")
        page_path = pages_dir / f"{folio}.json"
        if not page_path.exists():
            continue
        page = json.loads(page_path.read_text(encoding="utf-8"))
        words = iter_page_words(page)

        g = set()
        ng = set()
        for w in words:
            if w not in base_set:
                continue
            if base_generic.get(w, True):
                g.add(w)
            else:
                ng.add(w)

        pages_out.append(
            {
                "folio": folio,
                "section": section,
                "page_number": page.get("page_number"),
                "generic": sorted(g),
                "non_generic": sorted(ng),
            }
        )

        sections_out[section]["generic"].update(g)
        sections_out[section]["non_generic"].update(ng)

    out_pages = pathlib.Path(args.out_pages)
    out_pages.parent.mkdir(parents=True, exist_ok=True)
    out_pages.write_text(json.dumps(pages_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out_sections = {}
    for sec, v in sections_out.items():
        out_sections[sec] = {"generic": sorted(v["generic"]), "non_generic": sorted(v["non_generic"])}

    out_sec_path = pathlib.Path(args.out_sections)
    out_sec_path.parent.mkdir(parents=True, exist_ok=True)
    out_sec_path.write_text(json.dumps(out_sections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote per-page vocab -> {out_pages}", file=sys.stderr)
    print(f"Wrote per-section vocab -> {out_sec_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

