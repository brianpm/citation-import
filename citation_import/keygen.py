"""Generate BibTeX citation keys in BibDesk's LastName:Year style."""

import re
import unicodedata


# LaTeX accent command patterns → base character
_LATEX_ACCENTS = re.compile(
    r"\\['`^\"~=.][{]?([a-zA-Z])[}]?"
    r"|\\[a-zA-Z]+[{]([a-zA-Z])[}]"
    r"|[{]\\[a-zA-Z]+\s+([a-zA-Z])[}]"
)
_BRACES = re.compile(r"[{}]")
_NONWORD = re.compile(r"[^\w\-]")
_MULTI_HYPHEN = re.compile(r"-+")


def _strip_latex(text: str) -> str:
    """Remove LaTeX accent commands and braces, keeping the base letter."""
    def _replace(m):
        for g in m.groups():
            if g:
                return g
        return ""
    text = _LATEX_ACCENTS.sub(_replace, text)
    text = _BRACES.sub("", text)
    return text


def _to_ascii(text: str) -> str:
    """Decompose unicode and drop combining characters."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _extract_last_name(author_field: str) -> str:
    """Return cleaned last name of first author.

    Handles both 'Last, First' and 'First Last' forms, and 'and'-separated lists.
    Compound last names (e.g. 'Vaillant de Guelis') are hyphen-joined.
    """
    # Take only the first author
    first_author = author_field.split(" and ")[0].strip()

    if "," in first_author:
        # "Last, First" form — everything before the first comma is the last name
        last = first_author.split(",")[0].strip()
    else:
        # "First Last" form — last word is the last name, but treat particles carefully
        # Simple heuristic: if there are multiple words, take all but the first as last name
        parts = first_author.split()
        if len(parts) == 1:
            last = parts[0]
        elif len(parts) == 2:
            last = parts[-1]
        else:
            # "First von Last" — everything after the first token
            last = " ".join(parts[1:])

    last = _strip_latex(last)
    last = _to_ascii(last)
    # Replace spaces with hyphens (BibDesk style for compound names)
    last = last.replace(" ", "-")
    # Strip anything not alphanumeric or hyphen
    last = _NONWORD.sub("", last)
    last = _MULTI_HYPHEN.sub("-", last).strip("-")
    return last or "Unknown"


def _extract_year(entry: dict) -> str:
    year = str(entry.get("year", "")).strip()
    m = re.search(r"\d{4}", year)
    return m.group() if m else "0000"


def generate_key(entry: dict, existing_keys: set[str]) -> str:
    """Return a unique LastName:Year key for *entry* not already in *existing_keys*."""
    author = entry.get("author", "")
    last = _extract_last_name(author) if author else "Unknown"
    year = _extract_year(entry)
    base = f"{last}:{year}"

    if base not in existing_keys:
        return base

    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = f"{base}{suffix}"
        if candidate not in existing_keys:
            return candidate

    # Extremely unlikely fallback
    import uuid
    return f"{base}_{uuid.uuid4().hex[:4]}"
