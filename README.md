# voynich (per-folio data)

Tools to download an IVTFF (EVA) transliteration and split it by folio/page.

Important: this is **transliteration**, not translation. Any downstream interpretation (e.g., “recipes”) is **speculative/procedural**.

## 1. Introduction

The Voynich Manuscript (15th century) remains one of the most persistent open problems in the study of languages and writing systems. Its content combines botanical illustrations, diagrams, and an undeciphered text system whose nature—language, cipher, or artificial construct—remains unknown. Despite many attempts, there is no consensus about its meaning or the correct method to approach it.

To enable computational analysis, many researchers use EVA (Extensible/European Voynich Alphabet), a transliteration scheme that maps manuscript glyphs to Latin characters. This transliteration is **not a translation**; it is a consistent representation that allows the text to be studied with computational tools. The EVA corpus exhibits notable properties such as frequent pattern repetition, small variations between words, and statistical distributions that sometimes resemble natural language.

This repository does **not** attempt semantic decipherment. Instead, it explores an alternative approach: treating EVA as a **procedural system**. Concretely, the hypothesis is that recurring sequences can be modeled as structured instructions—analogous to recipes or technical protocols. This turns unknown text into an interpretable (and in our case, executable) symbolic workflow while staying aligned with observed string-level patterns.

## What is EVA (in this repo)?

EVA (“European Voynich Alphabet”) is a **symbol-to-ASCII transliteration convention** used to represent Voynich glyphs with Latin letters so the text can be processed by computers. In other words:

- EVA here is treated as **input tokens** (strings) extracted from IVTFF/EVA files.
- EVA is **not** assumed to encode a known language, and we do **not** claim any validated meaning.
- This project uses EVA **procedurally**: we map recurring letter patterns to actions/states in a hypothetical fermentation workflow.

## 2. Proposed Grammar and Corpus Coverage (speculative)

The grammar below is a **user-defined symbolic model** (not Voynich scholarship). It converts EVA words into:

- ingredient/action markers
- intensity/state markers
- time/phase suffixes

### 2.1 CFG (high-level)

We describe the shape of many EVA words with a compact context-free grammar (CFG):

```
S     → W | W S

W     → CORE | CORE C W

CORE  → P BLOCK T
      | P BLOCK
      | BLOCK T
      | BLOCK

P     → qo | q | o

BLOCK → UNIT | UNIT BLOCK

UNIT  → M | B | G | V

M     → k | t | p | f
B     → ch | sh
G     → cth | ckh | cph | cfh

V     → e | ee | eee
      | i | ii | iii
      | a | ai | aiin

T     → dy | iin | aiin | ε

C     → l | r | n | s | m
```

In this formulation, prefixes (`P`) represent recurring base components, `BLOCK` introduces variability via combinations of `UNIT`s, suffixes (`T`) mark phase/closing conditions, and connectors (`C`) allow internal extensions that capture common EVA complexities.

### Normalizations

- `d → p`
- `y → (removed)`, except when it forms `dy`
- `ktp → k + t + p` (tokenized as three markers)

### Action / ingredient markers

- `qo` = liquid base / must / water
- `q` = general base marker
- `o` = mix / transfer / continuity
- `k` = sugars / fermentables
- `t` = heat / cooking
- `p` = yeast / fermentation start
- `ch` = main plant (always substituted with a safe edible plant)
- `sh` = secondary herb (safe edible)
- `f` = aroma modifier
- `cth`, `ckh`, `cph`, `cfh` = complex herbal compound (safe blend)

Connectors (low semantic weight, used as transitions):

- `l, r, n, s, m`

### State / time markers

We treat the first vowel-run found in a word as an intensity/state cue:

- `e…` = active extraction
- `i…` = cooling/rest
- `a…` = fermentation start/transition

Run length encodes level:

- `e` / `i` / `a` = level 1
- `ee` / `ii` = level 2
- `eee` / `iii` = level 3

Suffixes:

- `dy` = interpret the vowel-run length as **days**
- `iin` = medium fermentation phase (heuristic)
- `aiin` = long fermentation/aging phase (heuristic)

### 2.2 Coverage measurement (implemented)

We do **not** claim any universal coverage numbers in this README. Instead, this repository includes a small script that reports a strict token-coverage metric for the current token grammar:

```sh
python scripts/corpus_coverage.py
```

This prints token coverage (by occurrences) and type coverage (by distinct words), under a strict definition: a word is “covered” only if it tokenizes entirely into known markers.

## 3. Model Assumptions (procedural interpretation)

Given the structural grammar above, we make additional interpretive assumptions to convert EVA sequences into procedural instructions:

1. **Process, not narrative.** Each EVA word is treated as an action/state in a protocol.
2. **Vowel-run length is quantitative.** Repetitions like `e/ee/eee` or `i/ii/iii` are interpreted as level increments that can drive quantities/durations.
3. **Domain: herbal fermentation / mixing protocols.** Because botanical imagery dominates, we apply the model to transformations such as steeping/extraction, heating, mixing/transferring, and fermentation.
4. **Page as a “recipe set” around a main plant.** Operationally, we treat a page as a set of line-recipes. The illustrated plant is never used directly; we always substitute a known edible analog based on a heuristic category (`root/flower/leaf/aquatic/unknown`).
5. **Internal coherence is the evaluation criterion.** The model is useful if it generates internally consistent, materially plausible protocols—even without any claim of matching the manuscript’s true meaning.

### Safety model

- **Never** use an unidentified Voynich plant directly.
- Every “main plant/secondary herb” marker is converted to a **known edible substitute** based on a heuristic plant category:
  `root / flower / leaf / aquatic / unknown`.
- If classification is unknown or low confidence, recipes remain **experimental** and are flagged as only partially coherent.

## 4. Example (direct gloss + speculative instantiation)

Example EVA line:

`qokeedy qokedy chedy daiin`

### Segmentation (symbolic)

- `qokeedy` → `qo + k + ee + dy`
- `qokedy`  → `qo + k + e + dy`
- `chedy`   → `ch + e + dy`
- `daiin`   → `p + aiin` (after normalization `d → p`)

### Structural interpretation

- `qo` = liquid base
- `k` = fermentable sugar
- `ch` = main plant (from the page; always substituted safely)
- `p` = fermentation/yeast
- `e/ee` = level (1/2)
- `dy` = duration in days
- `aiin` = prolonged fermentation/aging phase

### Direct procedural gloss (not a real translation)

“Prepare a liquid base and add fermentables for two days; repeat the adjustment for one additional day; add the main plant for one day; start a prolonged fermentation/aging phase.”

### Instantiation into a small experimental recipe

In the generators in this repo, each manuscript line is treated as an independent small batch (default 0.5 L), with ingredient quantities derived from the detected level markers. The main/secondary plants are always **safe edible substitutes** chosen from a conservative list (e.g., chamomile/lemon balm/mint/ginger/hibiscus) based on the page’s heuristic category.

## Usage

Generate `data/pages/*.json` and `data/pages/*.eva.txt` from `voynich.nu`:

```sh
python scripts/build_pages.py
```

Force re-download:

```sh
python scripts/build_pages.py --force-download
```

## Output

- `data/pages/index.json`: list of folios + metadata (section, Currier, Plant ID if present).
- `data/pages/<folio>.eva.txt`: “cleaned” EVA text (space-separated).
- `data/pages/<folio>.json`: metadata + IVTFF loci + `eva_text`.

## Generated recipes & readmes

After building pages, generate speculative per-line recipes and plain-text READMEs:

```sh
python scripts/generate_recipes.py
python scripts/render_recipes_text.py
```

- `data/recipes/<folio>.recipe.json`: one folio containing multiple **line-recipes** (each locus line is treated as an independent recipe).
- `data/recipe_readmes/<folio>/README.md`: human-readable version with EVA text, direct gloss, and speculative recipe steps.

Quick links:

- `data/recipe_readmes/README.md` (index linking to every folio + every line-recipe)
- `data/recipes/index.json` (machine-readable index of recipe files)

## Images

Download page images from `voynich.nu` into `data/images/`:

```sh
python scripts/download_images.py
```
