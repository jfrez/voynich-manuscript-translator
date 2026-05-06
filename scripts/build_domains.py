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


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(s: str) -> str:
    s = (s or "unknown").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "unknown"


MARKER_MEANINGS = {
    "qo": "liquid base / must / water",
    "q": "general base marker",
    "o": "mix / transfer / continuity",
    "k": "sugars / fermentables",
    "t": "heat / cooking",
    "p": "yeast / fermentation start",
    "ch": "main plant (always substituted with a safe edible plant)",
    "sh": "secondary herb (safe edible)",
    "f": "aroma modifier",
    "cth/ckh/cph/cfh": "complex herbal compound (safe blend)",
    "l/r/n/s/m": "connectors (low semantic weight transitions)",
    "e…": "active extraction",
    "i…": "cooling/rest",
    "a…": "fermentation start/transition",
    "level 1": "e / i / a",
    "level 2": "ee / ii",
    "level 3": "eee / iii",
}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Create domain (section) subfolders with indexes and per-folio pointers.")
    ap.add_argument("--pages-dir", default="data/pages", help="Input pages dir")
    ap.add_argument("--readmes-dir", default="data/recipe_readmes", help="Per-folio READMEs dir")
    ap.add_argument("--images-dir", default="data/images", help="Images dir")
    ap.add_argument("--out-dir", default="data/domains", help="Output domains dir")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    idx_path = pages_dir / "index.json"
    if not idx_path.exists():
        print("Missing data/pages/index.json. Run: python scripts/build_pages.py", file=sys.stderr)
        return 2

    index = json.loads(idx_path.read_text(encoding="utf-8"))
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Group folios by section (domain)
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for m in index:
        domain = (m.get("section") or "unknown").lower()
        by_domain[domain].append(m)

    # Precompute: per-domain compound frequencies (procedural gloss compounds)
    domain_compounds: dict[str, Counter] = {d: Counter() for d in by_domain}
    domain_word_counts: Counter = Counter()
    domain_state_class: dict[str, Counter] = {d: Counter() for d in by_domain}
    domain_level: dict[str, Counter] = {d: Counter() for d in by_domain}

    for domain, items in by_domain.items():
        for m in items:
            folio = m["folio"]
            eva_path = pages_dir / f"{folio}.eva.txt"
            if not eva_path.exists():
                continue
            text = eva_path.read_text(encoding="utf-8", errors="replace")
            words = re.findall(r"[A-Za-z]+", text)
            domain_word_counts[domain] += len(words)
            for w in words:
                iw = interpret_word(w)
                domain_compounds[domain].update(iw.compounds)
                if iw.vowel_run:
                    cls = iw.vowel_run[0]
                    domain_state_class[domain][cls] += 1
                    lvl = min(3, len(iw.vowel_run))
                    domain_level[domain][str(lvl)] += 1

    # Root domains README
    root_lines = [
        "# Domains (Generated)",
        "",
        "These folders group folios by IVTFF section (a metadata label, not a translation).",
        "Each domain folder contains an index and per-folio pointers to the canonical README + image.",
        "",
        "Domains:",
    ]

    for domain in sorted(by_domain.keys()):
        dn = safe_name(domain)
        domain_folder = out_dir / dn
        domain_folder.mkdir(parents=True, exist_ok=True)

        folios = sorted(by_domain[domain], key=lambda x: (x.get("page_number") or 10**9, x["folio"]))

        # Domain summary ("what we know")
        total_folios = len(folios)
        total_words = int(domain_word_counts.get(domain, 0))
        top_comp = domain_compounds[domain].most_common(8)
        state_counts = domain_state_class[domain]
        level_counts = domain_level[domain]

        def pct(n: int, d: int) -> str:
            return f"{(n / d * 100):.1f}%" if d else "0.0%"

        comp = domain_compounds[domain]
        marker_prevalence = {
            "qo": (comp.get("liquid base", 0), total_words),
            "q": (comp.get("general base", 0), total_words),
            "o": (comp.get("mix/transfer", 0), total_words),
            "k": (comp.get("sugars", 0), total_words),
            "t": (comp.get("heat", 0), total_words),
            "p": (comp.get("yeast fermentation", 0), total_words),
            "ch": (comp.get("main herb", 0), total_words),
            "sh": (comp.get("secondary herb", 0), total_words),
            "f": (comp.get("aroma modifier", 0), total_words),
            "cth/ckh/cph/cfh": (comp.get("complex herbal compound", 0), total_words),
            "e…": (state_counts.get("e", 0), total_words),
            "i…": (state_counts.get("i", 0), total_words),
            "a…": (state_counts.get("a", 0), total_words),
            "level 1": (level_counts.get("1", 0), total_words),
            "level 2": (level_counts.get("2", 0), total_words),
            "level 3": (level_counts.get("3", 0), total_words),
        }

        dom_lines = [
            f"# Domain: {domain}",
            "",
            "## What we know (in this repo)",
            "- This domain label comes from IVTFF page metadata (`section`).",
            "- It does not imply any semantic decipherment of the Voynich text.",
            "- READMEs in this repo show EVA transliteration + a procedural gloss (not a translation).",
            "",
            "## Summary stats",
            f"- folios: {total_folios}",
            f"- EVA word tokens (approx): {total_words}",
            f"- top procedural compounds: {top_comp}",
            "",
            "## Domain-specific marker meanings (requested; speculative)",
            "Below is the requested meaning assignment for token markers, annotated with how often the corresponding marker-class appears in this domain.",
            "This is **not** a validated translation; it is a procedural interpretation layer.",
            "",
            "### Action / ingredient markers",
            f"- `qo` = {MARKER_MEANINGS['qo']} (prevalence {pct(*marker_prevalence['qo'])})",
            f"- `q` = {MARKER_MEANINGS['q']} (prevalence {pct(*marker_prevalence['q'])})",
            f"- `o` = {MARKER_MEANINGS['o']} (prevalence {pct(*marker_prevalence['o'])})",
            f"- `k` = {MARKER_MEANINGS['k']} (prevalence {pct(*marker_prevalence['k'])})",
            f"- `t` = {MARKER_MEANINGS['t']} (prevalence {pct(*marker_prevalence['t'])})",
            f"- `p` = {MARKER_MEANINGS['p']} (prevalence {pct(*marker_prevalence['p'])})",
            f"- `ch` = {MARKER_MEANINGS['ch']} (prevalence {pct(*marker_prevalence['ch'])})",
            f"- `sh` = {MARKER_MEANINGS['sh']} (prevalence {pct(*marker_prevalence['sh'])})",
            f"- `f` = {MARKER_MEANINGS['f']} (prevalence {pct(*marker_prevalence['f'])})",
            f"- `cth/ckh/cph/cfh` = {MARKER_MEANINGS['cth/ckh/cph/cfh']} (prevalence {pct(*marker_prevalence['cth/ckh/cph/cfh'])})",
            "",
            "Connectors (low semantic weight, used as transitions):",
            f"- `l, r, n, s, m` = {MARKER_MEANINGS['l/r/n/s/m']}",
            "",
            "### State / time markers",
            "We treat the first vowel-run found in a word as an intensity/state cue:",
            f"- `e…` = {MARKER_MEANINGS['e…']} (prevalence {pct(*marker_prevalence['e…'])})",
            f"- `i…` = {MARKER_MEANINGS['i…']} (prevalence {pct(*marker_prevalence['i…'])})",
            f"- `a…` = {MARKER_MEANINGS['a…']} (prevalence {pct(*marker_prevalence['a…'])})",
            "",
            "Run length encodes level:",
            f"- level 1 = {MARKER_MEANINGS['level 1']} (prevalence {pct(*marker_prevalence['level 1'])})",
            f"- level 2 = {MARKER_MEANINGS['level 2']} (prevalence {pct(*marker_prevalence['level 2'])})",
            f"- level 3 = {MARKER_MEANINGS['level 3']} (prevalence {pct(*marker_prevalence['level 3'])})",
            "",
            "## Folios",
        ]

        for m in folios:
            folio = m["folio"]
            # Pointers (relative links)
            readme_path = pathlib.Path(args.readmes_dir) / folio / "README.md"
            image_note = ""
            if not readme_path.exists():
                image_note = " (missing README)"
            dom_lines.append(f"- {folio}: ../../recipe_readmes/{folio}/README.md{image_note}")

            # Write a small pointer file inside the domain folder
            pointer = [
                f"# {folio} ({domain})",
                "",
                f"- Canonical README: `../../recipe_readmes/{folio}/README.md`",
                f"- Page data: `../../pages/{folio}.json`",
                f"- EVA text: `../../pages/{folio}.eva.txt`",
                "",
            ]
            (domain_folder / f"{folio}.md").write_text("\n".join(pointer), encoding="utf-8")

        (domain_folder / "README.md").write_text("\n".join(dom_lines).rstrip() + "\n", encoding="utf-8")

        root_lines.append(f"- {domain}: {dn}/README.md")

    (out_dir / "README.md").write_text("\n".join(root_lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote domain folders -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
