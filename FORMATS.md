# Reference Formats

Supported input formats for `import_citation` / the Downloads watcher.

---

## BibTeX (`.bib`)

- Spec: https://www.ctan.org/pkg/bibtex / https://www.bibtex.com/g/bibtex-format/
- Parsed with: [`bibtexparser`](https://bibtexparser.readthedocs.io/) v1
- Common source: AGU/Wiley journal pages, Google Scholar, AMS

**Known quirks:**
- AGU/Wiley exports use the DOI as the citation key (e.g. `@article{https://doi.org/10.1029/…}`).
  This tool always regenerates keys in `LastName:Year` format.
- Fields are preserved as-is; BibDesk-specific fields (`bdsk-url-*`, `bdsk-file-*`,
  `date-added`, `date-modified`) are kept if present, and `date-added` is stamped on new entries.

---

## RIS (`.ris`)

- Spec: https://en.wikipedia.org/wiki/RIS_(file_format)
- Parsed with: [`rispy`](https://github.com/MrTango/rispy)
- Common source: Web of Science, Scopus, Zotero, most journal pages

**Field mapping (RIS → BibTeX):**

| RIS tag | RIS meaning          | BibTeX field |
|---------|----------------------|--------------|
| TY      | Reference type       | ENTRYTYPE    |
| AU      | Author               | author       |
| TI      | Title                | title        |
| JO / JF | Journal              | journal      |
| VL      | Volume               | volume       |
| IS      | Issue/number         | number       |
| SP      | Start page           | pages (start)|
| EP      | End page             | pages (end)  |
| PY / Y1 | Year                 | year         |
| DO      | DOI                  | doi          |
| UR      | URL                  | url          |
| AB      | Abstract             | abstract     |
| KW      | Keywords             | keywords     |
| PB      | Publisher            | publisher    |
| CY      | City                 | address      |
| N1      | Notes                | note         |
| SN      | ISSN/ISBN            | issn         |

**Type mapping (TY → ENTRYTYPE):**

| TY code      | BibTeX type    |
|--------------|----------------|
| JOUR / JFULL | article        |
| CONF / CPAPER| inproceedings  |
| BOOK         | book           |
| CHAP         | incollection   |
| THES         | phdthesis      |
| RPRT         | techreport     |
| ELEC / GEN   | misc           |

---

## EndNote Tagged (`.enw`)

- Spec: https://support.clarivate.com/Endnote/s/article/EndNote-tagged-format-specifications
- Parsed with: custom parser in `citation_import/parsers/endnote.py`
- Common source: Web of Science "Export → EndNote", library databases

**Field mapping (ENW → BibTeX):**

| ENW tag | ENW meaning       | BibTeX field |
|---------|-------------------|--------------|
| %0      | Reference type    | ENTRYTYPE    |
| %A      | Author (repeats)  | author       |
| %E      | Editor (repeats)  | editor       |
| %T      | Title             | title        |
| %J / %B | Journal / Book    | journal      |
| %V      | Volume            | volume       |
| %N      | Number/Issue      | number       |
| %P      | Pages             | pages        |
| %D      | Year/Date         | year         |
| %R      | DOI               | doi          |
| %U      | URL               | url          |
| %X      | Abstract          | abstract     |
| %K / %! | Keywords          | keywords     |
| %I      | Publisher         | publisher    |
| %C      | City              | address      |
| %Z      | Notes             | note         |
| %@      | ISSN/ISBN         | issn         |

**Type mapping (%0 → ENTRYTYPE):**

| %0 value              | BibTeX type    |
|-----------------------|----------------|
| Journal Article       | article        |
| Conference Paper      | inproceedings  |
| Book                  | book           |
| Book Section          | incollection   |
| Thesis                | phdthesis      |
| Report                | techreport     |
| Web Page              | misc           |
| Electronic Article    | article        |

---

## Citation Key Generation

Keys are always regenerated in **BibDesk's `LastName:Year` style**, regardless of what key
was in the source file. This matches the existing entries in `refs.bib`.

Rules:
1. Take the first author's last name (everything before the first comma in `Last, First` form,
   or everything after the first token in `First Last` form).
2. For compound last names (e.g. `Vaillant de Guélis`), join parts with hyphens →
   `Vaillant-de-Guelis`.
3. Strip LaTeX accent commands (`\'e` → `e`) and transliterate Unicode to ASCII.
4. Append `:Year` (four-digit year from the `year` field).
5. If the key already exists in the target file, append `a`, `b`, `c`, … until unique.

Examples:
- `Andrews, Timothy` + 2022 → `Andrews:2022`
- `Vaillant de Gu\'elis, T.` + 2017 → `Vaillant-de-Guelis:2017`
- `García, Carlos` + 2021 → `Garcia:2021`
- Second `Smith:2022` entry → `Smith:2022a`
