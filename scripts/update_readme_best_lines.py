#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import sys


DOMAINS = ["herbal", "astronomical", "biological", "cosmological", "text_only", "unknown"]


def normalize_eva(word: str) -> str:
    w = word.lower()
    w = w.replace("dy", "__DY__")
    w = w.replace("d", "p")
    w = w.replace("y", "")
    w = w.replace("__DY__", "dy")
    return w


def parse_domain_lexicon(domain: str) -> dict[str, dict]:
    p = pathlib.Path("data/domains") / domain / "README.md"
    text = p.read_text(encoding="utf-8", errors="replace")
    rows = {}
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("| EVA baseword |"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            parts = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(parts) < 9:
                continue
            eva = parts[0].strip()
            if eva.startswith("`") and eva.endswith("`"):
                eva = eva.strip("`")
            cnt = int(parts[1]) if parts[1].isdigit() else 0
            it_mod, en_mod = parts[3], parts[4]
            it_med, en_med = parts[5], parts[6]
            la, en_la = parts[7], parts[8]
            rows[eva.lower()] = {
                "count": cnt,
                "it_mod": it_mod,
                "en_mod": en_mod,
                "it_med": it_med,
                "en_med": en_med,
                "la": la,
                "en_la": en_la,
            }
    return rows


def best_line_for_domain(domain: str, lex: dict[str, dict], pages_index: list[dict]) -> dict | None:
    # Search all lines in pages belonging to the domain, pick the line with max hits.
    best = None
    for m in pages_index:
        dom = (m.get("section") or "unknown").lower().replace(" ", "_")
        if dom != domain:
            continue
        folio = m["folio"]
        page = json.loads((pathlib.Path("data/pages") / f"{folio}.json").read_text(encoding="utf-8"))
        for loc in page.get("loci", []):
            eva_line = (loc.get("eva") or "").strip()
            if not eva_line:
                continue
            words = re.findall(r"[A-Za-z]+", eva_line)
            hits = []
            for w in words:
                wn = normalize_eva(w)
                # exact first
                key = wn if wn in lex else w.lower()
                if key in lex:
                    hits.append((w, key, lex[key]))
                    continue
                # substring longest
                best_bw = None
                for bw in lex.keys():
                    if len(bw) < 4:
                        continue
                    if bw in wn:
                        if best_bw is None or len(bw) > len(best_bw):
                            best_bw = bw
                if best_bw:
                    hits.append((w, best_bw, lex[best_bw]))
            # score: count only hits with any English gloss available
            scored_hits = []
            for w, bw, info in hits:
                if any(info.get(k) and info.get(k) != "[n/a]" for k in ("en_mod", "en_med", "en_la")):
                    scored_hits.append((w, bw, info))
            score = len(scored_hits)
            if score <= 0:
                continue
            cand = {
                "score": score,
                "folio": folio,
                "locus": loc.get("locus"),
                "eva_line": eva_line,
                "hits": scored_hits[:12],
            }
            if best is None or cand["score"] > best["score"] or (cand["score"] == best["score"] and len(cand["eva_line"]) > len(best["eva_line"])):
                best = cand
    return best


def format_hit(w: str, bw: str, info: dict) -> str:
    def cell(x: str | None) -> str:
        if not x or x == "[n/a]":
            return "[n/a]"
        return x

    return (
        f"- `{w}` (→ `{bw}`): "
        f"it(mod) {cell(info.get('it_mod'))} / {cell(info.get('en_mod'))}; "
        f"it(med) {cell(info.get('it_med'))} / {cell(info.get('en_med'))}; "
        f"la {cell(info.get('la'))} / {cell(info.get('en_la'))}"
    )


def build_block() -> str:
    pages_index = json.loads((pathlib.Path("data/pages") / "index.json").read_text(encoding="utf-8"))
    lines = []
    lines.append("## Best full-line lexicon glosses (by domain)")
    lines.append("")
    lines.append(
        "For each IVTFF domain, this selects one complete manuscript line with the most lexicon hits (modern Italian list + WikWik “medieval-ish” proxy + Whitaker Latin). Still not a translation."
    )
    lines.append("")

    for dom in DOMAINS:
        lex = parse_domain_lexicon(dom)
        best = best_line_for_domain(dom, lex, pages_index)
        if not best:
            continue
        # Load the generated per-line parsing (structural gloss) for this locus
        english_gloss = None
        try:
            rj = json.loads((pathlib.Path("data/recipes") / f"{best['folio']}.recipe.json").read_text(encoding="utf-8"))
            for lr in rj.get("line_recipes", []):
                if lr.get("locus") == best["locus"]:
                    parsing = (lr.get("recipe") or {}).get("parsing", [])
                    if parsing:
                        english_gloss = "; ".join(f"{p.get('word')}: {p.get('interpretation')}" for p in parsing[:20])
                    break
        except Exception:
            english_gloss = None
        lines.append(f"### {dom}")
        lines.append(f"- Source: `{best['folio']}` / `{best['locus']}` → `data/recipe_readmes/{dom}/{best['folio']}/README.md`")
        lines.append("- EVA line:")
        lines.append("```text")
        lines.append(best["eva_line"])
        lines.append("```")
        if english_gloss:
            lines.append("- English structural gloss (generated):")
            lines.append("```text")
            lines.append(english_gloss)
            lines.append("```")
        lines.append("- Lexicon hits (inherited context):")
        for w, bw, info in best["hits"]:
            lines.append(format_hit(w, bw, info))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    readme = pathlib.Path("README.md")
    txt = readme.read_text(encoding="utf-8")
    block = build_block()

    # Replace the old block starting at "## Best full-line lexicon glosses" up to "## Top candidate basewords..."
    m = re.search(r"^## Best full-line lexicon glosses \(by domain\)\s*$", txt, flags=re.M)
    if not m:
        raise SystemExit("Could not find start marker (## Best full-line lexicon glosses ...) in README.md")
    start_idx = m.start()
    m2 = re.search(r"^## Top candidate basewords by domain \(first 20\)\s*$", txt[m.end() :], flags=re.M)
    if not m2:
        raise SystemExit("Could not find end marker (## Top candidate basewords...) in README.md")
    end_idx = m.end() + m2.start()

    new_txt = txt[:start_idx].rstrip() + "\n\n" + block + "\n" + txt[end_idx:].lstrip()
    readme.write_text(new_txt, encoding="utf-8")
    print("Updated README.md full-line examples block.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
