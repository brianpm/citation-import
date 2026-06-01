"""Background daemon: watch configured directories for new reference files."""

import logging
import os
import signal
import sys
import time
from pathlib import Path

from send2trash import send2trash
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from . import config as _config
from .importer import import_to_bib
from .notify import send as notify
from .parsers import SUPPORTED_EXTENSIONS

log = logging.getLogger(__name__)


class _ReferenceHandler(FileSystemEventHandler):
    def __init__(self, target_bib: str):
        self._target = target_bib
        self._processing = set()

    def _handle(self, path: str) -> None:
        p = Path(path)
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        if not p.exists():
            return

        path_str = str(p.resolve())
        if path_str in self._processing:
            return
        self._processing.add(path_str)

        try:
            self._process_file(p, path_str)
        finally:
            self._processing.discard(path_str)

    def _process_file(self, p: Path, path_str: str) -> None:
        log.info("Detected reference file: %s", p)
        # Wait briefly to ensure the file is fully written
        time.sleep(1.0)

        if not p.exists():
            return

        result = import_to_bib(str(p), self._target)

        if result.errors:
            msg = "; ".join(result.errors)
            log.error("Import failed for %s: %s", p.name, msg)
            notify(
                "Citation Import — Error",
                subtitle=p.name,
                body=msg[:200],
            )
            return

        if result.imported:
            n = len(result.imported)
            subtitle = result.imported[0] if n == 1 else f"{n} citations"
            log.info("Imported %d entry/entries: %s", n, ", ".join(result.imported))
            notify(
                "Citation Imported",
                subtitle=subtitle,
                body=f"Added to {Path(self._target).name}",
            )
            try:
                send2trash(str(p))
                log.info("Moved to Trash: %s", p)
            except Exception as exc:
                log.warning("Could not move to Trash: %s", exc)

        elif result.skipped:
            log.info("All entries already present (duplicate): %s", p.name)
            notify(
                "Citation Import — Duplicate",
                subtitle=p.name,
                body="Already in refs.bib — moved to Trash",
            )
            try:
                send2trash(str(p))
            except Exception as exc:
                log.warning("Could not move to Trash: %s", exc)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.dest_path)


def main():
    cfg = _config.load()
    log_file = cfg["log_file"]
    target_bib = cfg["target_bib"]
    watch_dirs = cfg["watch_dirs"]

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # Only add file handler; launchd captures stdout/stderr from the plist config
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    log.info("Citation watcher starting. Target: %s", target_bib)

    observer = Observer()
    handler = _ReferenceHandler(target_bib)

    for watch_dir in watch_dirs:
        expanded = os.path.expanduser(watch_dir)
        if not os.path.isdir(expanded):
            log.warning("Watch directory does not exist, skipping: %s", expanded)
            continue
        observer.schedule(handler, expanded, recursive=False)
        log.info("Watching: %s", expanded)

    observer.start()

    def _shutdown(signum, frame):
        log.info("Stopping citation watcher (signal %d)", signum)
        observer.stop()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while observer.is_alive():
            observer.join(timeout=1.0)
    finally:
        observer.stop()
        observer.join()
        log.info("Citation watcher stopped.")


if __name__ == "__main__":
    main()
