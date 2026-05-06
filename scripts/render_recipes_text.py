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


def build_folio_image_map(images_dir: pathlib.Path) -> dict[str, list[pathlib.Path]]:
    """
    Build mapping folio -> image path using the cached folios.html if available.
    Falls back to scanning *_crd.jpg files.
    """
    mapping: dict[str, list[pathlib.Path]] = {}
    cache = images_dir / "_cache" / "folios.html"
    if cache.exists():
        html = cache.read_text(encoding="utf-8", errors="replace")
        for rel_thumb in re.findall(r'IMG\s+SRC="(q\d{2}/f[^"]+?_th\.jpg)"', html, flags=re.IGNORECASE):
            rel_full = rel_thumb.replace("_th.jpg", "_crd.jpg")
            base = pathlib.Path(rel_full).name.replace("_crd.jpg", "")
            folio = _normalize_folio_from_image_basename(base)
            p = images_dir / rel_full
            mapping.setdefault(folio, []).append(p)
            # If the image is a split page like f101v1/f101v2, also map to base folio f101v.
            if re.match(r"^f\d+[rv]\d+$", folio):
                base_folio = re.sub(r"(\d+)$", "", folio)
                mapping.setdefault(base_folio, []).append(p)
    else:
        for p in images_dir.glob("q*/f*_crd.jpg"):
            base = p.name.replace("_crd.jpg", "")
            folio = _normalize_folio_from_image_basename(base)
            mapping.setdefault(folio, []).append(p)
            if re.match(r"^f\d+[rv]\d+$", folio):
                base_folio = re.sub(r"(\d+)$", "", folio)
                mapping.setdefault(base_folio, []).append(p)
    # Sort for stable output
    for k, v in mapping.items():
        mapping[k] = sorted(set(v), key=lambda x: str(x))
    return mapping


def _safe_anchor_id(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "recipe"


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
    index_entries: list[dict] = []
    for meta in index:
        folio = meta["folio"]
        recipe_path = recipes_dir / meta["recipe_file"]
        obj = json.loads(recipe_path.read_text(encoding="utf-8"))

        # New schema: one page contains multiple line-recipes.
        line_recipes = obj.get("line_recipes", [])

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
        }

        parts: list[str] = []
        parts.append("\n".join(header))

        folio_dir = out_dir / folio
        folio_dir.mkdir(parents=True, exist_ok=True)
        img_paths = folio_images.get(folio, [])
        img_paths = [p for p in img_paths if p.exists()]
        if img_paths:
            for p in img_paths:
                rel = os.path.relpath(p, start=folio_dir)
                parts.append(f"![{folio}]({rel})")
        else:
            parts.append("_Image not found for this folio in `data/images/`._")

        parts.append(format_kv_block("Page / Folio", page_meta))

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
            eva_block = page_payload["eva_text"].rstrip("\n")
            parts.append("## EVA Text (Transliteration)\n```text\n" + eva_block + "\n```")
        # Intentionally omit any speculative aggregation (summary/pantry/plant heuristics) from READMEs.

        # Render each line as its own recipe
        if line_recipes:
            idx_lines = ["## Recipes Index (This Page)"]
            line_links = []
            for i, lr in enumerate(line_recipes, start=1):
                locus = lr.get("locus", f"line_{i}")
                anchor = _safe_anchor_id(f"{folio}-{i}-{locus}")
                idx_lines.append(f"- [{locus}](#{anchor})")
                line_links.append({"locus": locus, "path": f"{folio}/README.md#{anchor}"})
            parts.append("\n".join(idx_lines))

            blocks = ["## Line Glosses (Procedural Gloss Only; Not a Translation)"]
            for i, lr in enumerate(line_recipes, start=1):
                locus = lr.get("locus", f"line_{i}")
                anchor = _safe_anchor_id(f"{folio}-{i}-{locus}")
                eva_line = lr.get("eva_line", "")
                recipe = lr.get("recipe", {}) or {}
                blocks.append(f'<a id="{anchor}"></a>')
                blocks.append(f"### {locus}")
                if eva_line:
                    blocks.append(f"EVA: {eva_line}")
                parsing = recipe.get("parsing", [])
                if parsing:
                    blocks.append(
                        "Direct Gloss (Procedural, Not a Real Translation):\n"
                        + "\n".join(f"- {p.get('word')}: {p.get('interpretation')}" for p in parsing)
                    )
                else:
                    blocks.append("Direct Gloss (Procedural, Not a Real Translation):\n- [no parsed tokens]")
            parts.append("\n\n".join(blocks))

        # Intentionally omit speculative recipe instantiation (ingredients/process/etc.) from READMEs.
        # Keep only the procedural gloss; full speculative outputs remain in JSON.

        readme = "\n\n".join(parts).strip() + "\n"

        (folio_dir / "README.md").write_text(readme, encoding="utf-8")

        index_entries.append({"folio": folio, "readme": f"{folio}/README.md", "lines": line_links if line_recipes else []})

        rendered += 1
        if args.limit and rendered >= args.limit:
            break

    # Root index for convenience
    root_index_lines = [
        "# Recipe Readmes (Generated)",
        "",
        "One folder per folio, containing `README.md` with linkable line-recipes.",
        "",
    ]
    for entry in index_entries:
        root_index_lines.append(f"- {entry['folio']}: {entry['readme']}")
        for lr in entry["lines"]:
            root_index_lines.append(f"  - {lr['locus']}: {lr['path']}")
    (out_dir / "README.md").write_text("\n".join(root_index_lines) + "\n", encoding="utf-8")

    print(f"Wrote {rendered} README files -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
