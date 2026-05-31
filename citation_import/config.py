"""Load configuration from ~/.citation_import.toml with sensible defaults."""

import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_DEFAULTS = {
    "target_bib": "~/refs.bib",
    "watch_dirs": ["~/Downloads"],
    "log_file": "~/.citation_import.log",
}


def load() -> dict:
    cfg = dict(_DEFAULTS)
    config_path = Path("~/.citation_import.toml").expanduser()
    if config_path.exists():
        with open(config_path, "rb") as f:
            cfg.update(tomllib.load(f))
    cfg["target_bib"] = str(Path(cfg["target_bib"]).expanduser())
    cfg["watch_dirs"] = [str(Path(d).expanduser()) for d in cfg["watch_dirs"]]
    cfg["log_file"] = str(Path(cfg["log_file"]).expanduser())
    return cfg
