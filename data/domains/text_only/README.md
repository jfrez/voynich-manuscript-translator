# Domain: text only

## What we know (in this repo)
- This domain label comes from IVTFF page metadata (`section`).
- It does not imply any semantic decipherment of the Voynich text.
- READMEs in this repo show EVA transliteration + a procedural gloss (not a translation).

## Summary stats
- folios: 8
- EVA word tokens (approx): 3240
- top procedural compounds: [('mix/transfer', 1406), ('yeast fermentation', 1125), ('sugars', 789), ('main herb', 692), ('heat', 487), ('secondary herb', 440), ('liquid base', 426), ('complex herbal compound', 156)]

## Domain-specific marker meanings (requested; speculative)
Below is the requested meaning assignment for token markers, annotated with how often the corresponding marker-class appears in this domain.
This is **not** a validated translation; it is a procedural interpretation layer.

### Action / ingredient markers
- `qo` = liquid base / must / water (prevalence 13.1%)
- `q` = general base marker (prevalence 0.3%)
- `o` = mix / transfer / continuity (prevalence 43.4%)
- `k` = sugars / fermentables (prevalence 24.4%)
- `t` = heat / cooking (prevalence 15.0%)
- `p` = yeast / fermentation start (prevalence 34.7%)
- `ch` = main plant (always substituted with a safe edible plant) (prevalence 21.4%)
- `sh` = secondary herb (safe edible) (prevalence 13.6%)
- `f` = aroma modifier (prevalence 1.5%)
- `cth/ckh/cph/cfh` = complex herbal compound (safe blend) (prevalence 4.8%)

Connectors (low semantic weight, used as transitions):
- `l, r, n, s, m` = connectors (low semantic weight transitions)

### State / time markers
We treat the first vowel-run found in a word as an intensity/state cue:
- `e…` = active extraction (prevalence 28.5%)
- `i…` = cooling/rest (prevalence 0.8%)
- `a…` = fermentation start/transition (prevalence 41.9%)

Run length encodes level:
- level 1 = e / i / a (prevalence 63.8%)
- level 2 = ee / ii (prevalence 6.8%)
- level 3 = eee / iii (prevalence 0.6%)

## Folios
- f1r: ../../recipe_readmes/f1r/README.md
- f58r: ../../recipe_readmes/f58r/README.md
- f58v: ../../recipe_readmes/f58v/README.md
- f66r: ../../recipe_readmes/f66r/README.md
- f76r: ../../recipe_readmes/f76r/README.md
- f85r1: ../../recipe_readmes/f85r1/README.md
- f86v6: ../../recipe_readmes/f86v6/README.md
- f86v5: ../../recipe_readmes/f86v5/README.md
