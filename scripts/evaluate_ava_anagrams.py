#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import sys
from collections import Counter, defaultdict


def strip_accents(w: str) -> str:
    return (
        w.replace("à", "a")
        .replace("è", "e")
        .replace("é", "e")
        .replace("ì", "i")
        .replace("ò", "o")
        .replace("ù", "u")
    )


def load_wordlist(paths: list[pathlib.Path]) -> list[str]:
    out: list[str] = []
    for p in paths:
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            w = strip_accents(ln.strip().lower())
            if not w:
                continue
            if re.fullmatch(r"[a-z]+", w):
                out.append(w)
    # dedup
    return sorted(set(out))


def sig(s: str, equiv_ou: bool) -> str:
    if equiv_ou:
        s = s.replace("u", "o")
    return "".join(sorted(s))


def eva_tokenize(word: str) -> list[str]:
    # Minimal tokenization for this experiment:
    # treat 'ain' as one unit; otherwise single chars.
    w = word.lower()
    toks = []
    i = 0
    while i < len(w):
        if w.startswith("ain", i):
            toks.append("ain")
            i += 3
        else:
            toks.append(w[i])
            i += 1
    return toks


def eva_to_ava_minimal(word: str) -> str:
    """
    Minimal rules as per the Reddit claim:
      - EVA 'k' is a ligature => AVA 'tl'
      - EVA 'ain' strokes => AVA 'm'
      - keep other letters as-is (lowercased)
    This is NOT validated and is used only for evaluation.
    """
    out = []
    for t in eva_tokenize(word):
        if t == "k":
            out.append("tl")
        elif t == "ain":
            out.append("m")
        else:
            out.append(t)
    s = "".join(out)
    s = re.sub(r"[^a-z]", "", s)
    return s


def random_mapping_from_vocab(vocab: list[str], rng: random.Random) -> dict[str, str]:
    """
    Build a random token mapping for baseline comparisons.
    Tokens include single letters plus 'ain' treated as a unit.
    Map each token to a random single letter, except 'k' which maps to a random digraph.
    """
    letters = list("abcdefghijklmnopqrstuvwxyz")
    tokens = sorted(set(vocab))
    mapping: dict[str, str] = {}
    for t in tokens:
        if t == "k":
            mapping[t] = rng.choice(letters) + rng.choice(letters)
        elif t == "ain":
            mapping[t] = rng.choice(letters)
        else:
            mapping[t] = rng.choice(letters)
    return mapping


def apply_mapping(word: str, mapping: dict[str, str]) -> str:
    out = []
    for t in eva_tokenize(word):
        out.append(mapping.get(t, t))
    s = "".join(out)
    s = re.sub(r"[^a-z]", "", s)
    return s


def build_sig_index(words: list[str], equiv_ou: bool) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for w in words:
        idx[sig(w, equiv_ou)].append(w)
    return idx


def extract_eva_words_for_folio(pages_dir: pathlib.Path, folio: str) -> list[dict]:
    page_json = pages_dir / f"{folio}.json"
    obj = json.loads(page_json.read_text(encoding="utf-8"))
    loci = obj.get("loci", [])
    words_out = []
    for loc in loci:
        eva_line = (loc.get("eva") or "").strip()
        if not eva_line:
            continue
        words = re.findall(r"[A-Za-z]+", eva_line)
        words_out.append({"locus": loc.get("locus"), "words": [w.lower() for w in words]})
    return words_out


def score_folio_line_words(
    line_words: list[dict],
    sig_index: dict[str, list[str]],
    transform_fn,
    equiv_ou: bool,
    baseword_filter: set[str] | None = None,
) -> dict:
    total = 0
    matched = 0
    matches = []
    token_counter = Counter()
    for line in line_words:
        locus = line["locus"]
        for w in line["words"]:
            if baseword_filter is not None and w not in baseword_filter:
                continue
            total += 1
            token_counter.update(eva_tokenize(w))
            t = transform_fn(w)
            if not t:
                continue
            s = sig(t, equiv_ou)
            cands = sig_index.get(s, [])
            if cands:
                matched += 1
                matches.append({"locus": locus, "eva": w, "mapped": t, "candidates": cands[:10]})
    return {
        "total_words": total,
        "matched_words": matched,
        "match_rate": (matched / total) if total else 0.0,
        "token_vocab": sorted(token_counter.keys()),
        "matches": matches,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Evaluate a claimed EVA->AVA mapping via Italian anagram matching + baseline permutations.")
    ap.add_argument("--folio", default="f99r", help="Folio to evaluate (e.g., f99r)")
    ap.add_argument("--pages-dir", default="data/pages", help="Pages directory")
    ap.add_argument("--wordlist", action="append", default=["data/lexicon/italian_words.txt"], help="Italian wordlist path(s)")
    ap.add_argument("--equiv-ou", action="store_true", help="Treat o and u as equivalent for anagram signature")
    ap.add_argument("--permutations", type=int, default=200, help="Number of random-mapping baselines")
    ap.add_argument("--seed", type=int, default=1, help="RNG seed")
    ap.add_argument("--basewords", default="data/base_words.txt", help="If set, evaluate only words present in this baseword list")
    ap.add_argument("--out", default="data/ava_eval_f99r.json", help="Output JSON report path")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    wl_paths = [pathlib.Path(p) for p in args.wordlist]
    for p in wl_paths:
        if not p.exists():
            print(f"Missing wordlist: {p}", file=sys.stderr)
            return 2

    it_words = load_wordlist(wl_paths)
    sig_index = build_sig_index(it_words, equiv_ou=args.equiv_ou)

    line_words = extract_eva_words_for_folio(pages_dir, args.folio)
    base_set = None
    if args.basewords:
        bp = pathlib.Path(args.basewords)
        if bp.exists():
            base_set = {ln.strip().lower() for ln in bp.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()}
        else:
            print(f"Baseword file not found: {bp} (continuing without filter)", file=sys.stderr)

    # Claimed mapping score
    claimed = score_folio_line_words(
        line_words=line_words,
        sig_index=sig_index,
        transform_fn=eva_to_ava_minimal,
        equiv_ou=args.equiv_ou,
        baseword_filter=base_set,
    )

    # Baseline: random token mappings
    rng = random.Random(args.seed)
    vocab = claimed["token_vocab"]
    baseline_rates = []
    for _ in range(args.permutations):
        mapping = random_mapping_from_vocab(vocab, rng)
        res = score_folio_line_words(
            line_words=line_words,
            sig_index=sig_index,
            transform_fn=lambda w, m=mapping: apply_mapping(w, m),
            equiv_ou=args.equiv_ou,
            baseword_filter=base_set,
        )
        baseline_rates.append(res["match_rate"])

    # p-value: fraction of baselines >= claimed
    claimed_rate = claimed["match_rate"]
    ge = sum(1 for r in baseline_rates if r >= claimed_rate)
    p = (ge + 1) / (len(baseline_rates) + 1)

    report = {
        "folio": args.folio,
        "equiv_ou": args.equiv_ou,
        "wordlists": [str(p) for p in wl_paths],
        "basewords_filter": str(args.basewords) if base_set is not None else None,
        "italian_word_count": len(it_words),
        "claimed_mapping": {
            "description": "Minimal EVA->AVA rules: k->tl, ain->m, others identity; then anagram match against Italian wordlist.",
            **{k: claimed[k] for k in ("total_words", "matched_words", "match_rate")},
        },
        "baseline_random_mapping": {
            "permutations": args.permutations,
            "seed": args.seed,
            "mean_match_rate": sum(baseline_rates) / len(baseline_rates) if baseline_rates else 0.0,
            "p_value_ge_claimed": p,
        },
        "sample_matches": claimed["matches"][:50],
    }

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote report -> {out}", file=sys.stderr)
    print(f"Claimed match rate: {claimed_rate:.3%} ({claimed['matched_words']}/{claimed['total_words']}); baseline p≈{p:.4f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
