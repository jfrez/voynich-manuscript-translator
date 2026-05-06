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
    ap.add_argument("--latin-anagrams", default="data/base_words_latin_anagrams_whitaker.json", help="Latin anagram candidates (Whitaker WORDS-based)")
    ap.add_argument("--latin-gloss", default="data/lexicon/latin_whitaker_gloss.json", help="Latin lemma -> English gloss (Whitaker WORDS-based)")
    ap.add_argument("--modern-italian-anagrams", default="data/base_words_modern_italian_anagrams.json", help="Modern Italian anagram candidates (wordlist-based)")
    ap.add_argument("--baseword-counts", default="data/base_words_by_section.json", help="Counts by section")
    ap.add_argument("--top", type=int, default=30, help="How many non-generic words per domain to include")
    ap.add_argument("--no-wiktionary", action="store_true", help="Skip English gloss lookups (offline mode)")
    ap.add_argument("--wiktionary-cache", default="data/lexicon/wiktionary_en_cache.json", help="Cache file for Wiktionary gloss lookups")
    args = ap.parse_args(argv)

    domains_dir = pathlib.Path(args.domains_dir)
    section_vocab = json.loads(pathlib.Path(args.section_vocab).read_text(encoding="utf-8"))
    anagrams = json.loads(pathlib.Path(args.anagrams).read_text(encoding="utf-8"))
    latin_anagrams = json.loads(pathlib.Path(args.latin_anagrams).read_text(encoding="utf-8")) if pathlib.Path(args.latin_anagrams).exists() else {}
    modern_it = json.loads(pathlib.Path(args.modern_italian_anagrams).read_text(encoding="utf-8")) if pathlib.Path(args.modern_italian_anagrams).exists() else {}
    latin_gloss = json.loads(pathlib.Path(args.latin_gloss).read_text(encoding="utf-8")) if pathlib.Path(args.latin_gloss).exists() else {}
    base_counts = json.loads(pathlib.Path(args.baseword_counts).read_text(encoding="utf-8"))
    cache_path = pathlib.Path(args.wiktionary_cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        gloss_cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    except Exception:
        gloss_cache = {}

    # baseword -> candidates
    ana_map = {r["baseword"]: r for r in anagrams.get("rows", [])}
    lat_map = {r.get("baseword"): r for r in (latin_anagrams.get("rows", []) or []) if isinstance(r, dict)}
    modern_map = {r.get("baseword"): r for r in (modern_it.get("rows", []) or []) if isinstance(r, dict)}
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
        lines.append("## Domain Lexicon (Medieval-ish Italian proxy; heuristic)")
        lines.append(
            "This section defines **domain-associated basewords** using a pragmatic proxy: anagram candidates from a large Wiktionary-derived Italian wordlist (WikWik)."
        )
        lines.append("This is not a translation; matches are heuristic and may be coincidental.")
        lines.append("English glosses are best-effort summaries extracted from English Wiktionary wikitext and may be missing/wrong.")
        lines.append("")
        lines.append("| EVA baseword | Count (domain) | Reduced form | Italian (modern list) | English (it) | Italian (WikWik/medieval-ish) | English (it) | Latin (Whitaker) | English (la) |")
        lines.append("|---|---:|---|---|---|---|---|---|---|")
        for w in selected:
            reduced = italianize_eva(w)
            # modern Italian
            mod_cands = (modern_map.get(w, {}).get("anagram_candidates", []) or [])[:5]
            it_mod = mod_cands[0] if mod_cands else None
            # medieval-ish Italian proxy (WikWik)
            med_cands = (ana_map.get(w, {}).get("anagram_candidates", []) or [])[:5]
            it_med = med_cands[0] if med_cands else None
            # Latin
            lat_cands = (lat_map.get(w, {}).get("latin_candidates") or [])[:3]
            lat = lat_cands[0] if lat_cands else None
            en_mod = None
            if not args.no_wiktionary and it_mod:
                cached = gloss_cache.get(it_mod) if it_mod in gloss_cache else None
                if cached not in (None, "*", ":"):
                    en_mod = cached
                else:
                    en_mod = wiktionary_english_gloss(it_mod)
                    gloss_cache[it_mod] = en_mod

            en_med = None
            if not args.no_wiktionary and it_med:
                cached = gloss_cache.get(it_med) if it_med in gloss_cache else None
                if cached not in (None, "*", ":"):
                    en_med = cached
                else:
                    en_med = wiktionary_english_gloss(it_med)
                    gloss_cache[it_med] = en_med

            en_lat = latin_gloss.get(lat) if lat else None
            cnt = 0
            row = count_map.get(w)
            if row:
                cnt = int(row.get(raw_section, 0) or 0)
            it_mod_cell = f"`{it_mod}`" if it_mod else "[n/a]"
            en_mod_cell = (en_mod or "[n/a]").replace("\n", " ").replace("|", "\\|")
            it_med_cell = f"`{it_med}`" if it_med else "[n/a]"
            en_med_cell = (en_med or "[n/a]").replace("\n", " ").replace("|", "\\|")
            lat_cell = f"`{lat}`" if lat else "[n/a]"
            en_lat_cell = (en_lat or "[n/a]").replace("\n", " ").replace("|", "\\|")
            lines.append(
                f"| `{w}` | {cnt} | `{reduced}` | {it_mod_cell} | {en_mod_cell} | {it_med_cell} | {en_med_cell} | {lat_cell} | {en_lat_cell} |"
            )
        lines.append("")

        readme = domains_dir / domain / "README.md"
        if not readme.exists():
            continue
        base = readme.read_text(encoding="utf-8")
        # Replace existing block if present
        marker = "## Domain Lexicon (Medieval-ish Italian proxy; heuristic)"
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
