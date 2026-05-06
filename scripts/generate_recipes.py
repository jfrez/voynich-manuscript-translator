#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.recipe_model import generate_recipe  # noqa: E402


def _merge_pantry_max(pantry: dict, ingredients: dict) -> dict:
    """
    Combine ingredients across recipes into a "max-needed" pantry for running any single line-recipe.
    Numeric fields are max(); strings are collected as a set (rendered as sorted lists).
    """
    out = dict(pantry)
    for k, v in (ingredients or {}).items():
        if v is None:
            continue
        if isinstance(v, (int, float)):
            prev = out.get(k)
            if isinstance(prev, (int, float)):
                out[k] = max(prev, v)
            else:
                out[k] = v
        elif isinstance(v, str):
            prev = out.get(k)
            if prev is None:
                out[k] = {v}
            elif isinstance(prev, set):
                prev.add(v)
                out[k] = prev
            else:
                out[k] = {str(prev), v}
        else:
            out.setdefault(k, v)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Generate speculative procedural 'recipes' (generic processes) per folio from EVA.")
    ap.add_argument("--pages-dir", default="data/pages", help="Input directory produced by scripts/build_pages.py")
    ap.add_argument("--out-dir", default="data/recipes", help="Output directory for per-folio recipe JSON")
    ap.add_argument("--limit", type=int, default=0, help="If set, only generate first N folios (debug).")
    args = ap.parse_args(argv)

    pages_dir = pathlib.Path(args.pages_dir)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    index_path = pages_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))

    out_index: list[dict] = []
    count = 0
    for meta in index:
        folio = meta["folio"]
        page_json = pages_dir / f"{folio}.json"
        if not page_json.exists():
            continue
        payload = json.loads(page_json.read_text(encoding="utf-8"))
        eva_text = payload.get("eva_text", "")
        plant_cat = payload.get("plant_category_guess", "unknown")
        plant_conf = payload.get("plant_category_confidence", 0.0)
        plant_matches = payload.get("plant_category_matches", [])
        plant_candidates = payload.get("plant_candidates", [])

        # Treat each IVTFF locus line as an independent recipe (small experimental batch).
        line_recipes = []
        pantry_max: dict = {}
        for loc in payload.get("loci", []):
            line_eva = (loc.get("eva") or "").strip()
            if not line_eva:
                continue
            line_recipe = generate_recipe(line_eva, plant_category_guess=plant_cat, batch_l=0.5)
            line_recipe["plant_interpretation"] = {
                "category": plant_cat,
                "confidence": plant_conf,
                "textual_evidence_terms": plant_matches,
                "note": (
                    "Heuristic classification based on the IVTFF 'Plant ID' string (not the drawing). "
                    "Does not imply real identification of the manuscript plant."
                ),
            }
            line_recipes.append({"locus": loc.get("locus"), "eva_line": line_eva, "recipe": line_recipe})
            pantry_max = _merge_pantry_max(pantry_max, line_recipe.get("ingredients", {}))

        pantry_out = {}
        for k, v in pantry_max.items():
            pantry_out[k] = sorted(v) if isinstance(v, set) else v

        # Page-level summary (not a "single recipe"): aggregated procedural cues from the full page text.
        page_summary = generate_recipe(eva_text, plant_category_guess=plant_cat, batch_l=2.0) if eva_text else {}
        if page_summary:
            page_summary.pop("parsing", None)
            page_summary.pop("process", None)
            page_summary.pop("ingredients", None)

        out_payload = {
            "folio": folio,
            "page_number": payload.get("page_number"),
            "section": payload.get("section"),
            "currier": payload.get("currier"),
            "plant_id": payload.get("plant_id"),
            "plant_candidates": plant_candidates,
            "plant_category_guess": plant_cat,
            "plant_category_confidence": plant_conf,
            "plant_category_matches": plant_matches,
            "source": {
                "transliteration": "IVTFF/EVA (ZL file as downloaded by scripts/build_pages.py)",
                "pages_file": str(page_json),
            },
            "page_pantry_max_per_line_recipe": pantry_out,
            "page_summary_procedural": page_summary,
            "line_recipes": line_recipes,
        }

        (out_dir / f"{folio}.recipe.json").write_text(
            json.dumps(out_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        out_index.append(
            {
                "folio": folio,
                "section": payload.get("section"),
                "plant_id": payload.get("plant_id"),
                "plant_candidates": plant_candidates,
                "plant_category_guess": plant_cat,
                "recipe_file": f"{folio}.recipe.json",
            }
        )

        count += 1
        if args.limit and count >= args.limit:
            break

    (out_dir / "index.json").write_text(json.dumps(out_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(out_index)} recipe files -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
