#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


FOLIOS_URL = "https://www.voynich.nu/folios.html"
UA = "voynich-recipe-research-bot/0.1 (+https://www.voynich.nu/)"


def fetch_folios_html(dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "-L",
            "-A",
            UA,
            "-H",
            "Accept: text/html,*/*;q=0.8",
            "-o",
            str(dest),
            FOLIOS_URL,
        ],
        check=True,
    )


def parse_thumbnail_paths(html: str) -> list[str]:
    # Example: q01/f001r_th.jpg
    paths = re.findall(r'IMG\s+SRC="(q\d{2}/f[^"]+?_th\.jpg)"', html, flags=re.IGNORECASE)
    # Deduplicate preserving order
    seen = set()
    out = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def thumb_to_full(p: str) -> str:
    # Preferred: _crd.jpg (used on quire pages)
    return p.replace("_th.jpg", "_crd.jpg")


def curl_download(url: str, out_path: Path) -> bool:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    cmd = [
        "curl",
        "-L",
        "-f",
        "-A",
        UA,
        "-H",
        "Accept: image/jpeg,image/*;q=0.8,*/*;q=0.5",
        "-o",
        str(tmp),
        url,
    ]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        return False
    tmp.replace(out_path)
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download voynich.nu page images for all folios listed in folios.html.")
    ap.add_argument("--out-dir", default="data/images", help="Output directory for downloaded images.")
    ap.add_argument("--force", action="store_true", help="Re-download everything.")
    ap.add_argument("--limit", type=int, default=0, help="Download only first N images (debug).")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    cache_html = out_dir / "_cache" / "folios.html"
    fetch_folios_html(cache_html, force=args.force)
    html = cache_html.read_text(encoding="utf-8", errors="replace")

    thumbs = parse_thumbnail_paths(html)
    if args.limit:
        thumbs = thumbs[: args.limit]

    ok = 0
    failed = 0
    skipped = 0
    for rel_thumb in thumbs:
        rel_full = thumb_to_full(rel_thumb)
        url = f"https://www.voynich.nu/{rel_full}"
        out_path = out_dir / rel_full
        if out_path.exists() and not args.force:
            skipped += 1
            continue
        if curl_download(url, out_path):
            ok += 1
        else:
            failed += 1
            print(f"FAILED {url}", file=sys.stderr)

    print(f"Downloaded: {ok}, skipped: {skipped}, failed: {failed} -> {out_dir}", file=sys.stderr)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

