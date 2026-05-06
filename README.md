# voynich (per-folio data)

Tools to download an IVTFF (EVA) transliteration and split it by folio/page.

Important: this is **transliteration**, not translation. Any downstream interpretation is **speculative/procedural**.

## 1. Introduction

The Voynich Manuscript (15th century) remains one of the most persistent open problems in the study of languages and writing systems. Its content combines botanical illustrations, diagrams, and an undeciphered text system whose nature—language, cipher, or artificial construct—remains unknown. Despite many attempts, there is no consensus about its meaning or the correct method to approach it.

To enable computational analysis, many researchers use EVA (Extensible/European Voynich Alphabet), a transliteration scheme that maps manuscript glyphs to Latin characters. This transliteration is **not a translation**; it is a consistent representation that allows the text to be studied with computational tools. The EVA corpus exhibits notable properties such as frequent pattern repetition, small variations between words, and statistical distributions that sometimes resemble natural language.

This repository does **not** attempt semantic decipherment. Instead, it explores an alternative approach: treating EVA as a **procedural system**. Concretely, the hypothesis is that recurring sequences can be modeled as structured instructions (technical protocols). This turns unknown text into an interpretable symbolic workflow while staying aligned with observed string-level patterns.

## What is EVA (in this repo)?

EVA (“European Voynich Alphabet”) is a **symbol-to-ASCII transliteration convention** used to represent Voynich glyphs with Latin letters so the text can be processed by computers. In other words:

- EVA here is treated as **input tokens** (strings) extracted from IVTFF/EVA files.
- EVA is **not** assumed to encode a known language, and we do **not** claim any validated meaning.
- This project uses EVA **procedurally**: we map recurring letter patterns to abstract operations/states in a token system.

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

### Token markers (non-semantic)

To avoid arbitrary meaning assignment, this repo treats recurring EVA fragments as **structural markers only**. They are used to drive a procedural *parse* (a “gloss”), not a validated translation.

Core markers:

- `qo`, `q`, `o`, `k`, `t`, `p`, `ch`, `sh`, `f`
- `cth`, `ckh`, `cph`, `cfh` (complex multi-letter markers)

Connectors (low semantic weight; treated as transitions):

- `l, r, n, s, m`

### State / time markers (structural)

We treat the first vowel-run found in a word as a **state/intensity class**:

- `e…`, `i…`, `a…` (three distinct classes)

Run length encodes a level:

- `e` / `i` / `a` = level 1
- `ee` / `ii` = level 2
- `eee` / `iii` = level 3

Suffixes:

- `dy` = interpret the vowel-run length as **days**
- `iin` = medium phase marker (heuristic)
- `aiin` = long phase marker (heuristic)

### 2.2 Coverage measurement (implemented)

This repository includes a small script that reports a strict token-coverage metric for the current token grammar:

```sh
python scripts/corpus_coverage.py
```

This prints token coverage (by occurrences) and type coverage (by distinct words), under a strict definition: a word is “covered” only if it tokenizes entirely into known markers (compounds/connectors/state tokens/suffixes or explicitly-ignored filler tokens).

Current snapshot (from `python scripts/corpus_coverage.py --json`):

- **Token coverage (strict):** 40,259 / 40,992 ≈ **98.21%**
- **Type coverage (strict):** 7,563 / 8,036 ≈ **94.11%**

This is a **string-coverage** metric. It does **not** validate any hypothesis about Voynich meaning.

### 2.3 Lexicon match stats (Italian anagram experiment; heuristic)

This repo also includes a deliberately weak “does it look like an anagrammed lexicon?” probe, inspired by community claims around f99r (pharmaceutical labels).

On **f99r**, using a claimed EVA→AVA-style normalization and checking Italian anagram hits against a 60,404-word list:

- **Claimed mapping:** 30 / 120 basewords matched (**25.0%**)
- **Random mappings baseline:** mean ≈ **10.4%** over 200 permutations
- **p-value (≥ claimed):** **0.00498**

This does **not** imply a correct decipherment. It only shows that a specific normalization produces more anagram hits than random letter-mappings under this narrow test.

Reproduce:

```sh
python scripts/evaluate_ava_anagrams.py --folio f99r --basewords data/base_words.txt
```

### 2.4 “Medieval Italian” angle (pragmatic proxy)

There is no built-in, authoritative “medieval Italian lexicon API” in this repo. Instead, for a *practical* approximation, we use:

- a **WikWik** Italian wordlist (Wiktionary-derived; large coverage; includes many non-modern forms), treated as “medieval-ish” for breadth
- a smaller modern Italian wordlist (for comparison / baselines)

On the **top-500 basewords** (`data/base_words.txt`), using the WikWik-derived list, the anagram search finds:

- **201 / 500** basewords with ≥1 Italian anagram candidate (40.2%)
- of those, a heuristic split labels **66** as “non-generic” and **135** as “generic” (where “generic” means too many candidates / low specificity)

Reproduce:

```sh
python scripts/italianized_anagrams.py
python scripts/classify_anagram_candidates.py
```

## Example “translations” by domain (procedural gloss)

The tables below show what this repository means by “process words”: each EVA token is treated as a compact instruction-like unit (markers + phase/state + optional day/phase suffixes). This is a **procedural gloss**, not a validated translation.

### Herbal (botanical)

| Example folio | Example EVA line | Procedural gloss (first words; abbreviated) |
|---|---|---|
| `f1v` (`data/recipe_readmes/herbal/f1v/README.md`) | `kchsy chydaiin ol o l tchey char cfhar am` | `kchsy`→add solutes; `chydaiin`→main material + activation + long phase; `ol/o`→mix/transfer; `tchey`→heat + main material + extraction… |

### Astronomical / Astrological

| Example folio | Example EVA line | Procedural gloss (first words; abbreviated) |
|---|---|---|
| `f67r1` (`data/recipe_readmes/astronomical/f67r1/README.md`) | `teeodaiin shey epairody osaiin yteeoey…` | `teeodaiin`→heat + mix + activation + long phase; `shey`→secondary material + extraction; `epairody`→mix + activation + days… |

### Biological

| Example folio | Example EVA line | Procedural gloss (first words; abbreviated) |
|---|---|---|
| `f75r` (`data/recipe_readmes/biological/f75r/README.md`) | `kchedykary okeey qokar shyk chedy…` | `kchedykary`→solutes + main material + activation; `okeey`→solutes + mix + extraction; `qokar`→base + solutes + phase-start… |

### Cosmological

| Example folio | Example EVA line | Procedural gloss (first words; abbreviated) |
|---|---|---|
| `f57v` (`data/recipe_readmes/cosmological/f57v/README.md`) | `dairal` | `dairal`→activation + phase-start (single compact token) |

### Text-only (“recipes” pages)

| Example folio | Example EVA line | Procedural gloss (first words; abbreviated) |
|---|---|---|
| `f1r` (`data/recipe_readmes/text_only/f1r/README.md`) | `fachys ykal ar ataiin shol shory…` | `fachys`→main material + aroma + phase-start; `ykal`→solutes + phase-start; `ataiin`→heat + long phase; `shol/shory`→secondary material + mix… |

### Unknown / other

| Example folio | Example EVA line | Procedural gloss (first words; abbreviated) |
|---|---|---|
| `f70v2` (`data/recipe_readmes/unknown/f70v2/README.md`) | `okcheo dar otey ykeey tchy…` | `okcheo`→solutes + main material + mix + extraction; `dar`→activation + phase-start; `otey`→heat + mix + extraction… |

## 3. Model Assumptions (procedural interpretation)

Given the structural grammar above, we make additional interpretive assumptions to convert EVA sequences into procedural instructions:

1. **Process, not narrative.** Each EVA word is treated as an action/state in a protocol.
2. **Vowel-run length is quantitative.** Repetitions like `e/ee/eee` or `i/ii/iii` are interpreted as level increments that can drive quantities/durations.
3. **Domain: procedural protocols (generic).** We apply the model to abstract transformations (e.g., extraction, heating, mixing/transferring, phase transitions) as procedural classes, not validated semantics.
4. **Page as a “protocol set”.** Operationally, we treat a page as a set of line-level protocol units.
5. **Internal coherence is the evaluation criterion.** The model is useful if it generates internally consistent, materially plausible protocols—even without any claim of matching the manuscript’s true meaning.

## 4. Example (direct gloss)

Example EVA line:

`qokeedy qokedy chedy daiin`

### Segmentation (symbolic)

- `qokeedy` → `qo + k + ee + dy`
- `qokedy`  → `qo + k + e + dy`
- `chedy`   → `ch + e + dy`
- `daiin`   → `p + aiin` (after normalization `d → p`)

### Structural interpretation (procedural gloss layer)

- `qo`, `k`, `ch`, `p` are treated as structural markers in the gloss layer.
- `e/ee` = level (1/2)
- `dy` = duration in days
- `aiin` = prolonged phase marker

### Direct procedural gloss (not a real translation)

“Prepare a base and apply markers for two days; repeat for one additional day; add the main component marker for one day; start a prolonged phase.”

### Optional instantiation (experimental)

The codebase includes generators that can turn a procedural gloss into structured steps and quantities. This is experimental and does not imply validated semantics.

## 5. Outputs (what’s in the repo)

- Per-folio EVA text: `data/pages/<folio>.eva.txt`
- Per-folio images (voynich.nu cache): `data/images/`
- Per-folio generated protocols: `data/recipes/<folio>.recipe.json`
- Per-folio READMEs (image + EVA with line breaks + gloss + domain context): `data/recipe_readmes/<domain>/<folio>/README.md`
- Domain folders (section indexes + associated basewords + heuristic anagrams/glosses): `data/domains/<domain>/README.md`
- Domain “sense layer” (separate script; heuristic): `data/domain_sense/<domain>.sense.json`

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

## Generated outputs & readmes

After building pages, generate per-line outputs and plain-text READMEs:

```sh
python scripts/generate_recipes.py
python scripts/render_recipes_text.py
```

- `data/recipes/<folio>.recipe.json`: one folio containing multiple line-level protocol units (JSON).
- `data/recipe_readmes/<folio>/README.md`: human-readable version with EVA text and a direct procedural gloss.

Quick links:

- `data/recipe_readmes/README.md` (index linking to every folio + every line-recipe)
- `data/recipes/index.json` (machine-readable index of recipe files)

## Images

Download page images from `voynich.nu` into `data/images/`:

```sh
python scripts/download_images.py
```
