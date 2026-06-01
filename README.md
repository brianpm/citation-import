# citation-import

Watches your `~/Downloads` folder and automatically imports reference files (`.bib`, `.ris`, `.enw`) into a master BibTeX bibliography. Designed for researchers who manage citations with **BibDesk** on macOS.

When a reference file appears in Downloads, citation-import:

1. Parses the file and extracts the entry (or entries)
2. Checks for duplicates against your existing bibliography (by DOI, then title)
3. Generates a clean `LastName:Year` citation key matching BibDesk's style
4. Appends the entry to your master `.bib` file **atomically** (no risk of corruption)
5. Sends a macOS notification with the new key
6. Moves the source file to the Trash

It also ships a standalone CLI (`import_citation`) for one-off imports and for building per-project bibliographies from a subset of files.

---

## Features

- **Three reference formats:** BibTeX (`.bib`), RIS (`.ris`), EndNote tagged (`.enw`)
- **Smart key generation:** always produces `LastName:Year` keys; handles LaTeX accents, Unicode, compound last names, and suffix disambiguation (`Smith:2022a`, `Smith:2022b`, …)
- **Duplicate detection:** DOI match first (definitive), then exact title match (fallback)
- **Atomic writes:** uses a temp-file + rename strategy — `refs.bib` is never left in a partial state
- **Preserves BibDesk metadata:** `@string` definitions and `bdsk-*` fields survive round-trips
- **macOS notifications:** via `osascript`, no extra dependencies
- **Background daemon:** uses [watchdog](https://github.com/gorakhargosh/watchdog) (native FSEvents on macOS) managed by launchd

---

## Requirements

- macOS (tested on macOS 14+)
- Python 3.10+
- [BibDesk](https://bibdesk.sourceforge.io/) (or any BibTeX workflow — BibDesk is not strictly required)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/citation-import.git
cd citation-import
```

### 2. Configure

Copy the example config and edit it:

```bash
cp config.example.toml ~/.citation_import.toml
```

Open `~/.citation_import.toml` and set `target_bib` to the path of your master bibliography:

```toml
target_bib = "~/Dropbox/refs.bib"   # wherever your master .bib lives
watch_dirs = ["~/Downloads"]
log_file   = "~/.citation_import.log"
```

### 3. Run the installer

```bash
bash install.sh
```

This will:
- Create an isolated Python virtual environment in `.venv/` (avoiding PEP 668 restrictions on system Python)
- Install Python dependencies (`pip install -r requirements.txt`) into that venv
- Generate a `launchd` plist tailored to your venv Python path and install location
- Load the watcher as a background login agent (starts immediately and on every login)

To verify it is running:

```bash
launchctl list | grep citation
tail -f ~/.citation_import.log
```

### Managing the daemon

```bash
# Stop
launchctl unload ~/Library/LaunchAgents/local.citation-import.plist

# Start
launchctl load ~/Library/LaunchAgents/local.citation-import.plist
```

### Installing on a second Mac

Repeat steps 1–3 on the other machine. Because `install.sh` detects your Python path and install directory at runtime, no editing is needed.

---

## Usage

### Background watcher

Once installed, the daemon runs silently. Drop any `.bib`, `.ris`, or `.enw` file into `~/Downloads` — it will be imported within a second or two and you will receive a notification.

### Standalone CLI

You can also import files manually:

```bash
# Import a file into your default target bibliography
python bin/import_citation paper.ris

# Import into a specific .bib file
python bin/import_citation paper.bib --target ~/projects/my_paper/local_refs.bib

# Preview what would be imported without writing anything
python bin/import_citation paper.ris --dry-run

# Verbose output (shows parsing and key generation details)
python bin/import_citation paper.ris --verbose
```

**Exit codes:** `0` = imported, `1` = parse error, `2` = write error, `3` = all entries were duplicates (skipped).

This makes it easy to build per-project bibliographies:

```bash
# Import a batch of downloaded papers into a project-local bib
for f in ~/Downloads/papers/*.ris; do
    python bin/import_citation "$f" --target ~/projects/thesis/refs.bib
done
```

---

## How citation keys are generated

Keys are always regenerated to match BibDesk's `LastName:Year` convention, regardless of what key appears in the source file. This matters because many journal sites export BibTeX with DOIs as keys (e.g. `@article{https://doi.org/10.1029/2022JD036675, …}`).

| Author field | Year | Generated key |
|---|---|---|
| `Andrews, Timothy and …` | 2022 | `Andrews:2022` |
| `Vaillant de Gu\'elis, T.` | 2017 | `Vaillant-de-Guelis:2017` |
| `García, Carlos` | 2021 | `Garcia:2021` |
| Second `Smith:2022` entry | 2022 | `Smith:2022a` |

Rules in detail:
- First author's last name is extracted from `Last, First` or `First Last` form
- LaTeX accent commands (`\'e`, `\"{u}`) are stripped to their base letter
- Unicode is transliterated to ASCII
- Compound last names (e.g. `Vaillant de Guelis`) are hyphen-joined
- Suffix `a`, `b`, `c`, … is appended when a key already exists in the target file

---

## Supported formats

### BibTeX (`.bib`)

Standard BibTeX format, parsed with [bibtexparser](https://bibtexparser.readthedocs.io/).

Common sources: AGU/Wiley journal pages, Google Scholar "Export BibTeX", AMS, ACS.

Note: many publishers export BibTeX with a DOI as the citation key. citation-import detects and replaces these automatically.

### RIS (`.ris`)

Parsed with [rispy](https://github.com/MrTango/rispy). Full field mapping is documented in [FORMATS.md](FORMATS.md).

Common sources: Web of Science, Scopus, most journal databases, Zotero.

### EndNote Tagged (`.enw`)

Custom parser. Full field mapping is in [FORMATS.md](FORMATS.md).

Common sources: Web of Science "Export → EndNote", library catalog systems.

---

## Configuration reference

`~/.citation_import.toml`:

| Key | Default | Description |
|---|---|---|
| `target_bib` | `~/refs.bib` | Path to your master BibTeX file |
| `watch_dirs` | `["~/Downloads"]` | Directories to watch (list) |
| `log_file` | `~/.citation_import.log` | Daemon log file |

All paths support `~` expansion.

---

## Troubleshooting

**Notifications don't appear after install**

macOS requires notification permission for `osascript` / Script Editor. Go to **System Settings → Notifications → Script Editor** and enable notifications. This prompt appears automatically on first use on most systems, but on some macOS versions you may need to enable it manually.

**`target_bib` doesn't exist yet**

If you're starting a fresh bibliography rather than importing into an existing one, create an empty `.bib` file first:

```bash
echo '%% Bibliography' > ~/path/to/refs.bib
```

citation-import will not create the file itself — it treats a missing target as an error to avoid silently writing to the wrong location.

**`import_citation` picks up the wrong Python**

`install.sh` uses `which python3` to find Python. If your system has multiple Python installations, make sure the right one is active before running the installer, or edit the generated plist at `~/Library/LaunchAgents/local.citation-import.plist` to point at the correct interpreter.

**File is imported but BibDesk doesn't show it**

BibDesk watches for external file changes and will prompt to reload. If it doesn't, use **File → Revert** to pick up the appended entry.

---

## Running the tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Project layout

```
citation_import/        Python package
  parsers/              Format-specific parsers (.bib, .ris, .enw)
  keygen.py             LastName:Year key generation
  dedup.py              Duplicate detection
  importer.py           Core import logic (atomic writes)
  watcher.py            FSEvents-based daemon
  notify.py             macOS notifications
  cli.py                import_citation CLI entry point
  config.py             Config loading

bin/
  import_citation       CLI entry point script
  watch_downloads       Daemon entry point script

launchd/
  com.citation-import.plist.template   launchd plist template (install.sh fills this in)

tests/                  Unit and integration tests
FORMATS.md              Detailed field mappings for all supported formats
config.example.toml     Example configuration
install.sh              One-step installer for the launchd daemon
```

---

## License

MIT
