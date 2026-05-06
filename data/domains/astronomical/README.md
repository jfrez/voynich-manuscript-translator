# Domain: astronomical

## What we know (in this repo)
- This domain label comes from IVTFF page metadata (`section`).
- It does not imply any semantic decipherment of the Voynich text.
- READMEs in this repo show EVA transliteration + a procedural gloss (not a translation).

## Summary stats
- folios: 8
- EVA word tokens (approx): 962
- top procedural compounds: [('mix/transfer', 654), ('yeast fermentation', 338), ('main herb', 289), ('sugars', 242), ('heat', 156), ('secondary herb', 67), ('complex herbal compound', 43), ('liquid base', 34)]

## Domain-specific marker meanings (requested; speculative)
Below is the requested meaning assignment for token markers, annotated with how often the corresponding marker-class appears in this domain.
This is **not** a validated translation; it is a procedural interpretation layer.

### Action / ingredient markers
- `qo` = liquid base / must / water (prevalence 3.5%)
- `q` = general base marker (prevalence 0.4%)
- `o` = mix / transfer / continuity (prevalence 68.0%)
- `k` = sugars / fermentables (prevalence 25.2%)
- `t` = heat / cooking (prevalence 16.2%)
- `p` = yeast / fermentation start (prevalence 35.1%)
- `ch` = main plant (always substituted with a safe edible plant) (prevalence 30.0%)
- `sh` = secondary herb (safe edible) (prevalence 7.0%)
- `f` = aroma modifier (prevalence 0.7%)
- `cth/ckh/cph/cfh` = complex herbal compound (safe blend) (prevalence 4.5%)

Connectors (low semantic weight, used as transitions):
- `l, r, n, s, m` = connectors (low semantic weight transitions)

### State / time markers
We treat the first vowel-run found in a word as an intensity/state cue:
- `e…` = active extraction (prevalence 41.2%)
- `i…` = cooling/rest (prevalence 1.5%)
- `a…` = fermentation start/transition (prevalence 25.9%)

Run length encodes level:
- level 1 = e / i / a (prevalence 51.7%)
- level 2 = ee / ii (prevalence 14.7%)
- level 3 = eee / iii (prevalence 2.2%)

## Folios
- f67v1: ../../recipe_readmes/f67v1/README.md
- f68r1: ../../recipe_readmes/f68r1/README.md
- f68r2: ../../recipe_readmes/f68r2/README.md
- f68r3: ../../recipe_readmes/f68r3/README.md
- f68v2: ../../recipe_readmes/f68v2/README.md
- f68v1: ../../recipe_readmes/f68v1/README.md
- f67r1: ../../recipe_readmes/f67r1/README.md
- f67r2: ../../recipe_readmes/f67r2/README.md
