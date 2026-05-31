"""Parse .ris files using rispy and map to BibTeX-style dicts."""

from pathlib import Path

import rispy

# RIS type codes → BibTeX ENTRYTYPE
_TYPE_MAP = {
    "JOUR": "article",
    "JFULL": "article",
    "ABST": "article",
    "CONF": "inproceedings",
    "CPAPER": "inproceedings",
    "BOOK": "book",
    "CHAP": "incollection",
    "THES": "phdthesis",
    "RPRT": "techreport",
    "ELEC": "misc",
    "ICOMM": "misc",
    "GEN": "misc",
}

# RIS field tags → BibTeX field names
_FIELD_MAP = {
    "title": "title",
    "primary_title": "title",
    "authors": "author",
    "first_authors": "author",
    "year": "year",
    "publication_year": "year",
    "journal_name": "journal",
    "alternate_title1": "journal",
    "volume": "volume",
    "number": "number",
    "start_page": "pages",
    "doi": "doi",
    "url": "url",
    "abstract": "abstract",
    "keywords": "keywords",
    "publisher": "publisher",
    "place_published": "address",
    "issn": "issn",
    "language": "language",
    "note": "note",
}


def _join_authors(authors: list[str]) -> str:
    return " and ".join(authors)


def _join_pages(ris_entry: dict) -> str | None:
    start = ris_entry.get("start_page", "")
    end = ris_entry.get("end_page", "")
    if start and end and start != end:
        return f"{start}--{end}"
    return start or end or None


def parse(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace") as f:
        records = rispy.load(f)

    entries = []
    for rec in records:
        e: dict = {}

        # Entry type
        type_of_ref = rec.get("type_of_reference", "GEN")
        e["ENTRYTYPE"] = _TYPE_MAP.get(type_of_ref, "misc")

        # Map standard fields
        for ris_key, bib_key in _FIELD_MAP.items():
            val = rec.get(ris_key)
            if val is None:
                continue
            if isinstance(val, list):
                if ris_key in ("authors", "first_authors"):
                    val = _join_authors(val)
                elif ris_key == "keywords":
                    val = ", ".join(val)
                else:
                    val = "; ".join(val)
            if val and bib_key not in e:
                e[bib_key] = str(val)

        # Pages need special handling (start + end)
        pages = _join_pages(rec)
        if pages and "pages" not in e:
            e["pages"] = pages

        # Some RIS files put the year inside the date field
        if "year" not in e:
            date = rec.get("year") or rec.get("date") or ""
            if date:
                import re
                m = re.search(r"\d{4}", str(date))
                if m:
                    e["year"] = m.group()

        entries.append(e)

    return entries
