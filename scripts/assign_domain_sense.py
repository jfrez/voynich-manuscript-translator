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


MARKERS = ["qo", "q", "o", "k", "t", "p", "ch", "sh", "f", "cth", "ckh", "cph", "cfh", "dy", "iin", "aiin"]


def _extract_domain_lexicon_rows(domain_readme: str) -> list[dict]:
    """
    Parse the Domain Lexicon markdown table produced by scripts/domain_word_summaries.py.

    Expected row shape:
    | `EVA` | 12 | `reduced` | `it` | gloss |
    """
    rows: list[dict] = []
    in_table = False
    for line in domain_readme.splitlines():
        if line.strip().startswith("| EVA baseword |"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) < 5:
                continue
            eva = parts[0].strip("`")
            try:
                cnt = int(parts[1])
            except Exception:
                cnt = 0
            it = parts[3].strip()
            it = it.strip("`") if it.startswith("`") else None
            gloss = parts[4].strip()
            if gloss == "[n/a]":
                gloss = ""
            rows.append({"eva": eva, "count": cnt, "it": it, "gloss": gloss})
    return rows


def _score_keywords(glosses: list[str]) -> dict[str, int]:
    score = Counter()
    for g in glosses:
        low = g.lower()
        tokens = set(re.findall(r"[a-z]+", low))
        for label, kws in KEYWORD_DOMAINS.items():
            score[label] += len(tokens & kws)
    return dict(score)


def _suggest_marker_sense_from_labels(top_labels: list[str]) -> dict[str, str]:
    """
    Produce a *heuristic* per-domain sense mapping for the procedural markers.
    This does not claim decipherment; it only provides one possible "story" layer.
    """
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
        lex_rows = _extract_domain_lexicon_rows(text)

        all_glosses = [r["gloss"] for r in lex_rows if r.get("gloss")]
        scores = _score_keywords(all_glosses)
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top_labels = [k for k, v in top if v > 0][:3]

        mapping = _suggest_marker_sense_from_labels(top_labels)

        # Marker-specific evidence from the domain lexicon: basewords that contain the marker
        marker_scores: dict[str, dict] = {}
        for mk in MARKERS:
            mk_glosses = [r["gloss"] for r in lex_rows if r.get("gloss") and mk in (r.get("eva") or "")]
            if not mk_glosses:
                continue
            mk_scores = _score_keywords(mk_glosses)
            mk_top = sorted(mk_scores.items(), key=lambda kv: kv[1], reverse=True)
            mk_labels = [k for k, v in mk_top if v > 0][:3]
            marker_scores[mk] = {
                "keyword_scores": mk_scores,
                "top_keyword_labels": mk_labels,
                "examples": [
                    {"eva": r["eva"], "it": r.get("it"), "gloss": r.get("gloss")}
                    for r in lex_rows
                    if r.get("gloss") and mk in (r.get("eva") or "")
                ][:8],
            }

        payload = {
            "domain": p.name,
            "source": "data/domains/<domain>/README.md (Domain Lexicon table: medieval-ish Italian proxy + English gloss)",
            "note": "Heuristic 'sense layer' generated from medieval-ish lexicon matches; not a translation or decipherment.",
            "keyword_scores": scores,
            "marker_sense": mapping,
            "marker_evidence": marker_scores,
        }
        (out_dir / f"{p.name}.sense.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index_rows.append({"domain": p.name, "sense_file": f"{p.name}.sense.json"})

    (out_dir / "index.json").write_text(json.dumps(index_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote domain sense files -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
