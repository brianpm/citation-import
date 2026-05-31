"""Standalone CLI: import_citation <file> [--target refs.bib] [--dry-run] [--verbose]"""

import argparse
import logging
import sys
from pathlib import Path

from . import config as _config
from .importer import import_to_bib
from .parsers import SUPPORTED_EXTENSIONS


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="import_citation",
        description="Import a reference file (.bib, .ris, .enw) into a master BibTeX bibliography.",
    )
    parser.add_argument("source", help=f"Reference file to import ({', '.join(sorted(SUPPORTED_EXTENSIONS))})")
    parser.add_argument(
        "--target",
        default=None,
        help="Target .bib file (default: target_bib from ~/.citation_import.toml, or ~/refs.bib)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    cfg = _config.load()
    target = args.target or cfg["target_bib"]

    source = Path(args.source)
    if not source.exists():
        print(f"Error: source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    if not Path(target).exists():
        print(f"Error: target bib not found: {target}", file=sys.stderr)
        sys.exit(2)

    result = import_to_bib(source, target, dry_run=args.dry_run)

    prefix = "[dry-run] " if args.dry_run else ""

    for key in result.imported:
        print(f"{prefix}Imported: {key}")

    for msg in result.skipped:
        print(f"{prefix}Skipped: {msg}")

    for msg in result.errors:
        print(f"Error: {msg}", file=sys.stderr)

    if result.errors:
        sys.exit(2)
    if not result.imported and not result.skipped:
        # No entries at all
        sys.exit(1)
    if result.imported:
        sys.exit(0)
    # All skipped (duplicates)
    sys.exit(3)


if __name__ == "__main__":
    main()
