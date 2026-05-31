"""Parse .bib files using bibtexparser v1."""

from pathlib import Path

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode


def parse(path: Path) -> list[dict]:
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(path, encoding="utf-8", errors="replace") as f:
        db = bibtexparser.load(f, parser=parser)

    entries = []
    for entry in db.entries:
        e = {k.lower(): v for k, v in entry.items()}
        # bibtexparser stores type in ENTRYTYPE and key in ID
        e["ENTRYTYPE"] = e.pop("entrytype", "misc")
        # Drop the old key — it will be regenerated
        e.pop("id", None)
        entries.append(e)

    return entries
