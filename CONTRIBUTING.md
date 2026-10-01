<p align="center">
  <img src="https://global.media.stux.group/logo.png" height="80" alt="Stux.Group Logo">
</p>

# Contributing to Date Versioning

Date Versioning is a Stux.Group project and the specification is open to proposals. Questions:
[legal@stux.group](mailto:legal@stux.group) for legal matters, otherwise open an issue.

## Proposing a change to the specification

1. **Open an issue first** describing the problem and the change you suggest. Say which rule, section
   or FAQ entry it touches and why the current wording falls short.
2. If there is agreement, open a pull request that changes **only `SPEC.md`** (and, if the change
   needs it, `templates/`, `assets/js/datever.js` or `templates/llms.txt` so the site and its tools
   match). The specification text is the source of truth: the site is built from it, never edited
   to disagree with it.
3. Keep to the specification's style: RFC 2119 key words in capitals, short rules, examples in code.
4. By contributing you agree that your contribution to the specification is licensed under
   [CC BY 4.0](LICENSE.md), and that your contribution to the website's code is licensed to Stux.Group
   under the same terms as the rest of that code.

**A spec change releases a new spec version, dated per DateVer itself.** The maintainers will:

1. Move the previous `SPEC.md` to `spec-archive/<old version>.md` so its permanent page and `.md` keep working
2. Set the first heading of `SPEC.md` to the release date (`# Date Versioning YY.MM.DD`, or `YY.MM.DD-N`)
3. Release the site at the same version (see below)

## Local setup

```
git clone https://github.com/StuxGroup/DateVersioning.git
cd DateVersioning
pip install -r requirements.txt
./dev-server.sh
```

Python 3 and the pinned `markdown` package are the only requirements. `dev-server.sh` (or
`dev-server.bat`) runs `scripts/build.py`, then serves `_site/`. Pass `--no-dev-mode` to see the site
as production does (no dev banner). Changes need a rebuild: stop the server and run it again.

## Project conventions

- **The specification lives once, in `SPEC.md`.** Never paste it into HTML. `scripts/build.py` renders
  it, and checks it has the two `regex` blocks the tools read.
- Plain CSS and vanilla JS, no framework. Colour tokens live on `:root`; light and dark follow
  `prefers-color-scheme`. Accent teal `#0f9f8f`.
- The site makes no external requests beyond the Stux.Group logo in the footer. If you add one,
  update the Privacy Policy (`pages/legal-privacy.html`).
- Legal pages' text lives in `pages/legal-*.html`; the hub, sitemap and everything else is generated.
- Changelog sections are ordered Added, Changed, Fixed, Removed, Security, Deprecated, with fixed
  colours (`#2ecc71`, `#3ba7ff`, `#ffa64d`, `#ff4d4d`, `#b06bff`, `#8a8a94`). The build sorts them with
  an explicit order array, unknown types last.

## Versioning and changelog

This project versions itself with Date Versioning.

- The version lives in `VERSION.md` (a bare version, e.g. `26.10.01`); it is today's UTC date, with
  `-N` for further releases the same day
- Every release gets a `CHANGELOG.md` entry headed `## vYY.MM.DD` with `###` subsections, never a
  bare bullet list under a version
- `commit.sh` (bash) and `commit.bat` (Windows) read `VERSION.md` and handle the commit and
  `git tag vYY.MM.DD`; the release workflow publishes a GitHub Release when the tag is pushed

## Before committing

- Run the build and click through the home page tools and the changed pages in both light and dark
- Check `/spec.md` is byte-identical to `SPEC.md` (CI does too)
