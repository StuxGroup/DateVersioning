<p align="center">
  <img src="https://global.media.stux.group/logo.png" height="100" alt="Stux.Group Logo">
</p>

# Date Versioning (DateVer)

### *Version numbers that are release dates.*

**Date Versioning** is a versioning standard in which a version number is the date it was released:
`YY.MM.DD`, with `-1`, `-2` and so on for further releases made on the same day. It is created and
maintained by [Stux.Group](https://stux.group), and its home is **[datevers.ing](https://datevers.ing)**.

## Summary

Given a release, its version is:

1. `YY.MM.DD`, the UTC date of the release, with every part two digits (`26.10.01`), or
2. `YY.MM.DD-N` when it is not the first release on that date, where `N` counts the extra releases
   that day, starting at 1 (`26.10.01-1`, `26.10.01-2`, ...).

Later versions always have greater precedence: dates compare in order, and on the same date
`26.10.01` < `26.10.01-1` < `26.10.01-2`. Date Versions are **not** SemVer; the specification
explains the differences and gives a SemVer form for registries that need one.

Read the full specification in [SPEC.md](SPEC.md), at [datevers.ing](https://datevers.ing), or as
plain text at <https://datevers.ing/spec.md> (also [/llms.txt](https://datevers.ing/llms.txt) and
[/datever.json](https://datevers.ing/datever.json) for AI tools and programs).

Using it? Add a badge to your README:

```markdown
[![DateVer](https://img.shields.io/badge/DateVer-YY.MM.DD-0f9f8f)](https://datevers.ing)
```

## This repository

| Path | What it is |
|---|---|
| `SPEC.md` | The specification. The single source of truth; it is never copied into HTML by hand |
| `scripts/build.py` | Renders `SPEC.md` into the templates and writes the whole site to `_site/` |
| `templates/`, `pages/`, `assets/` | Page templates, the legal pages' text, and CSS/JS/icons |
| `CHANGELOG.md`, `VERSION.md` | Release notes and the current version, in Date Versioning itself |

This repository versions itself with Date Versioning: `VERSION.md` holds `26.10.01`, tags are `v26.10.01`.

## How the site is built

`scripts/build.py` (Python 3, with the pinned [`markdown`](https://pypi.org/project/Markdown/) package
in `requirements.txt`) renders `SPEC.md` with the `toc`, `tables`, `fenced_code` and `attr_list`
extensions, so headings get the same anchor ids as on GitHub. It writes `_site/` with:

- `/`, the home page: the specification with a "Next version" and a "Validate" tool
- `/spec.md`, a byte-for-byte copy of `SPEC.md`, and `/spec/<version>/` plus `/spec/<version>.md`, a
  permanent page and file for each version (the version comes from `SPEC.md`'s first heading)
- `/llms.txt` and `/datever.json`
- `/changelogs/` (with `/changelog/` redirecting), `/legal/` ("Boring Legal Stuff") and its six pages,
  `/sitemap/`, `sitemap.xml`, `robots.txt` and `404.html`

`.github/workflows/pages.yml` runs the build and deploys `_site/` to GitHub Pages.

## Local development

```
pip install -r requirements.txt
./dev-server.sh                      # builds, then serves _site/ at http://127.0.0.1:8080, DEV_MODE forced on
./dev-server.sh 3000 --no-dev-mode   # another port, and behave like production
```

On Windows use `dev-server.bat`. Changes need a rebuild: stop the server and run it again. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Releasing

1. Update `CHANGELOG.md` (sections in the order Added, Changed, Fixed, Removed, Security, Deprecated)
2. Bump `VERSION.md` to today's UTC date as a Date Version (`YY.MM.DD`, or `YY.MM.DD-N` if there was already a release today)
3. If the specification changed, update the version in `SPEC.md`'s first heading to match
4. Update this README if relevant
5. Run `./commit.sh` (or `commit.bat`): it reads `VERSION.md`, commits, and tags `vYY.MM.DD`
6. `git push origin main --tags`; the release workflow then publishes a GitHub Release from the
   matching `CHANGELOG.md` section

## License

The specification (`SPEC.md` and the specification pages) is &copy; Stux.Group and licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The website's code and design are
&copy; Stux.Group, all rights reserved. See [LICENSE.md](LICENSE.md).

---

*Date Versioning is a versioning standard created and maintained by [Stux.Group](https://stux.group)
<img src="https://global.media.stux.group/icon.png" height="14" alt="Stux.Group" valign="middle">.*

"Stux.Group" is the trading name of **Stux Group Ltd**, a company registered in England and Wales (company no. 13160574), registered office 82a James Carter Road, Mildenhall, England, IP28 7DE.
