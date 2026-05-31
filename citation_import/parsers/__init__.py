"""Dispatch to the right parser based on file extension."""

from pathlib import Path

from .bibtex import parse as _parse_bib
from .ris import parse as _parse_ris
from .endnote import parse as _parse_enw

_PARSERS = {
    ".bib": _parse_bib,
    ".ris": _parse_ris,
    ".enw": _parse_enw,
}

SUPPORTED_EXTENSIONS = set(_PARSERS)


def parse_file(path: str | Path) -> list[dict]:
    """Parse *path* and return a list of normalized entry dicts.

    Each dict has lowercase field names matching BibTeX conventions plus
    a mandatory 'ENTRYTYPE' key (e.g. 'article', 'book').
    The 'ID' key is NOT set here — key generation happens in importer.py.
    """
    path = Path(path)
    ext = path.suffix.lower()
    parser = _PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file type: {ext!r}. Supported: {sorted(SUPPORTED_EXTENSIONS)}")
    return parser(path)
