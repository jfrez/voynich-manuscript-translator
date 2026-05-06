#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re


DOMAINS = ["herbal", "astronomical", "biological", "cosmological", "text_only", "unknown"]


def _parse_table(text: str) -> list[tuple[str, str, str, str, str]]:
    """
    Returns rows as (eva, count, it_mod, en_mod, it_med, en_med, lat, en_lat)
    from the Domain Lexicon table in data/domains/<domain>/README.md.
    """
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
            rows.append((eva, cnt, it_mod, en_mod, it_med, en_med, lat, en_lat))
    return rows


def build_block() -> str:
    lines = []
    lines.append("## Top candidate basewords by domain (first 20)")
    lines.append("")
    lines.append("These are taken directly from `data/domains/<domain>/README.md` (Domain Lexicon table).")
    lines.append("")
    for dom in DOMAINS:
        p = pathlib.Path("data/domains") / dom / "README.md"
        if not p.exists():
            continue
        rows = _parse_table(p.read_text(encoding="utf-8", errors="replace"))[:20]
        lines.append(f"### {dom}")
        lines.append("| EVA baseword | Count | Italian (modern) | English | Italian (medieval-ish) | English | Latin | English |")
        lines.append("|---|---:|---|---|---|---|---|---|")
        for eva, cnt, it_mod, en_mod, it_med, en_med, lat, en_lat in rows:
            lines.append(f"| {eva} | {cnt} | {it_mod} | {en_mod} | {it_med} | {en_med} | {lat} | {en_lat} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    readme = pathlib.Path("README.md")
    txt = readme.read_text(encoding="utf-8")
    block = build_block()

    start = "## Top candidate basewords by domain (first 20)"
    m = re.search(r"^## Top candidate basewords by domain \(first 20\)\s*$", txt, flags=re.M)
    if not m:
        raise SystemExit("Could not find start marker in README.md")
    start_idx = m.start()

    # End marker: next H2 heading after the block (we expect '## 3. Model Assumptions')
    m2 = re.search(r"^## 3\. Model Assumptions", txt[m.end() :], flags=re.M)
    if not m2:
        raise SystemExit("Could not find end marker (## 3. Model Assumptions) in README.md")
    end_idx = m.end() + m2.start()

    new_txt = txt[:start_idx].rstrip() + "\n\n" + block + "\n" + txt[end_idx:].lstrip()
    readme.write_text(new_txt, encoding="utf-8")
    print("Updated README.md domain-candidate block.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
