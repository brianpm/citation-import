"""Integration tests for the core importer."""

import shutil
import tempfile
from pathlib import Path

import bibtexparser
import pytest

from citation_import.importer import import_to_bib

TESTS_DIR = Path(__file__).parent

_EMPTY_BIB = """\
%% Test bibliography

@string{jc = {J. Climate}}

"""

_EXISTING_BIB = """\
%% Test bibliography

@article{Smith:2022,
\tauthor = {Smith, John},
\ttitle = {A Study of Atmospheric Dynamics},
\tjournal = {Journal of Climate},
\tyear = {2022},
\tdoi = {10.1234/jclim.2022.test},
}

"""


@pytest.fixture()
def tmp_bib(tmp_path):
    """Return path to a temporary target .bib with one existing entry."""
    bib = tmp_path / "refs.bib"
    bib.write_text(_EXISTING_BIB, encoding="utf-8")
    return bib


@pytest.fixture()
def empty_bib(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(_EMPTY_BIB, encoding="utf-8")
    return bib


def test_import_ris(empty_bib):
    result = import_to_bib(TESTS_DIR / "sample.ris", empty_bib)
    assert not result.errors, result.errors
    assert len(result.imported) == 1
    assert result.imported[0] == "Smith:2022"
    # Verify written to file
    text = empty_bib.read_text()
    assert "Smith:2022" in text


def test_import_bib(empty_bib):
    result = import_to_bib(TESTS_DIR / "sample.bib", empty_bib)
    assert not result.errors, result.errors
    assert len(result.imported) == 1
    assert result.imported[0] == "Andrews:2022"


def test_import_enw(empty_bib):
    result = import_to_bib(TESTS_DIR / "sample.enw", empty_bib)
    assert not result.errors, result.errors
    assert len(result.imported) == 1
    # García → Garcia (accent stripped)
    assert "Garcia:2021" in result.imported[0] or "2021" in result.imported[0]


def test_duplicate_ris_skipped(tmp_bib):
    """sample.ris has the same DOI as the existing entry → should be skipped."""
    result = import_to_bib(TESTS_DIR / "sample.ris", tmp_bib)
    assert not result.errors
    assert len(result.imported) == 0
    assert len(result.skipped) == 1
    assert "DOI" in result.skipped[0]


def test_atomic_write_preserves_strings(empty_bib):
    """@string definitions in the target must be preserved after import."""
    result = import_to_bib(TESTS_DIR / "sample.ris", empty_bib)
    assert not result.errors
    text = empty_bib.read_text()
    assert "@string{jc" in text


def test_dry_run_does_not_write(empty_bib):
    original = empty_bib.read_text()
    result = import_to_bib(TESTS_DIR / "sample.ris", empty_bib, dry_run=True)
    assert not result.errors
    assert result.imported  # reports what would be imported
    assert empty_bib.read_text() == original  # file unchanged


def test_import_multi_bib_all_new(empty_bib):
    result = import_to_bib(TESTS_DIR / "multi.bib", empty_bib)
    assert not result.errors, result.errors
    assert len(result.imported) == 3
    text = empty_bib.read_text()
    for key in result.imported:
        assert key in text


def test_import_multi_bib_partial_duplicate(tmp_bib):
    # tmp_bib already contains Smith:2022 (DOI 10.1234/jclim.2022.test)
    result = import_to_bib(TESTS_DIR / "multi.bib", tmp_bib)
    assert not result.errors, result.errors
    assert len(result.imported) == 2
    assert len(result.skipped) == 1


def test_import_twice_second_is_duplicate(empty_bib):
    r1 = import_to_bib(TESTS_DIR / "sample.ris", empty_bib)
    assert r1.imported
    r2 = import_to_bib(TESTS_DIR / "sample.ris", empty_bib)
    assert not r2.errors
    assert not r2.imported
    assert r2.skipped
