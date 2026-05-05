#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from voynich.ivtff import classify_plant_category, extract_plant_candidates, parse_ivtff_lines


DEFAULT_URL = "https://www.voynich.nu/data/ZL3b-n.txt"


def download(url: str, dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "voynich-recipe-research-bot/0.1 (+https://www.voynich.nu/)",
            "Accept": "text/plain,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req) as r:
        data = r.read()
    dest.write_bytes(data)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download + split IVTFF transliteration into per-folio files.")
    ap.add_argument("--url", default=DEFAULT_URL, help="IVTFF transliteration URL (default: ZL3b-n.txt from voynich.nu).")
    ap.add_argument("--raw-out", default="data/raw/ZL3b-n.txt", help="Where to save the downloaded IVTFF file.")
    ap.add_argument("--out-dir", default="data/pages", help="Output directory for per-folio JSON/TXT.")
    ap.add_argument("--force-download", action="store_true", help="Re-download even if raw-out exists.")
    args = ap.parse_args(argv)

    raw_path = pathlib.Path(args.raw_out)
    out_dir = pathlib.Path(args.out_dir)

    if args.force_download or not raw_path.exists():
        print(f"Downloading {args.url} -> {raw_path}", file=sys.stderr)
        download(args.url, raw_path)

    print(f"Parsing {raw_path}", file=sys.stderr)
    records = list(parse_ivtff_lines(raw_path.read_text(encoding="utf-8", errors="replace").splitlines(True)))

    out_dir.mkdir(parents=True, exist_ok=True)

    index: list[dict] = []
    for rec in records:
        category, confidence, matches = classify_plant_category(rec.plant_id, section=rec.section)
        candidates = extract_plant_candidates(rec.plant_id)
        meta = {
            "folio": rec.folio,
            "page_number": rec.page_number,
            "section": rec.section,
            "currier": rec.currier,
            "plant_id": rec.plant_id,
            "plant_candidates": candidates,
            "plant_category_guess": category,
            "plant_category_confidence": confidence,
            "plant_category_matches": matches,
            "refs": rec.refs,
            "notes": rec.notes,
            "loci_count": len(rec.loci),
        }
        index.append(meta)

        (out_dir / f"{rec.folio}.eva.txt").write_text(rec.eva_text + ("\n" if rec.eva_text else ""), encoding="utf-8")
        (out_dir / f"{rec.folio}.json").write_text(
            json.dumps(
                {
                    **meta,
                    "loci": rec.loci,
                    "eva_text": rec.eva_text,
                    "disclaimer": (
                        "This dataset is a transliteration (IVTFF/EVA) and does not imply a validated translation. "
                        "Any downstream 'recipe' interpretations are speculative/procedural."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    (out_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} folios -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
