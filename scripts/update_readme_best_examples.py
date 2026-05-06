#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re


DOMAINS = ["herbal", "astronomical", "biological", "cosmological", "text_only", "unknown"]


def _parse_table(text: str) -> list[dict]:
    rows = []
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("| EVA baseword |"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) < 9:
                continue
            eva, cnt, _reduced, it_mod, en_mod, it_med, en_med, lat, en_lat = parts[:9]
            rows.append(
                {
                    "eva": eva,
                    "cnt": int(cnt) if cnt.isdigit() else 0,
                    "it_mod": it_mod,
                    "en_mod": en_mod,
                    "it_med": it_med,
                    "en_med": en_med,
                    "lat": lat,
                    "en_lat": en_lat,
                }
            )
    return rows


def _find_example(dom: str, baseword: str) -> str | None:
    # fast scan of recipe readmes index; just link to folio README
    # The per-folio README contains the loci; this is enough for the main README.
    root = pathlib.Path("data/recipe_readmes") / dom
    if not root.exists():
        return None
    # Find any folio README that contains the baseword
    for folio_dir in sorted(root.iterdir()):
        p = folio_dir / "README.md"
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace").lower()
        if baseword.strip("`").lower() in txt:
            return f"`data/recipe_readmes/{dom}/{folio_dir.name}/README.md`"
    return None


def build_block() -> str:
    lines = []
    lines.append("## Best lexicon-grounded examples (by domain)")
    lines.append("")
    lines.append(
        "Selected because they have a non-empty English gloss in the domain lexicon table (modern Italian list + WikWik “medieval-ish” proxy + Whitaker Latin). Still not a translation."
    )
    lines.append("")
    for dom in DOMAINS:
        p = pathlib.Path("data/domains") / dom / "README.md"
        if not p.exists():
            continue
        rows = _parse_table(p.read_text(encoding="utf-8", errors="replace"))
        # pick top rows with any English gloss present in any column
        good = [r for r in rows if any(x and x != "[n/a]" for x in (r["en_mod"], r["en_med"], r["en_lat"]))]
        good.sort(key=lambda r: r["cnt"], reverse=True)
        good = good[:3]
        lines.append(f"### {dom}")
        lines.append("| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English | Example |")
        lines.append("|---|---:|---|---|---|---|---|---|---|")
        for r in good:
            ex = _find_example(dom, r["eva"]) or "[n/a]"
            lines.append(
                f"| {r['eva']} | {r['cnt']} | {r['it_mod']} | {r['en_mod']} | {r['it_med']} | {r['en_med']} | {r['lat']} | {r['en_lat']} | {ex} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    readme = pathlib.Path("README.md")
    txt = readme.read_text(encoding="utf-8")
    block = build_block()

    m = re.search(r"^## Best lexicon-grounded examples \(by domain\)\s*$", txt, flags=re.M)
    if not m:
        raise SystemExit("Could not find start marker in README.md")
    start_idx = m.start()
    m2 = re.search(r"^## Top candidate basewords by domain \(first 20\)\s*$", txt[m.end() :], flags=re.M)
    if not m2:
        raise SystemExit("Could not find end marker (## Top candidate basewords...) in README.md")
    end_idx = m.end() + m2.start()

    new_txt = txt[:start_idx].rstrip() + "\n\n" + block + "\n" + txt[end_idx:].lstrip()
    readme.write_text(new_txt, encoding="utf-8")
    print("Updated README.md best-examples block.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
