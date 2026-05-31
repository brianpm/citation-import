"""Core import logic: parse → deduplicate → generate key → append to target .bib."""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import convert_to_unicode

from .dedup import is_duplicate
from .keygen import generate_key
from .parsers import parse_file

log = logging.getLogger(__name__)


@dataclass
class ImportResult:
    source: str
    imported: list[str] = field(default_factory=list)   # keys of newly added entries
    skipped: list[str] = field(default_factory=list)     # keys/reasons for skipped entries
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.errors


def _load_bib_for_reading(path: str) -> bibtexparser.bibdatabase.BibDatabase:
    """Load a .bib file for duplicate/key checking only. Never written back."""
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    parser.ignore_nonstandard_types = False
    with open(path, encoding="utf-8", errors="replace") as f:
        return bibtexparser.load(f, parser=parser)


def _format_new_entries(entries: list[dict]) -> str:
    """Render a list of new entries as BibTeX text (new entries only, not the whole file)."""
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = entries
    writer = BibTexWriter()
    writer.indent = "\t"
    writer.comma_first = False
    return bibtexparser.dumps(db, writer)


def _append_entries_atomically(new_text: str, target_path: str) -> None:
    """Append *new_text* to *target_path* without touching existing content.

    Writes to a temp file in the same directory, then atomically replaces the
    target so the file is never left in a partial state.
    """
    target = Path(target_path)
    existing = target.read_bytes()

    tmp_fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".bib.tmp")
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(existing)
            if not existing.endswith(b"\n"):
                f.write(b"\n")
            f.write(new_text.encode("utf-8"))
        os.replace(tmp_path, target_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _today_str() -> str:
    now = datetime.now()
    offset = datetime.now().astimezone().strftime("%z")
    return now.strftime(f"%Y-%m-%d %H:%M:%S {offset}")


def import_to_bib(
    source_path: str | Path,
    target_bib_path: str | Path,
    dry_run: bool = False,
) -> ImportResult:
    """Parse *source_path*, deduplicate against *target_bib_path*, and append new entries.

    Existing content in *target_bib_path* is never rewritten — only new entries
    are appended, preserving all formatting, entry order, and non-standard types.

    With *dry_run=True*, reports what would be imported without writing anything.
    """
    source_path = str(source_path)
    target_bib_path = str(target_bib_path)
    result = ImportResult(source=source_path)

    # --- Parse incoming file ---
    try:
        incoming = parse_file(source_path)
    except Exception as exc:
        result.errors.append(f"Parse error: {exc}")
        return result

    if not incoming:
        result.errors.append("No entries found in source file")
        return result

    # --- Load existing bibliography (read-only: dedup + key collision checks) ---
    try:
        db = _load_bib_for_reading(target_bib_path)
    except Exception as exc:
        result.errors.append(f"Could not read target bib: {exc}")
        return result

    existing_entries = db.entries
    existing_keys = {e["ID"] for e in existing_entries}

    # --- Process each incoming entry ---
    new_entries = []
    for entry in incoming:
        dup, reason = is_duplicate(entry, existing_entries)
        if dup:
            desc = entry.get("title", "(no title)")[:80]
            result.skipped.append(f"duplicate ({reason}): {desc}")
            log.info("Skipped duplicate: %s", desc)
            continue

        key = generate_key(entry, existing_keys)
        existing_keys.add(key)

        bib_entry = dict(entry)
        bib_entry["ID"] = key
        bib_entry["ENTRYTYPE"] = entry.get("ENTRYTYPE", "misc")
        bib_entry.setdefault("date-added", _today_str())
        bib_entry.setdefault("date-modified", bib_entry["date-added"])

        new_entries.append(bib_entry)
        result.imported.append(key)
        log.info("Will import: %s", key)

    if not new_entries:
        return result  # all duplicates — nothing to write

    if dry_run:
        return result

    # --- Append only new entries; existing file content is untouched ---
    try:
        new_text = _format_new_entries(new_entries)
        _append_entries_atomically(new_text, target_bib_path)
    except Exception as exc:
        result.errors.append(f"Write error: {exc}")
        result.errors.append("refs.bib was NOT modified (write failed safely)")
        result.imported.clear()

    return result
