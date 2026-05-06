#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


IRIS_HANDLE_URL = "https://iris.cnr.it/handle/20.500.14243/390952"
UA = "voynich-recipe-research-bot/0.1"


def curl_text(url: str) -> str:
    r = subprocess.run(
        ["curl", "-L", "-A", UA, "-H", "Accept: text/html,*/*;q=0.8", url],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return r.stdout


def download(url: str, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "curl",
            "-L",
            "-f",
            "-A",
            UA,
            "-H",
            "Accept: application/pdf,*/*;q=0.8",
            "-o",
            str(out),
            url,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download the open-access TLIO 2019 PDF volumes from IRIS CNR.")
    ap.add_argument("--out-dir", default="data/lexicon/tlio2019", help="Output directory for TLIO PDF volumes.")
    ap.add_argument("--force", action="store_true", help="Re-download PDFs even if present.")
    ap.add_argument("--limit", type=int, default=0, help="Download only first N PDFs (debug).")
    args = ap.parse_args(argv)

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    html = curl_text(IRIS_HANDLE_URL)
    # Extract all retrieve/.../prod_...pdf links (absolute or relative)
    rels = re.findall(r"(/retrieve/[^\"]+?/prod_[^\"\\s]+?\\.pdf)", html, flags=re.IGNORECASE)
    abss = re.findall(r"(https://iris\.cnr\.it/retrieve/[^\"]+?/prod_[^\"\\s]+?\\.pdf)", html, flags=re.IGNORECASE)
    urls = [f"https://iris.cnr.it{p}" for p in rels] + abss
    # Dedup preserving order
    seen = set()
    uniq = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        uniq.append(u)
    urls = uniq

    if not urls:
        print("No PDF URLs found on IRIS page (structure may have changed).", file=sys.stderr)
        return 2

    if args.limit:
        urls = urls[: args.limit]

    ok = 0
    for i, url in enumerate(urls, start=1):
        name = pathlib.Path(url).name
        out = out_dir / f"{i:02d}_{name}"
        if out.exists() and not args.force:
            ok += 1
            continue
        print(f"[{i}/{len(urls)}] {name}", file=sys.stderr)
        download(url, out)
        ok += 1

    print(f"Downloaded {ok} TLIO PDFs -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
