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

### 2.5 Latin candidates (Whitaker WORDS; heuristic)

This repo can also generate **Latin lemma anagram candidates** using Whitaker’s WORDS `DICTLINE.GEN` (downloaded and lemma-extracted locally). This is used as an additional “classical/medieval Latin” proxy wordlist.

Reproduce:

```sh
python scripts/download_latin_wordlist.py
python scripts/latinized_anagrams.py
```

## Example “translations” by domain (procedural gloss)

The sections below show what this repository means by “process words”: each EVA token is treated as a compact **structured token** (markers + state/intensity + optional suffixes). This is a procedural **gloss** (structure-first), not a validated translation.

### How a “process word” is built (decomposition)

One EVA word is treated as a **bundle of markers**:

- **compounds**: recurring chunks like `qo`, `k`, `t`, `p`, `ch`, `sh`, `cth`…
- **connectors**: low-weight joiners `l/r/n/s/m`
- **state/intensity**: the first vowel-run `e…` / `i…` / `a…` (length = level 1–3)
- **suffixes**: `dy` (days), `iin` (medium phase), `aiin` (long phase)
- **normalization**: `d→p`, `y` removed except in `dy`, `ktp` split into `k+t+p`

Concrete example:

| EVA word | Normalized | Segmentation | Procedural gloss (structural) |
|---|---|---|---|
| `qokeedy` | `qokeepy` (from `d→p`, and keeping `dy`) | `qo + k + ee + dy` | marker `qo` + marker `k` + state `ee` + suffix `dy` |
| `daiin` | `paiin` | `p + aiin` | marker `p` + suffix `aiin` |

If you want the markers to have a **domain-tinted sense**, this repo generates an optional “sense layer” from the domain lexicon tables (WikWik “medieval-ish Italian” proxy + English gloss keywords):

- `data/domain_sense/<domain>.sense.json` (built by `python scripts/assign_domain_sense.py`)

Note on `daiin`: after normalization `d→p`, `daiin` becomes `paiin` and tokenizes as `p + aiin`. In this repo’s time heuristic, `aiin` is a **long phase marker** (typically treated as multi-day, e.g. ~7–14 days) even though it does not explicitly contain `dy`.

## Best lexicon-grounded examples (by domain)

Selected because they have a **non-empty English gloss** in the domain lexicon table (WikWik “medieval-ish Italian” proxy + Wiktionary gloss extraction). Still not a translation.

### herbal
| EVA baseword | Count (domain) | Italian candidate | English gloss | Example |
|---|---:|---|---|---|
| `daiin` | 461 | `piani` | plans (arrangements) | `f1v` (f1v.8,+P0) → `data/recipe_readmes/herbal/f1v/README.md` |
| `odaiin` | 27 | `inopia` | poverty | `f3r` (f3r.20,+P0) → `data/recipe_readmes/herbal/f3r/README.md` |
| `otchol` | 25 | `colto` | cultivated | `f3r` (f3r.7,+P0) → `data/recipe_readmes/herbal/f3r/README.md` |

### astronomical
| EVA baseword | Count (domain) | Italian candidate | English gloss | Example |
|---|---:|---|---|---|
| `daiin` | 11 | `piani` | plans (arrangements) | `f67r1` (f67r1.6,+Cc) → `data/recipe_readmes/astronomical/f67r1/README.md` |
| `odaiin` | 2 | `inopia` | poverty | `f67r1` (f67r1.6,+Cc) → `data/recipe_readmes/astronomical/f67r1/README.md` |
| `ydaiin` | 2 | `piani` | plans (arrangements) | `f67r2` (f67r2.72,@P0) → `data/recipe_readmes/astronomical/f67r2/README.md` |

### biological
| EVA baseword | Count (domain) | Italian candidate | English gloss | Example |
|---|---:|---|---|---|
| `qokal` | 102 | `calco` | cast (of sculpture) | `f75r` (f75r.11,+P0) → `data/recipe_readmes/biological/f75r/README.md` |
| `daiin` | 81 | `piani` | plans (arrangements) | `f75v` (f75v.3,*P0) → `data/recipe_readmes/biological/f75v/README.md` |
| `okain` | 40 | `acino` | a berry | `f75v` (f75v.38,@P0) → `data/recipe_readmes/biological/f75v/README.md` |

### cosmological
| EVA baseword | Count (domain) | Italian candidate | English gloss | Example |
|---|---:|---|---|---|
| `daiin` | 28 | `piani` | plans (arrangements) | `f57v` (f57v.4,+Cc) → `data/recipe_readmes/cosmological/f57v/README.md` |
| `qokal` | 13 | `calco` | cast (of sculpture) | `f68v3` (f68v3.11,@Ri) → `data/recipe_readmes/cosmological/f68v3/README.md` |
| `odaiin` | 8 | `inopia` | poverty | `f85r2` (fRos.62,@Cc) → `data/recipe_readmes/cosmological/f85r2/README.md` |

### text_only
| EVA baseword | Count (domain) | Italian candidate | English gloss | Example |
|---|---:|---|---|---|
| `daiin` | 40 | `piani` | plans (arrangements) | `f1r` (f1r.4,+P0) → `data/recipe_readmes/text_only/f1r/README.md` |
| `qokal` | 23 | `calco` | cast (of sculpture) | `f58r` (f58r.31,+P0) → `data/recipe_readmes/text_only/f58r/README.md` |
| `okain` | 10 | `acino` | a berry | `f58v` (f58v.19,+P0) → `data/recipe_readmes/text_only/f58v/README.md` |

### unknown
| EVA baseword | Count (domain) | Italian candidate | English gloss | Example |
|---|---:|---|---|---|
| `daiin` | 231 | `piani` | plans (arrangements) | `f70v2` (f70v2.21,@Cc) → `data/recipe_readmes/unknown/f70v2/README.md` |
| `okain` | 69 | `acino` | a berry | `f89r2` (f89r2.29,@Lc) → `data/recipe_readmes/unknown/f89r2/README.md` |
| `qokal` | 43 | `calco` | cast (of sculpture) | `f89r2` (f89r2.22,@P0) → `data/recipe_readmes/unknown/f89r2/README.md` |

## Top candidate basewords by domain (first 20)

These are taken directly from `data/domains/<domain>/README.md` (Domain Lexicon table).

### herbal
| EVA baseword | Count | Medieval-ish Italian | English gloss | Latin candidate |
|---|---:|---|---|---|
| `daiin` | 461 | `piani` | plans (arrangements) | [n/a] |
| `okaiin` | 59 | `coniai` | [n/a] | [n/a] |
| `chaiin` | 39 | `acini` | [n/a] | [n/a] |
| `saiin` | 37 | `asini` | [n/a] | [n/a] |
| `qokaiin` | 34 | `ciancio` | [n/a] | [n/a] |
| `qokar` | 29 | `carco` | [n/a] | [n/a] |
| `odaiin` | 27 | `inopia` | poverty | [n/a] |
| `otchol` | 25 | `colto` | cultivated | `colot` |
| `kaiin` | 24 | `acini` | [n/a] | [n/a] |
| `chodaiin` | 24 | `apocini` | [n/a] | [n/a] |
| `qotol` | 20 | `colto` | cultivated | `colot` |
| `okain` | 19 | `acino` | a berry | [n/a] |
| `qotor` | 18 | `corto` | short | `coort` |
| `ykaiin` | 16 | `acini` | [n/a] | [n/a] |
| `qodaiin` | 15 | `apocini` | [n/a] | [n/a] |
| `shodaiin` | 15 | `sinopia` | [n/a] | [n/a] |
| `qotaiin` | 14 | `cationi` | [n/a] | `aconiti` |
| `otchor` | 14 | `corto` | short | `coort` |
| `shaiin` | 13 | `asini` | [n/a] | [n/a] |
| `qokal` | 12 | `calco` | cast (of sculpture) | `accol` |

### astronomical
| EVA baseword | Count | Medieval-ish Italian | English gloss | Latin candidate |
|---|---:|---|---|---|
| `daiin` | 11 | `piani` | plans (arrangements) | [n/a] |
| `daiir` | 4 | `aprii` | [n/a] | [n/a] |
| `saiin` | 2 | `asini` | [n/a] | [n/a] |
| `odaiin` | 2 | `inopia` | poverty | [n/a] |
| `ydaiin` | 2 | `piani` | plans (arrangements) | [n/a] |
| `okain` | 1 | `acino` | a berry | [n/a] |
| `qokeol` | 1 | `eccolo` | [n/a] | [n/a] |
| `chedar` | 1 | `capre` | [n/a] | `caper` |
| `oteos` | 1 | `osteo` | [n/a] | [n/a] |
| `okees` | 1 | `coese` | [n/a] | [n/a] |
| `okchor` | 1 | `corco` | [n/a] | [n/a] |
| `odain` | 1 | `opina` | opine | [n/a] |
| `chodar` | 1 | `capro` | male goat | [n/a] |
| `okeos` | 1 | `coeso` | cohesive | [n/a] |

### biological
| EVA baseword | Count | Medieval-ish Italian | English gloss | Latin candidate |
|---|---:|---|---|---|
| `qokain` | 158 | `acconi` | [n/a] | `cocain` |
| `qokal` | 102 | `calco` | cast (of sculpture) | `accol` |
| `daiin` | 81 | `piani` | plans (arrangements) | [n/a] |
| `qokaiin` | 81 | `ciancio` | [n/a] | [n/a] |
| `qokar` | 45 | `carco` | [n/a] | [n/a] |
| `okain` | 40 | `acino` | a berry | [n/a] |
| `okaiin` | 31 | `coniai` | [n/a] | [n/a] |
| `saiin` | 30 | `asini` | [n/a] | [n/a] |
| `olkain` | 26 | `alcino` | smart, clever, intelligent, bright | [n/a] |
| `qotal` | 25 | `colta` | [n/a] | `calot` |
| `otain` | 23 | `anito` | [n/a] | `natio` |
| `qotain` | 20 | `antico` | ancient | `aconit` |
| `qotar` | 16 | `corta` | [n/a] | `actor` |
| `qotaiin` | 13 | `cationi` | [n/a] | `aconiti` |
| `kaiin` | 7 | `acini` | [n/a] | [n/a] |
| `qotol` | 7 | `colto` | cultivated | `colot` |
| `olkaiin` | 7 | `caolini` | [n/a] | [n/a] |
| `olaiin` | 6 | `ialino` | hyaline, glassy | [n/a] |
| `olkar` | 6 | `carlo` | [n/a] | `calor` |
| `qokaly` | 6 | `calco` | cast (of sculpture) | `accol` |

### cosmological
| EVA baseword | Count | Medieval-ish Italian | English gloss | Latin candidate |
|---|---:|---|---|---|
| `daiin` | 28 | `piani` | plans (arrangements) | [n/a] |
| `qokal` | 13 | `calco` | cast (of sculpture) | `accol` |
| `odaiin` | 8 | `inopia` | poverty | [n/a] |
| `okees` | 7 | `coese` | [n/a] | [n/a] |
| `opaiin` | 6 | `inopia` | poverty | [n/a] |
| `ykaiin` | 5 | `acini` | [n/a] | [n/a] |
| `qodaiin` | 5 | `apocini` | [n/a] | [n/a] |
| `oteos` | 5 | `osteo` | [n/a] | [n/a] |
| `olkar` | 5 | `carlo` | [n/a] | `calor` |
| `okaiin` | 4 | `coniai` | [n/a] | [n/a] |
| `qotaiin` | 4 | `cationi` | [n/a] | `aconiti` |
| `qokaiin` | 3 | `ciancio` | [n/a] | [n/a] |
| `qokar` | 3 | `carco` | [n/a] | [n/a] |
| `olaiin` | 3 | `ialino` | hyaline, glassy | [n/a] |
| `oraiin` | 3 | `aironi` | [n/a] | [n/a] |
| `olkaiin` | 3 | `caolini` | [n/a] | [n/a] |
| `otair` | 3 | `atrio` | entrance hall, lobby (of a hotel etc.) | `ratio` |
| `shodaiin` | 3 | `sinopia` | [n/a] | [n/a] |
| `otain` | 2 | `anito` | [n/a] | `natio` |
| `kaiin` | 2 | `acini` | [n/a] | [n/a] |

### text_only
| EVA baseword | Count | Medieval-ish Italian | English gloss | Latin candidate |
|---|---:|---|---|---|
| `daiin` | 40 | `piani` | plans (arrangements) | [n/a] |
| `qokar` | 31 | `carco` | [n/a] | [n/a] |
| `qokaiin` | 25 | `ciancio` | [n/a] | [n/a] |
| `qokal` | 23 | `calco` | cast (of sculpture) | `accol` |
| `ykaiin` | 15 | `acini` | [n/a] | [n/a] |
| `okaiin` | 12 | `coniai` | [n/a] | [n/a] |
| `qokain` | 10 | `acconi` | [n/a] | `cocain` |
| `okain` | 10 | `acino` | a berry | [n/a] |
| `saiin` | 10 | `asini` | [n/a] | [n/a] |
| `kaiin` | 9 | `acini` | [n/a] | [n/a] |
| `odaiin` | 9 | `inopia` | poverty | [n/a] |
| `qotaiin` | 8 | `cationi` | [n/a] | `aconiti` |
| `qotar` | 8 | `corta` | [n/a] | `actor` |
| `qotal` | 8 | `colta` | [n/a] | `calot` |
| `otain` | 7 | `anito` | [n/a] | `natio` |
| `qokaly` | 7 | `calco` | cast (of sculpture) | `accol` |
| `qotain` | 6 | `antico` | ancient | `aconit` |
| `qokair` | 6 | `accori` | [n/a] | `cicaro` |
| `olkar` | 6 | `carlo` | [n/a] | `calor` |
| `olaiin` | 5 | `ialino` | hyaline, glassy | [n/a] |

### unknown
| EVA baseword | Count | Medieval-ish Italian | English gloss | Latin candidate |
|---|---:|---|---|---|
| `daiin` | 231 | `piani` | plans (arrangements) | [n/a] |
| `qokaiin` | 122 | `ciancio` | [n/a] | [n/a] |
| `okaiin` | 109 | `coniai` | [n/a] | [n/a] |
| `qokain` | 101 | `acconi` | [n/a] | `cocain` |
| `okain` | 69 | `acino` | a berry | [n/a] |
| `otain` | 53 | `anito` | [n/a] | `natio` |
| `qokar` | 48 | `carco` | [n/a] | [n/a] |
| `saiin` | 46 | `asini` | [n/a] | [n/a] |
| `qokal` | 43 | `calco` | cast (of sculpture) | `accol` |
| `qotaiin` | 40 | `cationi` | [n/a] | `aconiti` |
| `lkaiin` | 39 | `ancili` | [n/a] | `lacini` |
| `kaiin` | 37 | `acini` | [n/a] | [n/a] |
| `qokeol` | 37 | `eccolo` | [n/a] | [n/a] |
| `qotain` | 34 | `antico` | ancient | `aconit` |
| `qotar` | 29 | `corta` | [n/a] | `actor` |
| `olaiin` | 29 | `ialino` | hyaline, glassy | [n/a] |
| `lkain` | 28 | `lanci` | [n/a] | `alcin` |
| `chedar` | 25 | `capre` | [n/a] | `caper` |
| `odaiin` | 24 | `inopia` | poverty | [n/a] |
| `otair` | 21 | `atrio` | entrance hall, lobby (of a hotel etc.) | `ratio` |

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

Structural gloss (no semantic meaning claimed): the line decomposes into marker bundles like `qo+k+ee+dy`, `ch+e+dy`, `p+aiin`, plus a vowel-run class (`e/i/a`) whose length defines a level (1–3) and optional suffixes (`dy/iin/aiin`).

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
