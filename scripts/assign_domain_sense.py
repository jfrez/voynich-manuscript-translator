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


KEYWORD_DOMAINS = {
    "bath/wash": {"bath", "wash", "soak", "bathe", "wet", "rinse"},
    "heat/boil": {"boil", "hot", "heat", "warm", "simmer", "cook"},
    "oil/wax": {"oil", "oily", "wax", "grease", "ointment"},
    "plant/food": {"onion", "berry", "seed", "grain", "bread", "herb", "plant", "leaf", "root", "flower"},
    "measure/time": {"day", "days", "hour", "phase", "cycle", "repeat"},
    "astral": {"star", "moon", "sun", "planet", "zodiac", "degree"},
}


def _load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_gloss_terms(domain_readme: str) -> list[str]:
    terms: list[str] = []
    # lines like: - `word` → ... → Italian anagram `x`; English: gloss
    for line in domain_readme.splitlines():
        if "English:" not in line:
            continue
        gloss = line.split("English:", 1)[1].strip()
        if gloss in ("[n/a]", ""):
            continue
        terms.append(gloss)
    return terms


def _score_keywords(glosses: list[str]) -> dict[str, int]:
    score = Counter()
    for g in glosses:
        low = g.lower()
        tokens = set(re.findall(r"[a-z]+", low))
        for label, kws in KEYWORD_DOMAINS.items():
            score[label] += len(tokens & kws)
    return dict(score)


def _suggest_marker_sense(domain: str, keyword_scores: dict[str, int]) -> dict[str, str]:
    """
    Produce a *heuristic* per-domain sense mapping for the procedural markers.
    This does not claim decipherment; it only provides one possible "story" layer.
    """
    top = sorted(keyword_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_labels = [k for k, v in top if v > 0][:3]

    # Baseline generic meanings (no fermentation bias)
    mapping = {
        "qo": "base liquid / carrier",
        "q": "generic base marker",
        "o": "mix / transfer / continuation",
        "k": "additives / solutes (often sweeteners)",
        "t": "apply heat",
        "p": "activation / starter step (optional)",
        "ch": "main material (page-centric)",
        "sh": "secondary material",
        "f": "aroma modifier",
        "cth/ckh/cph/cfh": "complex blend / compound step",
        "e…": "active step (extraction/work)",
        "i…": "rest/cool step",
        "a…": "transition/start step",
        "dy": "explicit days marker",
        "iin": "medium phase marker",
        "aiin": "long phase marker",
    }

    # Very light domain tinting using keyword signals
    if "bath/wash" in top_labels:
        mapping["qo"] = "wash/bath liquid"
        mapping["o"] = "rinse / transfer between baths"
    if "oil/wax" in top_labels:
        mapping["qo"] = "oil/wax carrier (or mixed base)"
        mapping["t"] = "warm/melt step"
    if "astral" in top_labels:
        mapping["dy"] = "day-count / calendar marker"
        mapping["iin"] = "mid-cycle marker"
        mapping["aiin"] = "long-cycle marker"
    if "heat/boil" in top_labels:
        mapping["t"] = "boil/simmer step"

    mapping["_top_keyword_labels"] = ", ".join(top_labels) if top_labels else "none"
    return mapping


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Assign a heuristic 'sense layer' per domain from associated word glosses.")
    ap.add_argument("--domains-dir", default="data/domains", help="Input domains dir")
    ap.add_argument("--out-dir", default="data/domain_sense", help="Output dir for per-domain sense files")
    args = ap.parse_args(argv)

    domains_dir = pathlib.Path(args.domains_dir)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    index_rows = []
    for p in sorted(domains_dir.iterdir()):
        if not p.is_dir():
            continue
        readme = p / "README.md"
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8", errors="replace")
        glosses = _extract_gloss_terms(text)
        scores = _score_keywords(glosses)
        mapping = _suggest_marker_sense(p.name, scores)

        payload = {
            "domain": p.name,
            "source": "data/domains/<domain>/README.md (Associated words English glosses)",
            "note": "Heuristic 'sense layer' generated from gloss keywords; not a translation or decipherment.",
            "keyword_scores": scores,
            "marker_sense": mapping,
        }
        (out_dir / f"{p.name}.sense.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index_rows.append({"domain": p.name, "sense_file": f"{p.name}.sense.json"})

    (out_dir / "index.json").write_text(json.dumps(index_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote domain sense files -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

