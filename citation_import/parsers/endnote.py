"""Parse EndNote tagged (.enw) files.

The ENW format uses percent-tag lines:
  %0 Reference Type
  %A Author
  %T Title
  %J Journal / Secondary Title
  %V Volume
  %N Number / Issue
  %P Pages
  %D Year
  %R DOI
  %U URL
  %X Abstract
  %K Keywords
  %I Publisher
  %C City
  %Z Notes
  %L Label / call number
  %M Accession Number

Multiple %A lines = multiple authors.
Records are separated by blank lines.
"""

from pathlib import Path
import re

# %tag → BibTeX field name (for single-value tags)
_FIELD_MAP = {
    "T": "title",
    "J": "journal",
    "B": "journal",   # secondary title (book title for chapters)
    "V": "volume",
    "N": "number",
    "P": "pages",
    "D": "year",
    "R": "doi",
    "U": "url",
    "X": "abstract",
    "I": "publisher",
    "C": "address",
    "Z": "note",
    "@": "issn",
    "!": "keywords",
    "K": "keywords",
}

# %0 type string → BibTeX ENTRYTYPE
_TYPE_MAP = {
    "journal article": "article",
    "conference paper": "inproceedings",
    "conference proceedings": "inproceedings",
    "book": "book",
    "book section": "incollection",
    "thesis": "phdthesis",
    "report": "techreport",
    "web page": "misc",
    "electronic article": "article",
    "electronic book": "book",
}


def _parse_records(lines: list[str]) -> list[dict[str, list[str]]]:
    """Split raw lines into per-record tag→value(s) dicts."""
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    last_tag: str | None = None

    for line in lines:
        line = line.rstrip("\n\r")
        m = re.match(r"^%([A-Z0@!])\s+(.*)", line)
        if m:
            tag, value = m.group(1), m.group(2)
            current.setdefault(tag, []).append(value)
            last_tag = tag
        elif line.strip() == "":
            if current:
                records.append(current)
                current = {}
                last_tag = None
        elif last_tag and line.startswith(" "):
            # Continuation of the previous field
            current[last_tag][-1] += " " + line.strip()

    if current:
        records.append(current)

    return records


def parse(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    raw_records = _parse_records(lines)
    entries = []

    for rec in raw_records:
        e: dict = {}

        # Entry type from %0
        ref_type = " ".join(rec.get("0", [])).lower()
        e["ENTRYTYPE"] = _TYPE_MAP.get(ref_type, "misc")

        # Authors from %A (multiple lines)
        authors = rec.get("A", [])
        if authors:
            e["author"] = " and ".join(authors)

        # Editors from %E (multiple lines)
        editors = rec.get("E", [])
        if editors:
            e["editor"] = " and ".join(editors)

        # Single-value fields
        for tag, bib_key in _FIELD_MAP.items():
            values = rec.get(tag, [])
            if values and bib_key not in e:
                e[bib_key] = " ".join(values)

        # Year: extract 4-digit year from whatever %D contains
        if "year" in e:
            m = re.search(r"\d{4}", e["year"])
            e["year"] = m.group() if m else e["year"]

        entries.append(e)

    return entries
