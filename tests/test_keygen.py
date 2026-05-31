"""Tests for citation key generation."""

import pytest
from citation_import.keygen import generate_key, _extract_last_name


@pytest.mark.parametrize("author,expected", [
    ("Smith, John A.", "Smith"),
    ("Smith, John", "Smith"),
    ("John Smith", "Smith"),
    ("George Ohring", "Ohring"),
    ("Vaillant de Gu\\'elis, T.", "Vaillant-de-Guelis"),
    ("Andr\\'e, Jean-Claude", "Andre"),
    ("von Neumann, John", "von-Neumann"),
    ("García, Carlos", "Garcia"),
])
def test_extract_last_name(author, expected):
    assert _extract_last_name(author) == expected


def test_generate_key_basic():
    entry = {"author": "Smith, John", "year": "2022"}
    assert generate_key(entry, set()) == "Smith:2022"


def test_generate_key_no_conflict():
    entry = {"author": "Jones, Mary", "year": "2021"}
    existing = {"Smith:2022"}
    assert generate_key(entry, existing) == "Jones:2021"


def test_generate_key_conflict():
    entry = {"author": "Smith, John", "year": "2022"}
    existing = {"Smith:2022"}
    assert generate_key(entry, existing) == "Smith:2022a"


def test_generate_key_multiple_conflicts():
    entry = {"author": "Smith, John", "year": "2022"}
    existing = {"Smith:2022", "Smith:2022a", "Smith:2022b"}
    assert generate_key(entry, existing) == "Smith:2022c"


def test_generate_key_doi_author():
    # The kind of entry downloaded from AGU/Wiley with DOI as key
    entry = {
        "author": "Andrews, Timothy and Gregory, Jonathan M.",
        "year": "2022",
        "ENTRYTYPE": "article",
    }
    key = generate_key(entry, set())
    assert key == "Andrews:2022"


def test_generate_key_no_author():
    entry = {"year": "2020"}
    key = generate_key(entry, set())
    assert key == "Unknown:2020"
