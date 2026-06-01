"""Tests for reference file parsers."""

from pathlib import Path
import pytest
from citation_import.parsers import parse_file

TESTS_DIR = Path(__file__).parent


def test_parse_bib():
    entries = parse_file(TESTS_DIR / "sample.bib")
    assert len(entries) == 1
    e = entries[0]
    assert e["ENTRYTYPE"] == "article"
    assert "Andrews" in e["author"]
    assert e["year"] == "2022"
    assert "doi" in e
    # Key should NOT be in the entry (regenerated later)
    assert "ID" not in e


def test_parse_ris():
    entries = parse_file(TESTS_DIR / "sample.ris")
    assert len(entries) == 1
    e = entries[0]
    assert e["ENTRYTYPE"] == "article"
    assert "Smith" in e["author"]
    assert e["year"] == "2022"
    assert e["journal"] == "Journal of Climate"
    assert e["doi"] == "10.1234/jclim.2022.test"


def test_parse_enw():
    entries = parse_file(TESTS_DIR / "sample.enw")
    assert len(entries) == 1
    e = entries[0]
    assert e["ENTRYTYPE"] == "article"
    assert "García" in e["author"] or "Garc" in e["author"]
    assert e["year"] == "2021"
    assert "Cloud Radiative" in e["title"]
    assert e["doi"] == "10.1029/2021GL095000"


def test_parse_bib_multi():
    entries = parse_file(TESTS_DIR / "multi.bib")
    assert len(entries) == 3


def test_unsupported_extension():
    from citation_import.parsers import parse_file
    with pytest.raises(ValueError, match="Unsupported"):
        parse_file("something.docx")
