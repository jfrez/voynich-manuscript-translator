#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter


UA = "voynich-recipe-research-bot/0.1"
WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"


def italianize_eva(word: str) -> str:
    # Same heuristic used in scripts/italianized_anagrams.py
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


def wiktionary_english_gloss(term: str) -> str | None:
    """
    Best-effort: fetch wikitext for a term and extract the first Italian definition line.
    Returns a short plain-text gloss, or None.
    """
    params = {"action": "parse", "page": term, "prop": "wikitext", "format": "json"}
    url = WIKTIONARY_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

    wt = data.get("parse", {}).get("wikitext", {}).get("*", "")
    if not wt:
        return None

    # Narrow to Italian section if present.
    if "==Italian==" in wt:
        wt = wt.split("==Italian==", 1)[1]
    # Stop at next language header.
    wt = re.split(r"\n==[^=]", wt, maxsplit=1)[0]

    for line in wt.splitlines():
        line = line.strip()
        if not line.startswith("#"):
            continue
        gloss = line.lstrip("#").strip()
        # drop templates
        gloss = re.sub(r"\{\{[^}]+\}\}", "", gloss)
        # wiki links [[a|b]] -> b ; [[a]] -> a
        gloss = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", gloss)
        gloss = re.sub(r"\[\[([^\]]+)\]\]", r"\1", gloss)
        # italics markup
        gloss = gloss.replace("''", "")
        gloss = re.sub(r"\s+", " ", gloss).strip(" -–—")
        if not gloss or gloss in {"*", ":"}:
            continue
        return (gloss[:160] + "…") if len(gloss) > 160 else gloss
    return None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Add per-domain word summaries (reduced form + Italian anagram + English gloss).")
    ap.add_argument("--domains-dir", default="data/domains", help="Domains directory created by scripts/build_domains.py")
    ap.add_argument("--section-vocab", default="data/section_anagram_vocab.json", help="Per-section vocab sets")
    ap.add_argument("--anagrams", default="data/base_words_wikwik_anagrams_unrestricted.json", help="Anagram candidates (WikWik-based)")
    ap.add_argument("--baseword-counts", default="data/base_words_by_section.json", help="Counts by section")
    ap.add_argument("--top", type=int, default=30, help="How many non-generic words per domain to include")
    ap.add_argument("--no-wiktionary", action="store_true", help="Skip English gloss lookups (offline mode)")
    ap.add_argument("--wiktionary-cache", default="data/lexicon/wiktionary_en_cache.json", help="Cache file for Wiktionary gloss lookups")
    args = ap.parse_args(argv)

    domains_dir = pathlib.Path(args.domains_dir)
    section_vocab = json.loads(pathlib.Path(args.section_vocab).read_text(encoding="utf-8"))
    anagrams = json.loads(pathlib.Path(args.anagrams).read_text(encoding="utf-8"))
    base_counts = json.loads(pathlib.Path(args.baseword_counts).read_text(encoding="utf-8"))
    cache_path = pathlib.Path(args.wiktionary_cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        gloss_cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    except Exception:
        gloss_cache = {}

    # baseword -> candidates
    ana_map = {r["baseword"]: r for r in anagrams.get("rows", [])}
    # baseword -> per-section counts
    count_map = {r["word"]: r for r in base_counts.get("rows", [])}
    sections = base_counts.get("sections", [])

    for domain in [p.name for p in domains_dir.iterdir() if p.is_dir()]:
        # domain folder name matches section normalization in build_domains.py, but section_vocab keys are raw (e.g. "text only")
        # try to map back
        raw_section = domain.replace("_", " ")
        if raw_section not in section_vocab:
            # try exact
            if domain in section_vocab:
                raw_section = domain
            else:
                continue

        non_generic = section_vocab[raw_section]["non_generic"]
        # rank by total occurrences in this section
        scored = []
        for w in non_generic:
            row = count_map.get(w)
            if not row:
                continue
            scored.append((int(row.get(raw_section, 0)), int(row.get("total", 0)), w))
        scored.sort(reverse=True)
        selected = [w for _sec_count, _total, w in scored[: args.top]]

        lines = []
        lines.append("## Associated words (non-generic; heuristic)")
        lines.append(
            "These are non-generic basewords observed in this domain, with a reduced form and best-effort anagram candidates from a Wiktionary-derived Italian lexicon (WikWik)."
        )
        lines.append("This is not a translation; matches are heuristic and may be coincidental.")
        lines.append("English glosses are best-effort summaries from English Wiktionary extracts and may be missing/wrong.")
        lines.append("")
        for w in selected:
            reduced = italianize_eva(w)
            cand = ana_map.get(w, {}).get("anagram_candidates", [])[:5]
            it = cand[0] if cand else None
            en = None
            if not args.no_wiktionary and it:
                cached = gloss_cache.get(it) if it in gloss_cache else None
                if cached not in (None, "*", ":"):
                    en = cached
                else:
                    en = wiktionary_english_gloss(it)
                    gloss_cache[it] = en
            lines.append(f"- `{w}` → reduced `{reduced}` → Italian anagram `{it}`; English: {en or '[n/a]'}")
        lines.append("")

        readme = domains_dir / domain / "README.md"
        if not readme.exists():
            continue
        base = readme.read_text(encoding="utf-8")
        # Replace existing block if present
        marker = "## Associated words (non-generic; heuristic)"
        if marker in base:
            base = base.split(marker, 1)[0].rstrip() + "\n"
        insert_marker = "## Folios"
        if insert_marker in base:
            pre, post = base.split(insert_marker, 1)
            out = pre.rstrip() + "\n\n" + "\n".join(lines).rstrip() + "\n\n" + insert_marker + post
        else:
            out = base.rstrip() + "\n\n" + "\n".join(lines).rstrip() + "\n"
        readme.write_text(out, encoding="utf-8")

    if not args.no_wiktionary:
        try:
            cache_path.write_text(json.dumps(gloss_cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception:
            pass

    print("Updated domain READMEs with associated word summaries.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
