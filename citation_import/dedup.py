"""Duplicate detection for BibTeX entries."""

import re


def _normalize_doi(doi: str) -> str:
    doi = doi.strip().lower()
    # Strip common prefixes
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi


def _normalize_title(title: str) -> str:
    # Remove braces, LaTeX commands, extra whitespace; lowercase
    title = re.sub(r"[{}\\]", "", title)
    title = re.sub(r"\s+", " ", title).strip().lower()
    return title


def _entry_doi(entry: dict) -> str | None:
    doi = entry.get("doi", "").strip()
    return _normalize_doi(doi) if doi else None


def _entry_title(entry: dict) -> str | None:
    title = entry.get("title", "").strip()
    return _normalize_title(title) if title else None


def is_duplicate(entry: dict, existing_entries: list[dict]) -> tuple[bool, str]:
    """Return (True, reason) if *entry* is already in *existing_entries*, else (False, '')."""
    incoming_doi = _entry_doi(entry)
    incoming_title = _entry_title(entry)

    for existing in existing_entries:
        if incoming_doi:
            existing_doi = _entry_doi(existing)
            if existing_doi and incoming_doi == existing_doi:
                return True, f"DOI match ({incoming_doi})"

        if not incoming_doi and incoming_title:
            existing_title = _entry_title(existing)
            if existing_title and incoming_title == existing_title:
                return True, f"title match"

    return False, ""
