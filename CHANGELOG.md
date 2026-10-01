# Changelog

All notable changes to Date Versioning (datevers.ing) are documented here. This project is
versioned with [Date Versioning](https://datevers.ing) itself: `YY.MM.DD`, with `-1`, `-2`
and so on for further releases on the same day.

## v26.10.01-7

### Added

- Specification 26.10.01-2: Date Versioning works forever. The years 2000 to 2099 are written `YY` as before; from 2100, when two digits can no longer tell the century, the year is written in full with as many digits as it needs (`2100.01.01`, `10000.01.01`). The full year is never used before 2100, so each release date has exactly one Date Version (rule 12, replacing the 2099 end date)
- The previous specification is kept at /spec/26.10.01-1/, in every format

### Changed

- Precedence compares the year as a number (`YY` is `20YY`), so `99.12.31` < `2100.01.01` (rule 9); dates must be real Gregorian dates (rule 2)
- The SemVer form's MAJOR is the year minus 2000 (still `YY` up to 2099; `2100.01.01` becomes `100.1.100`), and converts back with `year = 2000 + MAJOR − offset`
- The regular expressions accept the full year from 2100; the validator, the next-version tool, `datever.json` and `llms.txt` follow the new rules

## v26.10.01-6

### Changed

- The footer's Stux.Group logo has its own column on the left, spanning both rows, with a vertical separator after it; "A Versioning Standard" and the links, then the copyright, "Created with" and the version, sit to its right

## v26.10.01-5

### Fixed

- The Stux.Group logo in the footer stays on the left of "A Versioning Standard" and the links on phones too, with the text and links stacked beside it, instead of sitting above them

## v26.10.01-4

### Changed

- The footer is laid out in two rows: the Stux.Group logo with "A Versioning Standard" and the links on top, then the copyright and licence, "Created with … by Stux.Group" and the version (a link to the changelogs) below a divider. On phones each row stacks, without the stray divider
- The brand line reads just "A Versioning Standard", since "Created with … by Stux.Group" already credits Stux.Group

## v26.10.01-3

### Added

- Every specification in every format: change the extension of `/spec`, `/spec/latest` or `/spec/<version>` to `.md`, `.txt` (plain text, wrapped at 80 columns), `.json` or `.xml` (the metadata, the numbered rules and every section as text and Markdown) or `.html`, for example `/spec/26.10.01.txt` or `/spec/latest.json`
- The formats are listed on each specification page, in `llms.txt` and in `datever.json`

### Fixed

- CI read the specification's version from `VERSION.md`, so it failed as soon as the site and the specification had different versions; it now reads it from `SPEC.md`, and checks every format of every specification

## v26.10.01-2

### Added

- `/spec/latest/`, which always shows the current specification (rendered in place, not a redirect, so tools that fetch it get the specification itself), and `/spec/latest.md`, its plain text
- `latest_url` and `latest_markdown_url` in `datever.json`, and both links in `llms.txt`

### Changed

- Each version's permanent page links to `/spec/latest/` as the place the latest version always lives

## v26.10.01-1

### Added

- Specification 26.10.01-1, rule 13: adopting Date Versioning after another scheme. The switch is noted in the first Date Version's changelog entry, every Date Version ranks above the earlier versions, and a project whose old SemVer versions would outrank its SemVer forms (a major of 26 or more) declares a fixed **major offset**, a multiple of 100 added to MAJOR (`26.10.01` → `126.10.100`)
- The previous specification is kept at /spec/26.10.01/ and /spec/26.10.01.md

### Changed

- The SemVer form adds the major offset to MAJOR and converts back with `YY = MAJOR mod 100`; the FAQ on switching from SemVer covers projects already at major 26 or more
- `datever.json` describes the major offset, and the validator mentions it next to the SemVer form

### Fixed

- `llms.txt` built its examples from the specification's version, which would have produced the invalid `26.10.01-1-1` now that the version has a release number

## v26.10.01

### Added

- Date Versioning specification 26.10.01 (`SPEC.md`), the first version of the standard
- The website at datevers.ing: the specification rendered from `SPEC.md`, a "Next version" tool and a "Validate" tool, a README badge snippet, and a section on using Date Versioning with AI tools and programs
- `/spec.md`, an exact copy of `SPEC.md` served as text, and a permanent page and Markdown file for this version at `/spec/26.10.01/` and `/spec/26.10.01.md`
- `/llms.txt` and `/datever.json` for AI tools and programs
- Changelogs page, "Boring Legal Stuff" pages, sitemap, 404 page and `robots.txt`
- `scripts/build.py`, which renders `SPEC.md` into the site, plus local dev server, CI, Pages deploy and release workflows
