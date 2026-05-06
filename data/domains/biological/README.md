# Domain: biological

## What we know (in this repo)
- This domain label comes from IVTFF page metadata (`section`).
- It does not imply any semantic decipherment of the Voynich text.
- READMEs in this repo show EVA transliteration + a procedural gloss (not a translation).

## Summary stats
- folios: 19
- EVA word tokens (approx): 6569
- top procedural compounds: [('yeast fermentation', 2785), ('mix/transfer', 2289), ('sugars', 1926), ('liquid base', 1534), ('main herb', 1360), ('secondary herb', 998), ('heat', 832), ('complex herbal compound', 307)]

## Domain-specific marker meanings (requested; speculative)
Below is the requested meaning assignment for token markers, annotated with how often the corresponding marker-class appears in this domain.
This is **not** a validated translation; it is a procedural interpretation layer.

### Action / ingredient markers
- `qo` = liquid base / must / water (prevalence 23.4%)
- `q` = general base marker (prevalence 0.5%)
- `o` = mix / transfer / continuity (prevalence 34.8%)
- `k` = sugars / fermentables (prevalence 29.3%)
- `t` = heat / cooking (prevalence 12.7%)
- `p` = yeast / fermentation start (prevalence 42.4%)
- `ch` = main plant (always substituted with a safe edible plant) (prevalence 20.7%)
- `sh` = secondary herb (safe edible) (prevalence 15.2%)
- `f` = aroma modifier (prevalence 0.5%)
- `cth/ckh/cph/cfh` = complex herbal compound (safe blend) (prevalence 4.7%)

Connectors (low semantic weight, used as transitions):
- `l, r, n, s, m` = connectors (low semantic weight transitions)

### State / time markers
We treat the first vowel-run found in a word as an intensity/state cue:
- `e…` = active extraction (prevalence 45.3%)
- `i…` = cooling/rest (prevalence 0.9%)
- `a…` = fermentation start/transition (prevalence 26.3%)

Run length encodes level:
- level 1 = e / i / a (prevalence 59.1%)
- level 2 = ee / ii (prevalence 12.8%)
- level 3 = eee / iii (prevalence 0.6%)

## Folios
- f75r: ../../recipe_readmes/f75r/README.md
- f75v: ../../recipe_readmes/f75v/README.md
- f76v: ../../recipe_readmes/f76v/README.md
- f77r: ../../recipe_readmes/f77r/README.md
- f77v: ../../recipe_readmes/f77v/README.md
- f78r: ../../recipe_readmes/f78r/README.md
- f78v: ../../recipe_readmes/f78v/README.md
- f79r: ../../recipe_readmes/f79r/README.md
- f79v: ../../recipe_readmes/f79v/README.md
- f80r: ../../recipe_readmes/f80r/README.md
- f80v: ../../recipe_readmes/f80v/README.md
- f81r: ../../recipe_readmes/f81r/README.md
- f81v: ../../recipe_readmes/f81v/README.md
- f82r: ../../recipe_readmes/f82r/README.md
- f82v: ../../recipe_readmes/f82v/README.md
- f83r: ../../recipe_readmes/f83r/README.md
- f83v: ../../recipe_readmes/f83v/README.md
- f84r: ../../recipe_readmes/f84r/README.md
- f84v: ../../recipe_readmes/f84v/README.md
