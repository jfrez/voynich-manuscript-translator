from __future__ import annotations

import dataclasses
import re
from collections import Counter


DISCLAIMER_EN = (
    "IMPORTANT: this is NOT a real or validated translation of the Voynich Manuscript. "
    "It is a speculative/procedural model that interprets EVA using a user-defined grammar "
    "to generate experimental recipes using safe, known edible substitutes."
)


# Gramática (alineada con lo que diste + ampliada para tokens comunes en IVTFF)
COMPOUNDS = {
    "qo": "liquid base",
    "q": "general base",
    "o": "mix/transfer",
    "k": "sugars",
    "t": "heat",
    "p": "yeast fermentation",
    "ch": "main herb",
    "sh": "secondary herb",
    "f": "aroma modifier",
    "cth": "complex herbal compound",
    "ckh": "complex herbal compound",
    "cph": "complex herbal compound",
    "cfh": "complex herbal compound",
}

CONNECTORS = {"l", "r", "n", "s", "m"}

STATE_MAP = {
    "e": "active extraction",
    "i": "cooling/rest",
    "a": "fermentation start",
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
        return "long fermentation (aging)"
    if "iin" in word:
        return "medium fermentation"
    if "dy" in word:
        return "days"
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
    vowel_run: str | None
    suffix: str | None
    steps: list[str]


def interpret_word(word: str) -> WordInterpretation:
    normalized = normalize_word(word)
    tokens = longest_tokenize(word)

    compounds: list[str] = []
    connectors: list[str] = []
    for tok in tokens:
        if tok in COMPOUNDS:
            compounds.append(COMPOUNDS[tok])
        elif tok in CONNECTORS:
            connectors.append(tok)

    vowel = extract_vowel_run(normalized)
    suffix = extract_suffix(normalized)

    steps: list[str] = []
    if "liquid base" in compounds:
        steps.append("prepare liquid base")
    if "general base" in compounds and "liquid base" not in compounds:
        steps.append("prepare base (generic)")
    if "sugars" in compounds:
        steps.append("add fermentable sugars")
    if "heat" in compounds:
        steps.append("apply heat/cooking")
    if "main herb" in compounds:
        steps.append("add main plant (safe substitute)")
    if "secondary herb" in compounds:
        steps.append("add secondary herb (safe substitute)")
    if "aroma modifier" in compounds:
        steps.append("add aroma modifier")
    if "mix/transfer" in compounds:
        steps.append("mix / transfer")
    if "yeast fermentation" in compounds:
        steps.append("start fermentation (yeast)")
    if "complex herbal compound" in compounds:
        steps.append("add complex herbal compound (safe blend)")

    if vowel:
        duration = len(vowel)
        state = STATE_MAP.get(vowel[0], "unknown")
        if suffix == "days":
            steps.append(f"{duration} day(s)")
        else:
            steps.append(f"duration level {duration}")
        steps.append(f"state: {state}")

    if suffix == "long fermentation (aging)":
        steps.append("long fermentation / aging phase")
    elif suffix == "medium fermentation":
        steps.append("medium fermentation phase")

    return WordInterpretation(
        word=word,
        normalized=normalized,
        tokens=tokens,
        compounds=compounds,
        connectors=connectors,
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

    # Base doses (default 2L batch). Keep conservative.
    if batch_l <= 0:
        batch_l = 2.0
    scale = batch_l / 2.0
    water_l = float(batch_l)

    sugar_g = (100 * level) * scale
    if c.get("sugars", 0) == 0:
        # If no explicit sugars marker, keep low sugar so it stays more "infusion-like"
        sugar_g = (50 * level) * scale

    main_dry_g = (20 * level if c.get("main herb", 0) else 10 * level) * scale
    secondary_dry_g = (10 * level if c.get("secondary herb", 0) else 5 * level) * scale
    yeast_g = {1: 2, 2: 3, 3: 4}[level] if c.get("yeast fermentation", 0) else 2
    yeast_g = yeast_g * scale

    has_heat = c.get("heat", 0) > 0
    has_aroma = c.get("aroma modifier", 0) > 0
    has_complex = c.get("complex herbal compound", 0) > 0

    # Fermentation time
    norm_all = " ".join(w.normalized for w in interpreted)
    if "aiin" in norm_all:
        ferment_days = "7–14 days"
    elif "iin" in norm_all:
        ferment_days = "3–5 days"
    else:
        ferment_days = "2–4 days"

    subs = _substitutes_for_category(plant_category_guess)

    ingredients = {
        "water_l": water_l,
        "sugar_or_honey_g": int(sugar_g),
        "main_plant_substitute": subs["main"],
        "main_plant_dry_g": int(main_dry_g),
        "secondary_herb_substitute": subs["secondary"],
        "secondary_herb_dry_g": int(secondary_dry_g),
        "yeast_g": max(1, int(round(yeast_g))),
    }
    if has_aroma:
        ingredients["aroma_modifier"] = subs["aroma"]
        ingredients["aroma_modifier_dose"] = "2–5 g (or 1 strip of peel, avoiding the bitter pith)"
    if has_complex:
        ingredients["safe_complex_herbal_blend"] = "gentle spices (e.g., 1 g cinnamon + 1 g clove) or a commercial herbal tea blend"

    process: list[str] = []
    process.append("Sanitize the jar/fermenter and utensils.")
    process.append(f"Base: combine {water_l} L water with {int(sugar_g)} g sugar or honey.")
    if has_heat:
        process.append("Apply gentle heat: simmer 10–15 min, then cool to <30°C before adding yeast.")
    else:
        process.append("Infusion: use hot (not boiling) water, then let it cool before adding yeast.")
    process.append(f"Add main plant: {subs['main']} (~{int(main_dry_g)} g dried).")
    process.append(f"Add secondary herb: {subs['secondary']} (~{int(secondary_dry_g)} g dried).")
    if has_aroma:
        process.append("Add aroma modifier (optional) in a low dose.")
    if has_complex:
        process.append("If a complex herbal compound appears, use a safe commercial blend or gentle spices in micro-doses.")
    process.append(f"Pitch yeast: {ingredients['yeast_g']} g (ideally cider/beer yeast).")
    process.append(f"Ferment with an airlock: {ferment_days} (guided by iin/aiin markers).")
    process.append("Strain/rack (if very solid-heavy) and cold-crash 24 h.")
    process.append("Bottle only when activity clearly slows; refrigerate. Avoid overpressure.")

    does_make_sense = "yes"
    if plant_category_guess == "unknown":
        does_make_sense = "partial"

    risks = [
        "Never use unidentified Voynich plants directly; only use known edible substitutes.",
        "Do not consume if you see mold, smell rot, notice abnormal sliminess, or taste something clearly foul.",
        "Overpressure/bottle-bomb risk: do not bottle before stable; prefer an airlock and refrigeration.",
        "Avoid if pregnant/breastfeeding, for minors, or with medical conditions; consult a professional.",
        "No medical claims: this is an experimental beverage.",
    ]

    adjustments = [
        "If too bitter (leafy profile), halve the herbs or shorten steep/maceration time.",
        "If too sweet, extend fermentation or reduce sugar by 25–50%.",
        "For a non-alcoholic version, omit yeast and keep refrigerated as an infusion (not fermented).",
    ]

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
            "fermentation_estimate": ferment_days,
        },
        "ingredients": ingredients,
        "process": process,
        "expected_result": "A mild, aromatic herbal ferment, low-to-medium intensity depending on dose level.",
        "does_it_make_sense": does_make_sense,
        "risks": risks,
        "recommended_adjustments": adjustments,
    }
