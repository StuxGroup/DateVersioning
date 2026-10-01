# Changelog

All notable changes to Date Versioning (datevers.ing) are documented here. This project is
versioned with [Date Versioning](https://datevers.ing) itself: `YY.MM.DD`, with `-1`, `-2`
and so on for further releases on the same day.

## v26.10.01

### Added

- Date Versioning specification 26.10.01 (`SPEC.md`), the first version of the standard
- The website at datevers.ing: the specification rendered from `SPEC.md`, a "Next version" tool and a "Validate" tool, a README badge snippet, and a section on using Date Versioning with AI tools and programs
- `/spec.md`, an exact copy of `SPEC.md` served as text, and a permanent page and Markdown file for this version at `/spec/26.10.01/` and `/spec/26.10.01.md`
- `/llms.txt` and `/datever.json` for AI tools and programs
- Changelogs page, "Boring Legal Stuff" pages, sitemap, 404 page and `robots.txt`
- `scripts/build.py`, which renders `SPEC.md` into the site, plus local dev server, CI, Pages deploy and release workflows
