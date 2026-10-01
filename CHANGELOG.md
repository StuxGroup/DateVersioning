# Changelog

All notable changes to Date Versioning (datevers.ing) are documented here. This project is
versioned with [Date Versioning](https://datevers.ing) itself: `YY.MM.DD`, with `-1`, `-2`
and so on for further releases on the same day.

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
