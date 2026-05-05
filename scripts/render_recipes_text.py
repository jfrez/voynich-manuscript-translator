#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import os
import re
import sys


def format_kv_block(title: str, mapping: dict) -> str:
    lines = [f"## {title}"]
    for k in sorted(mapping.keys()):
        v = mapping[k]
        if v is None or v == "" or v == [] or v == {}:
            continue
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _normalize_folio_from_image_basename(name: str) -> str:
    # Examples:
    # - f001r -> f1r
    # - f010v -> f10v
    # - f102r1 -> f102r1 (no zero padding)
    m = re.match(r"^f(\d+)([rv].*)$", name)
    if not m:
        return name
    num = str(int(m.group(1)))
    return f"f{num}{m.group(2)}"


def build_folio_image_map(images_dir: pathlib.Path) -> dict[str, pathlib.Path]:
    """
    Build mapping folio -> image path using the cached folios.html if available.
    Falls back to scanning *_crd.jpg files.
    """
    mapping: dict[str, pathlib.Path] = {}
    cache = images_dir / "_cache" / "folios.html"
    if cache.exists():
        html = cache.read_text(encoding="utf-8", errors="replace")
        for rel_thumb in re.findall(r'IMG\s+SRC="(q\d{2}/f[^"]+?_th\.jpg)"', html, flags=re.IGNORECASE):
            rel_full = rel_thumb.replace("_th.jpg", "_crd.jpg")
            base = pathlib.Path(rel_full).name.replace("_crd.jpg", "")
            folio = _normalize_folio_from_image_basename(base)
            mapping[folio] = images_dir / rel_full
    else:
        for p in images_dir.glob("q*/f*_crd.jpg"):
            base = p.name.replace("_crd.jpg", "")
            folio = _normalize_folio_from_image_basename(base)
            mapping.setdefault(folio, p)
    return mapping


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Render per-folio recipe JSON into plain-text (Markdown) README files.")
    ap.add_argument("--recipes-dir", default="data/recipes", help="Input directory produced by scripts/generate_recipes.py")
    ap.add_argument("--out-dir", default="data/recipe_readmes", help="Output directory with one README per folio")
    ap.add_argument("--images-dir", default="data/images", help="Directory produced by scripts/download_images.py")
    ap.add_argument("--limit", type=int, default=0, help="If set, only render first N (debug).")
    args = ap.parse_args(argv)

    recipes_dir = pathlib.Path(args.recipes_dir)
    out_dir = pathlib.Path(args.out_dir)
    images_dir = pathlib.Path(args.images_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    index = json.loads((recipes_dir / "index.json").read_text(encoding="utf-8"))
    folio_images = build_folio_image_map(images_dir) if images_dir.exists() else {}

    rendered = 0
    for meta in index:
        folio = meta["folio"]
        recipe_path = recipes_dir / meta["recipe_file"]
        obj = json.loads(recipe_path.read_text(encoding="utf-8"))

        # New schema: one page contains multiple line-recipes.
        line_recipes = obj.get("line_recipes", [])
        page_pantry = obj.get("page_pantry_max_per_line_recipe", {})
        page_summary = obj.get("page_summary_procedural", {})

        # Plant interpretation: take from first line recipe if present, otherwise fallback
        plant_interp = {}
        if line_recipes and isinstance(line_recipes[0], dict):
            plant_interp = (line_recipes[0].get("recipe", {}) or {}).get("plant_interpretation", {}) or {}

        header = [
            f"# Voynich Speculative Herbal Ferment Recipe — {folio}",
            "",
            (line_recipes[0].get("recipe", {}).get("disclaimer", "") if line_recipes else "").strip(),
            "",
            "This file is generated automatically from IVTFF/EVA transliteration plus a user-defined procedural grammar.",
        ]

        page_meta = {
            "folio": obj.get("folio"),
            "page_number": obj.get("page_number"),
            "section": obj.get("section"),
            "currier": obj.get("currier"),
            "plant_id": obj.get("plant_id"),
            "plant_candidates": obj.get("plant_candidates"),
            "plant_category_guess": obj.get("plant_category_guess"),
            "plant_category_confidence": obj.get("plant_category_confidence"),
            "plant_category_matches": obj.get("plant_category_matches"),
        }

        parts: list[str] = []
        parts.append("\n".join(header))

        folio_dir = out_dir / folio
        folio_dir.mkdir(parents=True, exist_ok=True)
        img_path = folio_images.get(folio)
        if img_path and img_path.exists():
            rel = os.path.relpath(img_path, start=folio_dir)
            parts.append(f"![{folio}]({rel})")

        parts.append(format_kv_block("Page / Folio", page_meta))
        parts.append(format_kv_block("Plant Interpretation (Heuristic)", plant_interp))

        eva_text = obj.get("source", {}).get("pages_file")
        # Also include the EVA text as found in the page payload (if present)
        page_payload = None
        try:
            pages_file = obj.get("source", {}).get("pages_file")
            if pages_file:
                page_payload = json.loads(pathlib.Path(pages_file).read_text(encoding="utf-8"))
        except Exception:
            page_payload = None
        if page_payload and page_payload.get("eva_text"):
            parts.append("## EVA Text (Transliteration)\n" + page_payload["eva_text"].strip())
        if page_summary:
            parts.append(format_kv_block("Page Summary (Procedural, Aggregated)", page_summary.get("procedural_summary", {})))

        parts.append(format_kv_block("Pantry (Max Needed For Any Single Line-Recipe)", page_pantry))

        # Render each line as its own recipe
        if line_recipes:
            blocks = ["## Line Recipes (Each Line = One Recipe, 0.5L batch)"]
            for i, lr in enumerate(line_recipes, start=1):
                locus = lr.get("locus", f"line_{i}")
                eva_line = lr.get("eva_line", "")
                recipe = lr.get("recipe", {}) or {}
                blocks.append(f"### {locus}")
                if eva_line:
                    blocks.append(f"EVA: {eva_line}")
                blocks.append(format_kv_block("Ingredients", recipe.get("ingredients", {})))
                process = recipe.get("process", [])
                if process:
                    blocks.append("Process:\n" + "\n".join(f"{j+1}. {step}" for j, step in enumerate(process)))
                blocks.append(f"Expected Result: {recipe.get('expected_result','')}".rstrip())
                blocks.append(f"Does It Make Sense?: {recipe.get('does_it_make_sense','')}".rstrip())
                parsing = recipe.get("parsing", [])
                if parsing:
                    blocks.append(
                        "Direct Gloss (Procedural, Not a Real Translation):\n"
                        + "\n".join(f"- {p.get('word')}: {p.get('interpretation')}" for p in parsing)
                    )
            parts.append("\n\n".join(blocks))

        # Page-level safety notes: re-use standard warnings (from first line) to avoid repetition.
        if line_recipes:
            first = line_recipes[0].get("recipe", {}) or {}
            risks = first.get("risks", [])
            if risks:
                parts.append("## Risks & Warnings (Applies To All Line-Recipes)\n" + "\n".join(f"- {r}" for r in risks))
            adj = first.get("recommended_adjustments", [])
            if adj:
                parts.append("## Recommended Adjustments (General)\n" + "\n".join(f"- {a}" for a in adj))

        readme = "\n\n".join(parts).strip() + "\n"

        (folio_dir / "README.md").write_text(readme, encoding="utf-8")

        rendered += 1
        if args.limit and rendered >= args.limit:
            break

    # Root index for convenience
    root_index_lines = [
        "# Recipe Readmes (Generated)",
        "",
        "One folder per folio, containing `README.md`.",
        "",
    ]
    for meta in index[: rendered if args.limit else len(index)]:
        folio = meta["folio"]
        root_index_lines.append(f"- {folio}: {folio}/README.md")
    (out_dir / "README.md").write_text("\n".join(root_index_lines) + "\n", encoding="utf-8")

    print(f"Wrote {rendered} README files -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
