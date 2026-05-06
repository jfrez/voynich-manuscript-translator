from __future__ import annotations

import dataclasses
import re
from collections import Counter


DISCLAIMER_EN = (
    "IMPORTANT: this is NOT a real or validated translation of the Voynich Manuscript. "
    "It is a speculative/procedural model that interprets EVA using a user-defined grammar "
    "to generate experimental recipes using safe, known edible substitutes."
)


# Grammar: tokenization + structural gloss only (no semantic translation claims).
COMPOUNDS = {
    # These are treated as structural markers, not words with validated meaning.
    "qo": "qo",
    "q": "q",
    "o": "o",
    "k": "k",
    "t": "t",
    "p": "p",
    "ch": "ch",
    "sh": "sh",
    "f": "f",
    "cth": "cth",
    "ckh": "ckh",
    "cph": "cph",
    "cfh": "cfh",
}

CONNECTORS = {"l", "r", "n", "s", "m"}
STATE_TOKENS = {"e", "ee", "eee", "i", "ii", "iii", "a"}
SUFFIX_TOKENS = {"dy", "iin", "aiin"}
# Extra single-letter tokens observed in IVTFF that we deliberately treat as
# "filler" (no meaning assigned) so coverage can be audited without inventing semantics.
FILLER_TOKENS = {"v", "x", "c", "g", "j"}

STATE_MAP = {
    # Structural state classes (labels only)
    "e": "class e",
    "i": "class i",
    "a": "class a",
}


def normalize_word(word: str) -> str:
    """
    Normalizaciones del usuario:
    - d -> p
    - y -> vacío, salvo cuando forma dy
    - ktp -> k + t + p (para tokenizar mejor)
    """
    w = word.lower()
    w = w.replace("ktp", "ktp")  # keep string; tokenizer will split
    w = w.replace("d", "p")
    # remove 'y' except when part of 'dy'
    w = re.sub(r"y(?!$)", "y", w)  # no-op placeholder for readability
    w = re.sub(r"y(?!y)", "y", w)  # no-op
    # actual: remove all y not followed by 'y'? too broad; implement rule: keep only in 'dy'
    w = re.sub(r"y", "", w.replace("dy", "__DY__"))
    w = w.replace("__DY__", "dy")
    return w


def extract_vowel_run(word: str) -> str | None:
    # first occurrence of e+ / i+ / a+ in the word
    m = re.findall(r"(e+|i+|a+)", word)
    return m[0] if m else None


def extract_suffix(word: str) -> str | None:
    if "aiin" in word:
        return "aiin"
    if "iin" in word:
        return "iin"
    if "dy" in word:
        return "dy"
    return None


def longest_tokenize(word: str) -> list[str]:
    """
    Tokenización greedy para compuestos + conectores + sufijos frecuentes en EVA/IVTFF.
    """
    w = normalize_word(word)
    keys = sorted(
        list(COMPOUNDS.keys())
        + list(CONNECTORS)
        + ["aiin", "iin", "dy", "eee", "ee", "iii", "ii", "e", "i", "a", "ktp"],
        key=len,
        reverse=True,
    )
    out: list[str] = []
    i = 0
    while i < len(w):
        matched = None
        for k in keys:
            if w.startswith(k, i):
                matched = k
                break
        if matched:
            out.append(matched)
            i += len(matched)
        else:
            out.append(w[i])
            i += 1
    # expand ktp into k,t,p for the compound extraction logic
    expanded: list[str] = []
    for t in out:
        if t == "ktp":
            expanded.extend(["k", "t", "p"])
        else:
            expanded.append(t)
    return expanded


@dataclasses.dataclass(frozen=True)
class WordInterpretation:
    word: str
    normalized: str
    tokens: list[str]
    compounds: list[str]
    connectors: list[str]
    unknown_tokens: list[str]
    vowel_run: str | None
    suffix: str | None
    steps: list[str]


def interpret_word(word: str) -> WordInterpretation:
    normalized = normalize_word(word)
    tokens = longest_tokenize(word)

    compounds: list[str] = []
    connectors: list[str] = []
    unknown_tokens: list[str] = []
    for tok in tokens:
        if tok in COMPOUNDS:
            compounds.append(COMPOUNDS[tok])
        elif tok in CONNECTORS:
            connectors.append(tok)
        elif tok in STATE_TOKENS or tok in SUFFIX_TOKENS:
            # Explicitly modeled elsewhere (vowel-run + suffix extraction)
            continue
        elif tok in FILLER_TOKENS:
            # Intentionally ignored (no semantics claimed)
            continue
        else:
            # Preserve any leftover single-letter/glyph tokens so we can audit coverage
            unknown_tokens.append(tok)

    vowel = extract_vowel_run(normalized)
    suffix = extract_suffix(normalized)

    # Structural gloss only: show decomposition + state/suffix flags.
    steps: list[str] = []
    if tokens:
        steps.append("tokens: " + " ".join(tokens))
    if connectors:
        steps.append("connectors: " + " ".join(connectors))
    if vowel:
        duration = len(vowel)
        state = STATE_MAP.get(vowel[0], "unknown")
        steps.append(f"vowel_run: {vowel} (level {duration}; {state})")
    if suffix:
        steps.append(f"suffix: {suffix}")
    if unknown_tokens:
        uniq = []
        for t in unknown_tokens:
            if t not in uniq:
                uniq.append(t)
        steps.append("unmodeled_tokens: " + " ".join(uniq[:12]))

    return WordInterpretation(
        word=word,
        normalized=normalized,
        tokens=tokens,
        compounds=compounds,
        connectors=connectors,
        unknown_tokens=unknown_tokens,
        vowel_run=vowel,
        suffix=suffix,
        steps=steps,
    )


def interpret_text(eva_text: str) -> list[WordInterpretation]:
    words = re.findall(r"[a-zA-Z]+", eva_text)
    return [interpret_word(w) for w in words]


def _dose_level(interpreted: list[WordInterpretation]) -> int:
    # Use the maximum vowel-run length seen (e/ee/eee etc.), fallback to 1
    max_run = 1
    for w in interpreted:
        if w.vowel_run:
            max_run = max(max_run, len(w.vowel_run))
    return min(max_run, 3)


def _substitutes_for_category(category: str) -> dict[str, str]:
    # Always safe, edible, common substitutes. No use of unknown Voynich plants.
    cat = (category or "unknown").lower()
    if cat == "root":
        return {"main": "ginger (dry or fresh)", "secondary": "food-grade lemon peel", "aroma": "cardamom (optional)"}
    if cat == "flower":
        return {"main": "chamomile", "secondary": "lemon balm", "aroma": "orange peel (optional)"}
    if cat == "leaf":
        return {"main": "lemon balm", "secondary": "mint", "aroma": "lemon peel (optional)"}
    if cat == "aquatic":
        return {"main": "hibiscus (dried)", "secondary": "mint", "aroma": "cucumber (optional)"}
    return {"main": "chamomile (safe default substitute)", "secondary": "mint", "aroma": "lemon peel (optional)"}


def generate_recipe(eva_text: str, plant_category_guess: str = "unknown", batch_l: float = 2.0) -> dict:
    interpreted = interpret_text(eva_text)

    compounds_all = [c for w in interpreted for c in w.compounds]
    c = Counter(compounds_all)
    level = _dose_level(interpreted)

    # Phase/intensity summary (structural only)
    norm_all = " ".join(w.normalized for w in interpreted)
    phase = None
    duration_est = None
    if "aiin" in norm_all:
        phase = "aiin"
        duration_est = "7–14 days (heuristic long phase)"
    elif "iin" in norm_all:
        phase = "iin"
        duration_est = "3–5 days (heuristic medium phase)"
    elif "dy" in norm_all:
        phase = "dy"
        # If dy appears anywhere, interpret the max vowel-run level as an explicit day-count cue.
        duration_est = f"{level} day(s) (from max vowel-run level + dy)"

    return {
        "disclaimer": DISCLAIMER_EN,
        "plant_category_guess": plant_category_guess,
        "parsing": [
            {
                "word": w.word,
                "normalized": w.normalized,
                "tokens": w.tokens,
                "compounds": w.compounds,
                "connectors": w.connectors,
                "vowel_run": w.vowel_run,
                "suffix": w.suffix,
                "interpretation": " → ".join(w.steps) if w.steps else "[unparsed]",
            }
            for w in interpreted
        ],
        "procedural_summary": {
            "compound_counts": dict(Counter(compounds_all)),
            "dose_level": level,
            "phase_marker": phase,
            "duration_estimate": duration_est,
        },
        "ingredients": {},
        "process": [],
        "expected_result": None,
        "does_it_make_sense": None,
        "risks": [],
        "recommended_adjustments": [],
    }
