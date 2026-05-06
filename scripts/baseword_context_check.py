#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.recipe_model import interpret_word  # noqa: E402


def load_pages(pages_dir: pathlib.Path) -> dict[str, dict]:
    idx = json.loads((pages_dir / "index.json").read_text(encoding="utf-8"))
    pages = {}
    for m in idx:
        folio = m["folio"]
        p = pages_dir / f"{folio}.json"
        if not p.exists():
            continue
        pages[folio] = json.loads(p.read_text(encoding="utf-8"))
    return pages


def iter_tokens_by_folio(page_obj: dict) -> list[list[str]]:
    # Return list of lines; each line is list of EVA words
    lines = []
    for loc in page_obj.get("loci", []):
        eva = (loc.get("eva") or "").strip()
        if not eva:
            continue
        words = [w.lower() for w in re.findall(r"[A-Za-z]+", eva)]
        if words:
            lines.append(words)
    return lines


def word_signature(word: str) -> dict:
    w = interpret_word(word)
    # a compact signature: compounds + vowel_run len + suffix
    return {
        "word": word,
        "compounds": w.compounds,
        "vowel_run": w.vowel_run,
        "suffix": w.suffix,
        "interpretation": " → ".join(w.steps) if w.steps else "",
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Check whether baseword candidates have consistent procedural context.")
    ap.add_argument("--pages-dir", default="data/pages", help="Input pages dir")
    ap.add_argument("--anagrams", default="data/base_words_wikwik_anagrams_relaxed.json", help="Basewords with candidate anagrams")
    ap.add_argument("--window", type=int, default=2, help="Context window size (words on each side)")
    ap.add_argument("--min-occ", type=int, default=10, help="Minimum occurrences to include in report")
    ap.add_argument("--out-json", default="data/baseword_context_report.json", help="Output JSON report")
    ap.add_argument("--out-md", default="data/baseword_context_report.md", help="Output Markdown report")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    pages = load_pages(pages_dir)

    ana_path = pathlib.Path(args.anagrams)
    ana = json.loads(ana_path.read_text(encoding="utf-8"))
    candidates = ana.get("rows", [])

    # Build a global token index per folio
    folio_meta = {}
    folio_lines = {}
    for folio, obj in pages.items():
        folio_meta[folio] = {
            "section": obj.get("section") or "unknown",
            "page_number": obj.get("page_number"),
        }
        folio_lines[folio] = iter_tokens_by_folio(obj)

    report_rows = []

    for c in candidates:
        baseword = c["baseword"]
        # collect occurrences + contexts
        occ = 0
        section_counts = Counter()
        left_coll = Counter()
        right_coll = Counter()
        compound_context = Counter()
        self_sig = word_signature(baseword)
        examples = []

        for folio, lines in folio_lines.items():
            sec = folio_meta[folio]["section"]
            for line in lines:
                for i, w in enumerate(line):
                    if w != baseword:
                        continue
                    occ += 1
                    section_counts[sec] += 1
                    # context window
                    L = line[max(0, i - args.window) : i]
                    R = line[i + 1 : i + 1 + args.window]
                    if L:
                        left_coll.update(L)
                    if R:
                        right_coll.update(R)
                    # compounds in context window + self
                    for cw in (L + [w] + R):
                        iw = interpret_word(cw)
                        compound_context.update(iw.compounds)
                    if len(examples) < 8:
                        examples.append(
                            {
                                "folio": folio,
                                "section": sec,
                                "line": " ".join(line),
                                "left": " ".join(L),
                                "right": " ".join(R),
                            }
                        )

        if occ < args.min_occ:
            continue

        # Heuristic "context coherence" score: does it show consistent action compounds?
        # We consider it more coherent if one or two compounds dominate its contexts.
        total_comp = sum(compound_context.values()) or 1
        top_comp = compound_context.most_common(3)
        dominance = (top_comp[0][1] / total_comp) if top_comp else 0.0

        report_rows.append(
            {
                "baseword": baseword,
                "total_occurrences": occ,
                "sections": dict(section_counts),
                "italianized": c.get("italianized"),
                "anagram_candidates": c.get("anagram_candidates", [])[:10],
                "self_signature": self_sig,
                "context_compounds_top": top_comp,
                "context_compound_dominance": round(dominance, 4),
                "left_collocates_top": left_coll.most_common(10),
                "right_collocates_top": right_coll.most_common(10),
                "examples": examples,
            }
        )

    # Sort by occurrences desc
    report_rows.sort(key=lambda r: (-r["total_occurrences"], r["baseword"]))

    out_json = pathlib.Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"source_anagrams": str(ana_path), "rows": report_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Markdown summary
    md_lines = [
        "# Baseword Context Check (Procedural Gloss Context)",
        "",
        "This report does NOT validate any translation. It summarizes procedural-gloss contexts for selected basewords.",
        "",
        f"Source candidates: `{ana_path}`",
        f"Window: ±{args.window} words; min occurrences: {args.min_occ}",
        "",
    ]
    for r in report_rows[:50]:
        md_lines.append(f"## `{r['baseword']}` (occ={r['total_occurrences']})")
        md_lines.append(f"- sections: {r['sections']}")
        md_lines.append(f"- italianized: `{r.get('italianized')}`")
        md_lines.append(f"- anagram candidates (top): {r.get('anagram_candidates')[:5]}")
        md_lines.append(f"- self gloss: {r['self_signature'].get('interpretation')}")
        md_lines.append(f"- context compounds top: {r['context_compounds_top']} (dominance={r['context_compound_dominance']})")
        md_lines.append(f"- left collocates: {r['left_collocates_top'][:5]}")
        md_lines.append(f"- right collocates: {r['right_collocates_top'][:5]}")
        md_lines.append("- examples:")
        for ex in r["examples"][:3]:
            md_lines.append(f"  - {ex['folio']} ({ex['section']}): `{ex['line']}`")
        md_lines.append("")

    out_md = pathlib.Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")

    print(f"Wrote context report -> {out_json} and {out_md} (rows={len(report_rows)})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

