#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


UA = "voynich-recipe-research-bot/0.1"


def download(url: str, out: pathlib.Path) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".part")
    r = subprocess.run(
        [
            "curl",
            "-L",
            "-f",
            "-A",
            UA,
            "-H",
            "Accept: application/pdf,*/*;q=0.8",
            "-o",
            str(tmp),
            url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if r.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        return False
    tmp.replace(out)
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download TLIO 2019 PDFs from a URL list.")
    ap.add_argument("--urls", default="data/lexicon/tlio2019_urls.txt", help="Text file with one PDF URL per line.")
    ap.add_argument("--out-dir", default="data/lexicon/tlio2019_pdfs", help="Where to store downloaded PDFs.")
    ap.add_argument("--force", action="store_true", help="Re-download even if file exists.")
    args = ap.parse_args(argv)

    url_path = pathlib.Path(args.urls)
    if not url_path.exists():
        print(f"Missing URL list: {url_path}", file=sys.stderr)
        return 2

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = []
    for ln in url_path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        urls.append(ln)

    ok = 0
    failed = 0
    skipped = 0
    for i, url in enumerate(urls, start=1):
        name = url.split("/")[-1]
        out = out_dir / f"{i:02d}_{name}"
        if out.exists() and not args.force:
            skipped += 1
            continue
        if download(url, out):
            ok += 1
        else:
            failed += 1
            print(f"FAILED {url}", file=sys.stderr)

    print(f"Downloaded {ok}, skipped {skipped}, failed {failed} -> {out_dir}", file=sys.stderr)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

