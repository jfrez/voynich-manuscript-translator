#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.parse
import urllib.request


API = "https://en.wiktionary.org/w/api.php"


def api_get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "voynich-recipe-research-bot/0.1"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_category_members(category: str) -> list[str]:
    titles: list[str] = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "500",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        data = api_get(params)
        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            t = m.get("title")
            if t:
                titles.append(t)
        cont = data.get("continue", {})
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            break
    return titles


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download Wiktionary 'Italian archaic terms' titles as a wordlist.")
    ap.add_argument("--out", default="data/lexicon/wiktionary_it_archaic_terms.txt", help="Output path.")
    args = ap.parse_args(argv)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    titles = fetch_category_members("Italian archaic terms")
    # Keep only mainspace word titles (filter out Category:, Appendix:, etc.)
    words = []
    for t in titles:
        if ":" in t:
            continue
        words.append(t.strip().lower())

    # Dedup preserve order
    seen = set()
    uniq = []
    for w in words:
        if not w or w in seen:
            continue
        seen.add(w)
        uniq.append(w)

    out_path.write_text("\n".join(uniq) + "\n", encoding="utf-8")
    print(f"Wrote {len(uniq)} archaic Italian titles -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

