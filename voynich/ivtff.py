from __future__ import annotations

import dataclasses
import re
from typing import Iterable, Iterator


@dataclasses.dataclass(frozen=True)
class FolioRecord:
    folio: str
    page_number: int | None
    section: str | None  # e.g. herbal, pharma, astronomical, text only
    currier: str | None
    plant_id: str | None
    refs: list[str]
    notes: list[str]
    loci: list[dict]  # {"locus": "...", "raw": "...", "eva": "..."}

    @property
    def eva_text(self) -> str:
        return "\n".join(x["eva"] for x in self.loci if x.get("eva"))


_FOLIO_HEADER_RE = re.compile(r"^\s*<(?P<folio>f\d+(?:r|v)\d*(?:\.\d+)?)>\s*(?:<!.*>)?\s*$")
_PAGE_RE = re.compile(r"^\s*#\s*page\s+(?P<n>\d+)\s*$", re.IGNORECASE)
_SECTION_RE = re.compile(r"^\s*#\s*(?P<section>herbal|pharma|astronomical|cosmological|biological|text only)\s*$", re.IGNORECASE)
_CURRIER_RE = re.compile(r"^\s*#\s*Currier(?:'s)?\s+language\s+(?P<currier>[AB])", re.IGNORECASE)
_PLANT_ID_RE = re.compile(r"^\s*#\s*Plant ID:\s*(?P<id>.+?)\s*$", re.IGNORECASE)
_REF_RE = re.compile(r"^\s*#\s*Ref:\s*(?P<ref>.+?)\s*$", re.IGNORECASE)
_LOCUS_LINE_RE = re.compile(r"^\s*<(?P<locus>[^>]+)>\s*(?P<text>.*)\s*$")


def _strip_ivtff_markup(text: str) -> str:
    # Remove inline comments like <! ... >
    text = re.sub(r"<![^>]*>", "", text)
    # Remove paragraph start/end markers
    text = text.replace("<%>", "").replace("<$>", "")
    # Replace uncertain separators with spaces
    text = text.replace("<->", " ")
    # Remove most IVTFF braces used for uncertain readings while keeping payload
    # {c'y} -> c'y ; {cto} -> cto
    text = re.sub(r"{([^}]+)}", r"\1", text)
    # Normalize punctuation into spaces (Voynich EVA often uses '.' as word separator)
    text = text.replace(".", " ").replace(",", " ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_ivtff_lines(lines: Iterable[str]) -> Iterator[FolioRecord]:
    current_folio: str | None = None
    page_number: int | None = None
    section: str | None = None
    currier: str | None = None
    plant_id: str | None = None
    refs: list[str] = []
    notes: list[str] = []
    loci: list[dict] = []

    def flush() -> FolioRecord | None:
        nonlocal current_folio, page_number, section, currier, plant_id, refs, notes, loci
        if not current_folio:
            return None
        rec = FolioRecord(
            folio=current_folio,
            page_number=page_number,
            section=section,
            currier=currier,
            plant_id=plant_id,
            refs=list(refs),
            notes=list(notes),
            loci=list(loci),
        )
        page_number = None
        section = None
        currier = None
        plant_id = None
        refs = []
        notes = []
        loci = []
        return rec

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        m = _FOLIO_HEADER_RE.match(line)
        if m:
            prev = flush()
            if prev:
                yield prev
            current_folio = m.group("folio")
            continue

        if current_folio is None:
            continue

        m = _PAGE_RE.match(line)
        if m:
            page_number = int(m.group("n"))
            continue

        m = _SECTION_RE.match(line)
        if m:
            section = m.group("section").lower()
            continue

        m = _CURRIER_RE.match(line)
        if m:
            currier = m.group("currier").upper()
            continue

        m = _PLANT_ID_RE.match(line)
        if m:
            plant_id = m.group("id").strip()
            continue

        m = _REF_RE.match(line)
        if m:
            refs.append(m.group("ref").strip())
            continue

        if line.startswith("#"):
            note = line.lstrip("#").strip()
            if note:
                notes.append(note)
            continue

        m = _LOCUS_LINE_RE.match(line)
        if m:
            locus = m.group("locus").strip()
            text = m.group("text").strip()
            loci.append(
                {
                    "locus": locus,
                    "raw": text,
                    "eva": _strip_ivtff_markup(text),
                }
            )
            continue

    last = flush()
    if last:
        yield last


def guess_plant_category(plant_id: str | None, section: str | None) -> str:
    """
    Heuristic 'visual' proxy using only the provided Plant ID strings.
    This is NOT a real identification of the Voynich plant drawing.
    """
    category, _confidence, _matches = classify_plant_category(plant_id, section=section)
    return category
    if section == "herbal":
        return "unknown"
    return "unknown"


def classify_plant_category(plant_id: str | None, section: str | None = None) -> tuple[str, float, list[str]]:
    """
    Returns: (category, confidence, matched_terms)
    category in: root/flower/leaf/aquatic/unknown

    NOTE: This is a heuristic based on Plant ID *strings* in the IVTFF file.
    It does not analyze drawings and does not claim correctness.
    """
    if not plant_id:
        return ("unknown", 0.0, [])

    pid = plant_id.lower()
    # Tokenize into words; keep some multiword checks separately.
    words = set(re.findall(r"[a-z]+", pid))

    # Keyword sets (curated for common Plant ID strings seen in IVTFF ZL file)
    aquatic_terms = {
        "lotus",
        "nymphaea",
        "nymph",
        "nymphoides",
        "peltata",
        "water",
        "aquatic",
        "lily",  # water lily also possible; ambiguous with lilium
        "collocasia",  # often discussed with aquatic/lotus in IDs here
    }
    root_terms = {
        "radix",
        "rhiz",
        "rhizoma",
        "tuber",
        "bulb",
        "ginger",
        "zingiber",
        "mandragora",
        "cucumber",  # often implies tuber/root in these IDs
        "arctium",  # burdock root
        "ipomea",
        "ipomoea",
        "convolvula",  # often paired with ipomea in IDs
    }
    flower_terms = {
        "cyanus",
        "centaurea",
        "kornblume",
        "hypericum",
        "silene",
        "viola",
        "rosa",
        "lilium",
        "flos",
        "flower",
        "chamomile",
        "chamom",
        "sambuc",
    }
    leaf_terms = {
        "urtica",
        "parietaria",
        "paretaria",
        "atriplex",
        "spinach",
        "polygonum",
        "potentilla",
        "chelidonium",
        "salvia",
        "mentha",
        "basil",
        "folia",
        "leaf",
        "asclepiades",
        "pediculum",
        "bidens",
        "praenanthes",
    }

    scores = {"aquatic": 0, "root": 0, "flower": 0, "leaf": 0}
    matches: dict[str, list[str]] = {k: [] for k in scores}

    def add_hits(category: str, terms: set[str], weight: int = 1) -> None:
        for t in terms:
            if t in pid or t in words:
                scores[category] += weight
                matches[category].append(t)

    # Multiword/phrase boosts
    if "water lily" in pid or "egyptian lotus" in pid:
        scores["aquatic"] += 3
        matches["aquatic"].append("water_lily/egyptian_lotus")

    add_hits("aquatic", aquatic_terms, weight=2)
    add_hits("root", root_terms, weight=2)
    add_hits("flower", flower_terms, weight=2)
    add_hits("leaf", leaf_terms, weight=2)

    # If it's herbal section and nothing matched, default to leaf-ish (most herbs are leafy tops)
    if section and section.lower() == "herbal" and max(scores.values()) == 0:
        return ("leaf", 0.25, ["section=herbal_default"])

    best_cat = max(scores, key=lambda k: scores[k])
    best_score = scores[best_cat]
    if best_score == 0:
        return ("unknown", 0.1, [])

    # Confidence: normalized by total hits; cap at 0.95
    total = sum(scores.values()) or 1
    confidence = min(0.95, best_score / total)

    # If ties or low separation, reduce confidence
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and sorted_scores[0] == sorted_scores[1]:
        confidence = min(confidence, 0.4)

    # Deduplicate matches
    uniq_matches = sorted(set(matches[best_cat]))
    return (best_cat, float(confidence), uniq_matches)


def extract_plant_candidates(plant_id: str | None) -> list[str]:
    """
    Turn a free-text IVTFF 'Plant ID:' field into a list of candidate names.
    This is a best-effort normalization, not a botanical claim.
    """
    if not plant_id:
        return []
    s = plant_id.strip()
    # Drop bracket noise like belladonn[a] -> belladonna, d[iv|w]ale -> diwale (best-effort)
    s = re.sub(r"\[([^\]]+)\]", lambda m: m.group(1).split("|")[0], s)
    # Remove parenthetical attributions (authors etc.)
    s = re.sub(r"\([^)]*\)", "", s)
    # Replace separators with commas
    s = s.replace(";", ",")
    # Split and clean
    parts = []
    for p in s.split(","):
        p = p.strip()
        if not p:
            continue
        # Drop leading labels like "cf." or "sp?"
        p = re.sub(r"^(cf\.|cf|sp\?|sp)\s+", "", p, flags=re.IGNORECASE)
        # Collapse whitespace
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            parts.append(p)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for p in parts:
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out
