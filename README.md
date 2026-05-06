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

The grammar below is a **user-defined symbolic model** (not Voynich scholarship). It converts EVA words into structural markers + state/phase cues.

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

In this formulation, `P`/`BLOCK`/`T`/`C` capture recurring word-shapes seen in EVA.

### Normalizations

- `d → p`
- `y → (removed)`, except when it forms `dy`
- `ktp → k + t + p` (tokenized as three markers)

### Token markers (structural)

Core markers: `qo q o k t p ch sh f` and `cth ckh cph cfh` (multi-letter markers).  
Connectors: `l r n s m`.

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

This does not imply a correct decipherment; it is a narrow string-matching signal only.

Reproduce:

```sh
python scripts/evaluate_ava_anagrams.py --folio f99r --basewords data/base_words.txt
```

### 2.4 “Medieval Italian” angle (pragmatic proxy)

We use WikWik (Wiktionary-derived) as a “medieval-ish” breadth proxy, plus a smaller modern Italian list for comparison.

On the **top-500 basewords** (`data/base_words.txt`), using the WikWik-derived list, the anagram search finds:

- **201 / 500** basewords with ≥1 Italian anagram candidate (40.2%)
- of those, a heuristic split labels **66** as “non-generic” and **135** as “generic” (where “generic” means too many candidates / low specificity)

Reproduce:

```sh
python scripts/italianized_anagrams.py
python scripts/classify_anagram_candidates.py
```

### 2.5 Latin candidates (Whitaker WORDS; heuristic)

This repo can also generate Latin lemma anagram candidates using Whitaker’s WORDS `DICTLINE.GEN` (as an additional Latin proxy list).

Reproduce:

```sh
python scripts/download_latin_wordlist.py
python scripts/latinized_anagrams.py
```

## Example “translations” by domain (procedural gloss)

EVA tokens are treated as compact structured units (markers + state/intensity + optional suffixes). This is a procedural gloss (structure-first), not a translation.

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

Note on `daiin`: after normalization `d→p`, `daiin` is counted as `paiin` and tokenizes as `p + aiin` (long phase marker).

## Best full-line lexicon glosses (by domain)

For each IVTFF domain, this selects one complete manuscript line with the most lexicon hits (modern Italian list + WikWik “medieval-ish” proxy + Whitaker Latin). Still not a translation.

### herbal
- Source: `f32v` / `f32v.8,+P0` → `data/recipe_readmes/herbal/f32v/README.md`
- EVA line:
```text
otchol daiin daiin ctho daiin qotaiin otchy d shan
```
- English structural gloss (generated):
```text
otchol: tokens: o t ch o l → connectors: l; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; ctho: tokens: cth o; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; qotaiin: tokens: qo t aiin → vowel_run: a (level 1; class a) → suffix: aiin; otchy: tokens: o t ch; d: tokens: p; shan: tokens: sh a n → connectors: n → vowel_run: a (level 1; class a)
```
- Lexicon hits (inherited context):
- `otchol` (→ `otchol`): it(mod) `colto` / cultivated; it(med) `colto` / cultivated; la `colot` / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `qotaiin` (→ `qotaiin`): it(mod) `coniati` / [n/a]; it(med) `cationi` / [n/a]; la `aconiti` / without dust (literally)

### astronomical
- Source: `f67r1` / `f67r1.6,+Cc` → `data/recipe_readmes/astronomical/f67r1/README.md`
- EVA line:
```text
dair al cheol dal oekaiin sol daiin eetees saiin ykeos l chy otodaiin chetejy otar dair ar chedar okeedy ot[e:i]odaiin ychsy chekeey ot dol al cheor okeo r oiin cheeky ary okeo keds oshey shchey chol dair dain cho dar aldy
```
- English structural gloss (generated):
```text
dair: tokens: p a i r → connectors: r → vowel_run: a (level 1; class a); al: tokens: a l → connectors: l → vowel_run: a (level 1; class a); cheol: tokens: ch e o l → connectors: l → vowel_run: e (level 1; class e); dal: tokens: p a l → connectors: l → vowel_run: a (level 1; class a); oekaiin: tokens: o e k aiin → vowel_run: e (level 1; class e) → suffix: aiin; sol: tokens: s o l → connectors: s l; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; eetees: tokens: ee t ee s → connectors: s → vowel_run: ee (level 2; class e); saiin: tokens: s aiin → connectors: s → vowel_run: a (level 1; class a) → suffix: aiin; ykeos: tokens: k e o s → connectors: s → vowel_run: e (level 1; class e); l: tokens: l → connectors: l; chy: tokens: ch; otodaiin: tokens: o t o p aiin → vowel_run: a (level 1; class a) → suffix: aiin; chetejy: tokens: ch e t e j → vowel_run: e (level 1; class e); otar: tokens: o t a r → connectors: r → vowel_run: a (level 1; class a); dair: tokens: p a i r → connectors: r → vowel_run: a (level 1; class a); ar: tokens: a r → connectors: r → vowel_run: a (level 1; class a); chedar: tokens: ch e p a r → connectors: r → vowel_run: e (level 1; class e); okeedy: tokens: o k ee p → vowel_run: ee (level 2; class e); ot: tokens: o t
```
- Lexicon hits (inherited context):
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `chedar` (→ `chepar`): it(mod) `capre` / [n/a]; it(med) `capre` / [n/a]; la `caper` / goatish/armpit smell
- `odaiin` (→ `opaiin`): it(mod) `opinai` / [n/a]; it(med) `inopia` / poverty; la [n/a] / [n/a]

### biological
- Source: `f80r` / `f80r.19,+P0` → `data/recipe_readmes/biological/f80r/README.md`
- EVA line:
```text
dcheol shedy qok[ee:a]l qotaiin chtal schcthy qokal chcthy qokain okain oloky
```
- English structural gloss (generated):
```text
dcheol: tokens: p ch e o l → connectors: l → vowel_run: e (level 1; class e); shedy: tokens: sh e p → vowel_run: e (level 1; class e); qok: tokens: qo k; ee: tokens: ee → vowel_run: ee (level 2; class e); a: tokens: a → vowel_run: a (level 1; class a); l: tokens: l → connectors: l; qotaiin: tokens: qo t aiin → vowel_run: a (level 1; class a) → suffix: aiin; chtal: tokens: ch t a l → connectors: l → vowel_run: a (level 1; class a); schcthy: tokens: s ch cth → connectors: s; qokal: tokens: qo k a l → connectors: l → vowel_run: a (level 1; class a); chcthy: tokens: ch cth; qokain: tokens: qo k a i n → connectors: n → vowel_run: a (level 1; class a); okain: tokens: o k a i n → connectors: n → vowel_run: a (level 1; class a); oloky: tokens: o l o k → connectors: l
```
- Lexicon hits (inherited context):
- `qotaiin` (→ `qotaiin`): it(mod) `coniati` / [n/a]; it(med) `cationi` / [n/a]; la `aconiti` / without dust (literally)
- `qokal` (→ `qokal`): it(mod) `calco` / cast (of sculpture); it(med) `calco` / cast (of sculpture); la `accol` / one who lives nearby/beside
- `qokain` (→ `qokain`): it(mod) `concia` / tanning; it(med) `acconi` / [n/a]; la `cocain` / [n/a]
- `okain` (→ `okain`): it(mod) `conia` / [n/a]; it(med) `acino` / a berry; la [n/a] / [n/a]

### cosmological
- Source: `f86v4` / `f86v4.2,@Cc` → `data/recipe_readmes/cosmological/f86v4/README.md`
- EVA line:
```text
oeeey [o:y] daiin otedaiin otedy oteey chedaiin octhedy chy shedaiin chotaiin oraiin otodeee[?:o] ar yteeody oteedaraiin shedaiin chdar shedy qotedaiin chedy tchdy chetdy chedy qotar chedy chckhy daiin otedy seeedy yteey sam
```
- English structural gloss (generated):
```text
oeeey: tokens: o eee → vowel_run: eee (level 3; class e); o: tokens: o; y: [unparsed]; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; otedaiin: tokens: o t e p aiin → vowel_run: e (level 1; class e) → suffix: aiin; otedy: tokens: o t e p → vowel_run: e (level 1; class e); oteey: tokens: o t ee → vowel_run: ee (level 2; class e); chedaiin: tokens: ch e p aiin → vowel_run: e (level 1; class e) → suffix: aiin; octhedy: tokens: o cth e p → vowel_run: e (level 1; class e); chy: tokens: ch; shedaiin: tokens: sh e p aiin → vowel_run: e (level 1; class e) → suffix: aiin; chotaiin: tokens: ch o t aiin → vowel_run: a (level 1; class a) → suffix: aiin; oraiin: tokens: o r aiin → connectors: r → vowel_run: a (level 1; class a) → suffix: aiin; otodeee: tokens: o t o p eee → vowel_run: eee (level 3; class e); o: tokens: o; ar: tokens: a r → connectors: r → vowel_run: a (level 1; class a); yteeody: tokens: t ee o p → vowel_run: ee (level 2; class e); oteedaraiin: tokens: o t ee p a r aiin → connectors: r → vowel_run: ee (level 2; class e) → suffix: aiin; shedaiin: tokens: sh e p aiin → vowel_run: e (level 1; class e) → suffix: aiin; chdar: tokens: ch p a r → connectors: r → vowel_run: a (level 1; class a)
```
- Lexicon hits (inherited context):
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `otedaiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `chedaiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `shedaiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `oraiin` (→ `oraiin`): it(mod) `ironia` / irony; it(med) `aironi` / [n/a]; la [n/a] / [n/a]
- `shedaiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `qotedaiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `qotar` (→ `qotar`): it(mod) `corta` / [n/a]; it(med) `corta` / [n/a]; la `actor` / advocate
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]

### text_only
- Source: `f86v6` / `f86v6.39,+P0` → `data/recipe_readmes/text_only/f86v6/README.md`
- EVA line:
```text
y aiin dar otol qokain qoky lkor dal oraiin cheoty qotaiin olkam
```
- English structural gloss (generated):
```text
y: [unparsed]; aiin: tokens: aiin → vowel_run: a (level 1; class a) → suffix: aiin; dar: tokens: p a r → connectors: r → vowel_run: a (level 1; class a); otol: tokens: o t o l → connectors: l; qokain: tokens: qo k a i n → connectors: n → vowel_run: a (level 1; class a); qoky: tokens: qo k; lkor: tokens: l k o r → connectors: l r; dal: tokens: p a l → connectors: l → vowel_run: a (level 1; class a); oraiin: tokens: o r aiin → connectors: r → vowel_run: a (level 1; class a) → suffix: aiin; cheoty: tokens: ch e o t → vowel_run: e (level 1; class e); qotaiin: tokens: qo t aiin → vowel_run: a (level 1; class a) → suffix: aiin; olkam: tokens: o l k a m → connectors: l m → vowel_run: a (level 1; class a)
```
- Lexicon hits (inherited context):
- `qokain` (→ `qokain`): it(mod) `concia` / tanning; it(med) `acconi` / [n/a]; la `cocain` / [n/a]
- `oraiin` (→ `oraiin`): it(mod) `ironia` / irony; it(med) `aironi` / [n/a]; la [n/a] / [n/a]
- `qotaiin` (→ `qotaiin`): it(mod) `coniati` / [n/a]; it(med) `cationi` / [n/a]; la `aconiti` / without dust (literally)
- `olkam` (→ `olkam`): it(mod) `calmo` / calm, peaceful, quiet, still; it(med) `calmo` / calm, peaceful, quiet, still; la [n/a] / [n/a]

### unknown
- Source: `f101r` / `f101r.8,+P0` → `data/recipe_readmes/unknown/f101r/README.md`
- EVA line:
```text
olaiin oteol chor oteey chokchey kor daiin shok chol chol qoky daiin ol s al ydar daiin or ory okeey daiin shey daiin okol cheor
```
- English structural gloss (generated):
```text
olaiin: tokens: o l aiin → connectors: l → vowel_run: a (level 1; class a) → suffix: aiin; oteol: tokens: o t e o l → connectors: l → vowel_run: e (level 1; class e); chor: tokens: ch o r → connectors: r; oteey: tokens: o t ee → vowel_run: ee (level 2; class e); chokchey: tokens: ch o k ch e → vowel_run: e (level 1; class e); kor: tokens: k o r → connectors: r; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; shok: tokens: sh o k; chol: tokens: ch o l → connectors: l; chol: tokens: ch o l → connectors: l; qoky: tokens: qo k; daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; ol: tokens: o l → connectors: l; s: tokens: s → connectors: s; al: tokens: a l → connectors: l → vowel_run: a (level 1; class a); ydar: tokens: p a r → connectors: r → vowel_run: a (level 1; class a); daiin: tokens: p aiin → vowel_run: a (level 1; class a) → suffix: aiin; or: tokens: o r → connectors: r; ory: tokens: o r → connectors: r; okeey: tokens: o k ee → vowel_run: ee (level 2; class e)
```
- Lexicon hits (inherited context):
- `olaiin` (→ `olaiin`): it(mod) [n/a] / [n/a]; it(med) `ialino` / hyaline, glassy; la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]
- `daiin` (→ `paiin`): it(mod) `piani` / plans (arrangements); it(med) `piani` / plans (arrangements); la [n/a] / [n/a]

## Top candidate basewords by domain (first 20)

These are taken directly from `data/domains/<domain>/README.md` (Domain Lexicon table).

### herbal
| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |
|---|---:|---|---|---|---|---|---|
| `paiin` | 477 | `piani` | plans (arrangements) | `piani` | plans (arrangements) | [n/a] | [n/a] |
| `okaiin` | 59 | `coniai` | [n/a] | `coniai` | [n/a] | [n/a] | [n/a] |
| `qokep` | 41 | `pecco` | [n/a] | `pecco` | [n/a] | [n/a] | [n/a] |
| `saiin` | 40 | `asini` | [n/a] | `asini` | [n/a] | [n/a] | [n/a] |
| `kaiin` | 40 | [n/a] | [n/a] | `acini` | [n/a] | [n/a] | [n/a] |
| `chaiin` | 39 | [n/a] | [n/a] | `acini` | [n/a] | [n/a] | [n/a] |
| `qokaiin` | 34 | `conciai` | [n/a] | `ciancio` | [n/a] | [n/a] | [n/a] |
| `qokar` | 29 | [n/a] | [n/a] | `carco` | [n/a] | [n/a] | [n/a] |
| `opaiin` | 29 | `opinai` | [n/a] | `inopia` | poverty | [n/a] | [n/a] |
| `otchol` | 25 | `colto` | cultivated | `colto` | cultivated | `colot` | [n/a] |
| `chopaiin` | 24 | [n/a] | [n/a] | `apocini` | [n/a] | [n/a] | [n/a] |
| `qotol` | 20 | `colto` | cultivated | `colto` | cultivated | `colot` | [n/a] |
| `okain` | 19 | `conia` | [n/a] | `acino` | a berry | [n/a] | [n/a] |
| `qotor` | 18 | `corto` | short | `corto` | short | `coort` | breaking out (storm) |
| `qopaiin` | 15 | [n/a] | [n/a] | `apocini` | [n/a] | [n/a] | [n/a] |
| `shopaiin` | 15 | [n/a] | [n/a] | `sinopia` | [n/a] | [n/a] | [n/a] |
| `qotaiin` | 14 | `coniati` | [n/a] | `cationi` | [n/a] | `aconiti` | without dust (literally) |
| `otchor` | 14 | `corto` | short | `corto` | short | `coort` | breaking out (storm) |
| `qokal` | 13 | `calco` | cast (of sculpture) | `calco` | cast (of sculpture) | `accol` | one who lives nearby/beside |
| `shaiin` | 13 | `asini` | [n/a] | `asini` | [n/a] | [n/a] | [n/a] |

### astronomical
| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |
|---|---:|---|---|---|---|---|---|
| `paiin` | 13 | `piani` | plans (arrangements) | `piani` | plans (arrangements) | [n/a] | [n/a] |
| `paiir` | 4 | `aprii` | [n/a] | `aprii` | [n/a] | [n/a] | [n/a] |
| `saiin` | 2 | `asini` | [n/a] | `asini` | [n/a] | [n/a] | [n/a] |
| `opaiin` | 2 | `opinai` | [n/a] | `inopia` | poverty | [n/a] | [n/a] |
| `oteos` | 2 | [n/a] | [n/a] | `osteo` | [n/a] | [n/a] | [n/a] |
| `opain` | 2 | `opina` | opine | `opina` | opine | [n/a] | [n/a] |
| `okain` | 1 | `conia` | [n/a] | `acino` | a berry | [n/a] | [n/a] |
| `qokeol` | 1 | [n/a] | [n/a] | `eccolo` | [n/a] | [n/a] | [n/a] |
| `chepar` | 1 | `capre` | [n/a] | `capre` | [n/a] | `caper` | goatish/armpit smell |
| `qokche` | 1 | [n/a] | [n/a] | `cecco` | [n/a] | [n/a] | [n/a] |
| `okees` | 1 | [n/a] | [n/a] | `coese` | [n/a] | [n/a] | [n/a] |
| `okchor` | 1 | [n/a] | [n/a] | `corco` | [n/a] | [n/a] | [n/a] |
| `chopar` | 1 | `copra` | [n/a] | `capro` | male goat | [n/a] | [n/a] |
| `topaiin` | 1 | `opinati` | [n/a] | `opinati` | [n/a] | [n/a] | [n/a] |
| `poiin` | 1 | `opini` | [n/a] | `inopi` | [n/a] | `inopi` | poverty, destitution, dearth, want, scarcity |
| `okalp` | 1 | `colpa` | fault | `colpa` | fault | [n/a] | [n/a] |
| `okeos` | 1 | [n/a] | [n/a] | `coeso` | cohesive | [n/a] | [n/a] |

### biological
| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |
|---|---:|---|---|---|---|---|---|
| `qokep` | 160 | `pecco` | [n/a] | `pecco` | [n/a] | [n/a] | [n/a] |
| `qokain` | 159 | `concia` | tanning | `acconi` | [n/a] | `cocain` | [n/a] |
| `qokal` | 108 | `calco` | cast (of sculpture) | `calco` | cast (of sculpture) | `accol` | one who lives nearby/beside |
| `paiin` | 82 | `piani` | plans (arrangements) | `piani` | plans (arrangements) | [n/a] | [n/a] |
| `qokaiin` | 81 | `conciai` | [n/a] | `ciancio` | [n/a] | [n/a] | [n/a] |
| `qokar` | 45 | [n/a] | [n/a] | `carco` | [n/a] | [n/a] | [n/a] |
| `okain` | 41 | `conia` | [n/a] | `acino` | a berry | [n/a] | [n/a] |
| `okaiin` | 31 | `coniai` | [n/a] | `coniai` | [n/a] | [n/a] | [n/a] |
| `saiin` | 30 | `asini` | [n/a] | `asini` | [n/a] | [n/a] | [n/a] |
| `olkain` | 26 | `calino` | [n/a] | `alcino` | smart, clever, intelligent, bright | [n/a] | [n/a] |
| `qotal` | 25 | `colta` | [n/a] | `colta` | [n/a] | `calot` | [n/a] |
| `olchep` | 24 | `colpe` | [n/a] | `colpe` | [n/a] | [n/a] | [n/a] |
| `otain` | 23 | `notai` | [n/a] | `anito` | [n/a] | `natio` | birth |
| `qotain` | 20 | `antico` | ancient | `antico` | ancient | `aconit` | aconite as a poison |
| `olkep` | 20 | `colpe` | [n/a] | `colpe` | [n/a] | [n/a] | [n/a] |
| `qotar` | 17 | `corta` | [n/a] | `corta` | [n/a] | `actor` | advocate |
| `olshep` | 17 | `spole` | [n/a] | `spelo` | [n/a] | `lepos` | wit |
| `opchep` | 14 | [n/a] | [n/a] | `ceppo` | stump (of a tree) | [n/a] | [n/a] |
| `qotaiin` | 13 | `coniati` | [n/a] | `cationi` | [n/a] | `aconiti` | without dust (literally) |
| `kaiin` | 9 | [n/a] | [n/a] | `acini` | [n/a] | [n/a] | [n/a] |

### cosmological
| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |
|---|---:|---|---|---|---|---|---|
| `paiin` | 29 | `piani` | plans (arrangements) | `piani` | plans (arrangements) | [n/a] | [n/a] |
| `opaiin` | 14 | `opinai` | [n/a] | `inopia` | poverty | [n/a] | [n/a] |
| `qokal` | 13 | `calco` | cast (of sculpture) | `calco` | cast (of sculpture) | `accol` | one who lives nearby/beside |
| `kaiin` | 7 | [n/a] | [n/a] | `acini` | [n/a] | [n/a] | [n/a] |
| `okees` | 7 | [n/a] | [n/a] | `coese` | [n/a] | [n/a] | [n/a] |
| `oteop` | 6 | [n/a] | [n/a] | `poeto` | [n/a] | [n/a] | [n/a] |
| `qopaiin` | 5 | [n/a] | [n/a] | `apocini` | [n/a] | [n/a] | [n/a] |
| `oteos` | 5 | [n/a] | [n/a] | `osteo` | [n/a] | [n/a] | [n/a] |
| `olkar` | 5 | [n/a] | [n/a] | `carlo` | [n/a] | `calor` | warmth, glow |
| `qokep` | 4 | `pecco` | [n/a] | `pecco` | [n/a] | [n/a] | [n/a] |
| `okaiin` | 4 | `coniai` | [n/a] | `coniai` | [n/a] | [n/a] | [n/a] |
| `qotaiin` | 4 | `coniati` | [n/a] | `cationi` | [n/a] | `aconiti` | without dust (literally) |
| `qokaiin` | 3 | `conciai` | [n/a] | `ciancio` | [n/a] | [n/a] | [n/a] |
| `qokar` | 3 | [n/a] | [n/a] | `carco` | [n/a] | [n/a] | [n/a] |
| `olaiin` | 3 | [n/a] | [n/a] | `ialino` | hyaline, glassy | [n/a] | [n/a] |
| `olchep` | 3 | `colpe` | [n/a] | `colpe` | [n/a] | [n/a] | [n/a] |
| `qokeop` | 3 | [n/a] | [n/a] | `copeco` | kopek | [n/a] | [n/a] |
| `oraiin` | 3 | `ironia` | irony | `aironi` | [n/a] | [n/a] | [n/a] |
| `olkaiin` | 3 | [n/a] | [n/a] | `caolini` | [n/a] | [n/a] | [n/a] |
| `otair` | 3 | `atrio` | entrance hall, lobby (of a hotel etc.) | `atrio` | entrance hall, lobby (of a hotel etc.) | `ratio` | plan |

### text_only
| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |
|---|---:|---|---|---|---|---|---|
| `paiin` | 42 | `piani` | plans (arrangements) | `piani` | plans (arrangements) | [n/a] | [n/a] |
| `qokal` | 31 | `calco` | cast (of sculpture) | `calco` | cast (of sculpture) | `accol` | one who lives nearby/beside |
| `qokar` | 31 | [n/a] | [n/a] | `carco` | [n/a] | [n/a] | [n/a] |
| `qokaiin` | 25 | `conciai` | [n/a] | `ciancio` | [n/a] | [n/a] | [n/a] |
| `kaiin` | 24 | [n/a] | [n/a] | `acini` | [n/a] | [n/a] | [n/a] |
| `qokep` | 13 | `pecco` | [n/a] | `pecco` | [n/a] | [n/a] | [n/a] |
| `okaiin` | 12 | `coniai` | [n/a] | `coniai` | [n/a] | [n/a] | [n/a] |
| `opaiin` | 11 | `opinai` | [n/a] | `inopia` | poverty | [n/a] | [n/a] |
| `qokain` | 10 | `concia` | tanning | `acconi` | [n/a] | `cocain` | [n/a] |
| `okain` | 10 | `conia` | [n/a] | `acino` | a berry | [n/a] | [n/a] |
| `saiin` | 10 | `asini` | [n/a] | `asini` | [n/a] | [n/a] | [n/a] |
| `qotal` | 9 | `colta` | [n/a] | `colta` | [n/a] | `calot` | [n/a] |
| `qotaiin` | 8 | `coniati` | [n/a] | `cationi` | [n/a] | `aconiti` | without dust (literally) |
| `qotar` | 8 | `corta` | [n/a] | `corta` | [n/a] | `actor` | advocate |
| `otain` | 7 | `notai` | [n/a] | `anito` | [n/a] | `natio` | birth |
| `qopar` | 7 | `copra` | [n/a] | `capro` | male goat | [n/a] | [n/a] |
| `qotain` | 6 | `antico` | ancient | `antico` | ancient | `aconit` | aconite as a poison |
| `qokair` | 6 | `carico` | loaded, laden | `accori` | [n/a] | `cicaro` | [n/a] |
| `olkar` | 6 | [n/a] | [n/a] | `carlo` | [n/a] | `calor` | warmth, glow |
| `olaiin` | 5 | [n/a] | [n/a] | `ialino` | hyaline, glassy | [n/a] | [n/a] |

### unknown
| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |
|---|---:|---|---|---|---|---|---|
| `paiin` | 241 | `piani` | plans (arrangements) | `piani` | plans (arrangements) | [n/a] | [n/a] |
| `qokaiin` | 122 | `conciai` | [n/a] | `ciancio` | [n/a] | [n/a] | [n/a] |
| `okaiin` | 109 | `coniai` | [n/a] | `coniai` | [n/a] | [n/a] | [n/a] |
| `qokain` | 101 | `concia` | tanning | `acconi` | [n/a] | `cocain` | [n/a] |
| `okain` | 69 | `conia` | [n/a] | `acino` | a berry | [n/a] | [n/a] |
| `qokep` | 65 | `pecco` | [n/a] | `pecco` | [n/a] | [n/a] | [n/a] |
| `otain` | 54 | `notai` | [n/a] | `anito` | [n/a] | `natio` | birth |
| `qokar` | 48 | [n/a] | [n/a] | `carco` | [n/a] | [n/a] | [n/a] |
| `saiin` | 48 | `asini` | [n/a] | `asini` | [n/a] | [n/a] | [n/a] |
| `qokal` | 46 | `calco` | cast (of sculpture) | `calco` | cast (of sculpture) | `accol` | one who lives nearby/beside |
| `kaiin` | 45 | [n/a] | [n/a] | `acini` | [n/a] | [n/a] | [n/a] |
| `qotaiin` | 40 | `coniati` | [n/a] | `cationi` | [n/a] | `aconiti` | without dust (literally) |
| `lkaiin` | 40 | `canili` | [n/a] | `ancili` | [n/a] | `lacini` | strip/rag of cloth |
| `qokeol` | 38 | [n/a] | [n/a] | `eccolo` | [n/a] | [n/a] | [n/a] |
| `qotain` | 34 | `antico` | ancient | `antico` | ancient | `aconit` | aconite as a poison |
| `opaiin` | 32 | `opinai` | [n/a] | `inopia` | poverty | [n/a] | [n/a] |
| `oteop` | 31 | [n/a] | [n/a] | `poeto` | [n/a] | [n/a] | [n/a] |
| `qotar` | 29 | `corta` | [n/a] | `corta` | [n/a] | `actor` | advocate |
| `opchep` | 29 | [n/a] | [n/a] | `ceppo` | stump (of a tree) | [n/a] | [n/a] |
| `olaiin` | 29 | [n/a] | [n/a] | `ialino` | hyaline, glassy | [n/a] | [n/a] |

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

After building pages, generate per-line outputs and plain-text READMEs:

```sh
python scripts/generate_recipes.py
python scripts/render_recipes_text.py --group-by-domain
```

Quick links: `data/recipe_readmes/README.md`, `data/recipes/index.json`.

## Images

Download page images from `voynich.nu` into `data/images/`:

```sh
python scripts/download_images.py
```
