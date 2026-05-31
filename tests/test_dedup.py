"""Tests for duplicate detection."""

from citation_import.dedup import is_duplicate

_EXISTING = [
    {
        "ID": "Smith:2022",
        "ENTRYTYPE": "article",
        "author": "Smith, John",
        "title": "A Study of Atmospheric Dynamics",
        "doi": "10.1234/jclim.2022.test",
        "year": "2022",
    },
    {
        "ID": "Jones:2021",
        "ENTRYTYPE": "article",
        "author": "Jones, Mary",
        "title": "Cloud Radiative Effects in Climate Models",
        "year": "2021",
    },
]


def test_doi_match():
    entry = {"doi": "https://doi.org/10.1234/jclim.2022.test", "title": "Something else"}
    dup, reason = is_duplicate(entry, _EXISTING)
    assert dup is True
    assert "DOI" in reason


def test_doi_match_variant():
    entry = {"doi": "doi:10.1234/jclim.2022.test"}
    dup, reason = is_duplicate(entry, _EXISTING)
    assert dup is True


def test_title_match_no_doi():
    entry = {"title": "Cloud Radiative Effects in Climate Models"}
    dup, reason = is_duplicate(entry, _EXISTING)
    assert dup is True
    assert "title" in reason


def test_title_case_insensitive():
    entry = {"title": "cloud radiative effects in climate models"}
    dup, reason = is_duplicate(entry, _EXISTING)
    assert dup is True


def test_no_duplicate():
    entry = {"doi": "10.9999/new.paper", "title": "Brand New Paper"}
    dup, reason = is_duplicate(entry, _EXISTING)
    assert dup is False
    assert reason == ""


def test_different_doi_not_duplicate():
    entry = {"doi": "10.9999/different"}
    dup, _ = is_duplicate(entry, _EXISTING)
    assert dup is False
