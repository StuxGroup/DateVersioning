#!/usr/bin/env python3
"""Build the Date Versioning website into _site/.

SPEC.md is the single source of the specification. This script renders it (with the `markdown`
package: toc, tables, fenced_code and attr_list, so headings get the same anchor ids as GitHub)
into the HTML templates, copies it verbatim to /spec.md and to a permanent /spec/<version>/ page,
and writes the rest of the site (changelogs, legal pages, sitemap, llms.txt, datever.json, ...).

Usage: python scripts/build.py          (from anywhere; needs `pip install -r requirements.txt`)

Copyright (c) 2026 Stux.Group. All rights reserved.
"""
import datetime
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.exit("The 'markdown' package is missing. Run: pip install -r requirements.txt")

import spec_formats  # noqa: E402  (scripts/ is on sys.path when this file is run)

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
BASE_URL = "https://" + (ROOT / "CNAME").read_text(encoding="utf-8").strip()
ACCENT_HEX = "0f9f8f"
YEAR_START = 2026

# Changelog section types always render in this order (unknown types last), whatever order the
# markdown lists them in. Badge colours live in assets/css/style.css (.cl-label-*).
CHANGELOG_ORDER = ["Added", "Changed", "Fixed", "Removed", "Security", "Deprecated"]

LEGAL = [
    ("privacy", "Privacy Policy", "What we collect (nothing) and which requests your browser makes."),
    ("terms", "Terms and Ethics", "The rules for using the site, and using it responsibly."),
    ("cookies", "Cookies Policy", "No cookies, no browser storage, no tracking."),
    ("imprint", "Imprint", "Who operates this site and how to reach them."),
    ("disclaimer", "Disclaimer", "Licence, copyright, accuracy and third-party links."),
    ("opt-out", "Opt-Out Preferences", "There's nothing to sell, so nothing to opt out of."),
]


# --------------------------------------------------------------------------- helpers

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    out = SITE / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def fill(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def git_date(*sources: str) -> str:
    """Date (YYYY-MM-DD) of the last commit touching any of the sources; '' if none has history."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *sources], cwd=ROOT,
                             capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        return ""
    return out


# --------------------------------------------------------------------------- the specification

def spec_info(spec: str) -> tuple[str, str]:
    """(title, version) from SPEC.md's first heading, e.g. ('Date Versioning', '26.10.01')."""
    first = next((ln for ln in spec.splitlines() if ln.startswith("# ")), "")
    m = re.match(r"#\s+(.*?)\s+((?:\d{2}|[1-9]\d{3,})\.\d{2}\.\d{2}(?:-[1-9][0-9]*)?)\s*$", first)
    if not m:
        sys.exit("SPEC.md's first heading must be '# <name> YY.MM.DD'.")
    return m.group(1), m.group(2)


def spec_regexes(spec: str) -> tuple[str, str]:
    """The two ```regex blocks of SPEC.md: with and without named groups."""
    blocks = re.findall(r"```regex\n(.*?)\n```", spec, flags=re.S)
    if len(blocks) != 2:
        sys.exit("SPEC.md must contain exactly two ```regex blocks (named groups, then plain).")
    return blocks[0].strip(), blocks[1].strip()


LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+")


def prepare_markdown(text: str) -> str:
    """Make GitHub-flavoured list layout parse the same way in Python-Markdown (which wants four-space
    indents for nested content and a blank line before a nested list). Only whitespace changes."""
    out: list[str] = []
    in_fence = False
    shift = False  # inside a list item whose marker is one digit wide ("1. "), content indented 3
    prev = ""
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            prev = line
            continue
        if in_fence:
            out.append(line)
            continue
        m = re.match(r"^(\d)\.\s", line)
        if m:
            shift = True
        elif re.match(r"^(\d{2,})\.\s", line) or (line and not line.startswith(" ")):
            shift = False
        if shift and line.startswith("   ") and line.strip():
            line = " " + line
        lm = LIST_RE.match(line)
        if lm and prev.strip():
            pm = LIST_RE.match(prev)
            if not pm or len(lm.group(1)) > len(pm.group(1)):
                out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def autolink(fragment: str) -> str:
    """Link bare http(s) URLs in text (GitHub does this for SPEC.md), outside code and links."""
    parts = re.split(r"(<[^>]+>)", fragment)
    skip = 0
    for i, part in enumerate(parts):
        if part.startswith("<"):
            tag = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            if tag and tag.group(1).lower() in ("a", "code", "pre"):
                skip += -1 if part.startswith("</") else 1
            continue
        if skip > 0:
            continue

        def repl(m: re.Match) -> str:
            url = m.group(0)
            trail = ""
            while url and url[-1] in ".,;:!?":
                trail = url[-1] + trail
                url = url[:-1]
            return f'<a href="{url}">{url}</a>{trail}'

        parts[i] = re.sub(r"https?://[^\s<>\"')]+", repl, part)
    return "".join(parts)


def render_spec(spec: str):
    """Render SPEC.md. Returns (title_html, lead_html, sections, toc_tokens) where `sections` maps
    each h2 id to its HTML (heading included), in document order, and `lead_html` is what sits
    between the h1 and the first h2."""
    md = markdown.Markdown(
        extensions=["toc", "tables", "fenced_code", "attr_list"],
        extension_configs={"toc": {"permalink": "#", "permalink_title": "Link to this section", "permalink_class": "headerlink"}},
    )
    body = md.convert(prepare_markdown(spec))
    body = autolink(body)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    tokens = md.toc_tokens  # [{'level':1, 'id':..., 'name':..., 'children':[...]}]

    pieces = re.split(r'(?=<h2 id=")', body)
    head = pieces[0]
    h1 = re.search(r"<h1[^>]*>.*?</h1>", head, flags=re.S)
    lead = head.replace(h1.group(0), "", 1) if h1 else head
    sections: list[tuple[str, str]] = []
    for piece in pieces[1:]:
        sid = re.match(r'<h2 id="([^"]+)"', piece).group(1)
        sections.append((sid, piece))
    # toc_tokens nest everything under the h1; use its children (the h2s).
    h2s = tokens[0]["children"] if tokens and tokens[0]["level"] == 1 else tokens
    return (h1.group(0) if h1 else ""), lead, sections, h2s


def formats_links(base: str) -> str:
    """'<a>.md</a>, <a>.txt</a>, ...': the other formats of one specification URL."""
    return ", ".join(f'<a href="/{base}.{ext}">.{ext}</a>' for ext in ("md", "txt", "json", "xml"))


def toc_html(entries) -> str:
    """entries: [(id, name, [(id, name), ...])] -> nested <ul>."""
    items = []
    for sid, name, kids in entries:
        sub = ""
        if kids:
            sub = "<ul>" + "".join(f'<li><a href="#{k}">{esc(n)}</a></li>' for k, n in kids) + "</ul>"
        items.append(f'<li><a href="#{sid}">{esc(name)}</a>{sub}</li>')
    return "<ul>" + "".join(items) + "</ul>"


# --------------------------------------------------------------------------- changelog

def render_changelog(md_text: str) -> str:
    """Render CHANGELOG.md: one card per `## release`, `###` sections sorted into CHANGELOG_ORDER."""
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list"])
    releases = re.split(r"(?m)^##\s+", md_text.replace("\r\n", "\n"))[1:]
    cards = []
    for rel in releases:
        heading, _, rest = rel.partition("\n")
        chunks = re.split(r"(?m)^###\s+", rest)
        intro = chunks[0].strip()
        sections = []
        for idx, chunk in enumerate(chunks[1:]):
            name, _, body = chunk.partition("\n")
            name = name.strip()
            rank = next((i for i, t in enumerate(CHANGELOG_ORDER) if t.lower() == name.lower()), len(CHANGELOG_ORDER))
            sections.append((rank, idx, name, body.strip()))
        sections.sort(key=lambda s: (s[0], s[1]))
        parts = [f"<h2>{esc(heading.strip())}</h2>"]
        if intro:
            parts.append(f'<div class="cl-msg">{md.reset().convert(intro)}</div>')
        for rank, _idx, name, body in sections:
            label = CHANGELOG_ORDER[rank] if rank < len(CHANGELOG_ORDER) else name
            cls = f"cl-label cl-label-{label.lower()}" if rank < len(CHANGELOG_ORDER) else "cl-label"
            parts.append(f'<span class="{cls}">{esc(label)}</span>')
            parts.append(md.reset().convert(body).replace("<ul>", '<ul class="cl-list">'))
        cards.append('<article class="cl-entry">' + "".join(parts) + "</article>")
    return "".join(cards) or '<p class="cl-msg">No changelog entries yet.</p>'


# --------------------------------------------------------------------------- the site

class Site:
    def __init__(self) -> None:
        self.spec = read(ROOT / "SPEC.md")
        self.spec_name, self.spec_version = spec_info(self.spec)
        self.regex_named, self.regex_plain = spec_regexes(self.spec)
        self.site_version = read(ROOT / "VERSION.md").strip()
        self.base_tpl = read(ROOT / "templates" / "base.html")
        year = datetime.datetime.now(datetime.timezone.utc).year
        self.year_text = str(year) if YEAR_START >= year else f"{YEAR_START}–{year}"
        self.pages: list[dict] = []  # for the sitemap: path, label, description, sources, priority, freq

    # -- page shell
    def page(self, path: str, title: str, description: str, content: str, *, scripts: str = "",
             robots: bool = True, sitemap: dict | None = None, filename: str | None = None) -> None:
        canonical = BASE_URL + path
        text = fill(
            self.base_tpl,
            title=esc(title), description=esc(description), canonical=canonical, content=content, scripts=scripts,
            robots="" if robots else '  <meta name="robots" content="noindex">\n',
            year_text=self.year_text, site_version=esc(self.site_version),
        )
        write(filename or (path.lstrip("/") + "index.html"), text)
        if sitemap:
            self.pages.append({"path": path, "title": title, "description": description, **sitemap})

    @staticmethod
    def subpage(crumbs: list[tuple[str, str]], title: str, desc: str, body: str, wrap: str = "prose-page") -> str:
        trail = ['<a href="/">Home</a>']
        for href, label in crumbs:
            trail.append(f'<a href="{href}">{esc(label)}</a>')
        trail.append(f'<span class="bc-cur">{esc(title)}</span>')
        crumb = '<span class="bc-sep">/</span>'.join(trail)
        return f"""    <div class="page-hero">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb">{crumb}</nav>
        <h1 class="page-title">{esc(title)}</h1>
        <p class="page-desc">{desc}</p>
      </div>
    </div>
    <section class="section" style="padding-top: 0;">
      <div class="container">
{body}
      </div>
    </section>"""

    # -- pieces
    def build_assets(self) -> None:
        if SITE.exists():
            shutil.rmtree(SITE)
        SITE.mkdir()
        shutil.copytree(ROOT / "assets", SITE / "assets")
        for name in ("CNAME", "CHANGELOG.md", "VERSION.md"):
            shutil.copyfile(ROOT / name, SITE / name)
        shutil.copyfile(ROOT / "SPEC.md", SITE / "spec.md")  # byte for byte
        write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n")
        write("spec/" + self.spec_version + ".md", self.spec)

    def descriptor(self) -> dict:
        v = self.spec_version
        return {
            "name": self.spec_name,
            "short_name": "DateVer",
            "version": v,
            "url": BASE_URL + "/",
            "spec_url": f"{BASE_URL}/spec/{v}/",
            "spec_markdown_url": f"{BASE_URL}/spec.md",
            "latest_url": f"{BASE_URL}/spec/latest/",
            "latest_markdown_url": f"{BASE_URL}/spec/latest.md",
            "formats": {"extensions": list(spec_formats.FORMATS), "note": "Every specification URL works with each extension: /spec.<ext>, /spec/latest.<ext> and /spec/<version>.<ext>.", "examples": [f"{BASE_URL}/spec/latest.txt", f"{BASE_URL}/spec/{v}.json", f"{BASE_URL}/spec/{v}.xml"]},
            "spec_permalink_markdown_url": f"{BASE_URL}/spec/{v}.md",
            "llms_txt_url": f"{BASE_URL}/llms.txt",
            "repository": "https://github.com/StuxGroup/DateVersioning",
            "maintainer": {"name": "Stux.Group", "url": "https://stux.group"},
            "license": {"spec": "CC-BY-4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
            "format": "YY.MM.DD[-N][+build] for 2000-2099; YYYY.MM.DD[-N][+build] (the full year) from 2100",
            "regex": {"named_groups": self.regex_named, "plain": self.regex_plain, "dialect": "ECMAScript and PCRE"},
            "timezone": "UTC",
            "calendar_check_required": True,
            "precedence": ["YY", "MM", "DD", "N (no -N means 0)"],
            "build_metadata_affects_precedence": False,
            "years": {"from": 2000, "until": None, "short_form": "YY for 2000-2099", "full_form": "the full year, no leading zeros, from 2100 (2100.01.01, 10000.01.01)", "full_form_before_2100_allowed": False},
            "calendar": "Gregorian",
            "semver_form": {
                "major": "the year minus 2000 (YY without leading zeros up to 2099; 2100 -> 100), plus the project's major offset (rule 13; 0 unless declared)",
                "major_offset": "a multiple of 100, chosen once when a project switches from a scheme whose versions would otherwise outrank its SemVer forms; never changes",
                "minor": "MM without leading zeros",
                "patch": "DD * 100 + N (N is 0 when there is no -N suffix)",
                "build_metadata": "carried over unchanged",
                "max_release_number": 99,
                "reverse": {"year": "2000 + MAJOR - offset (written as YY up to 2099, in full from 2100)", "DD": "floor(PATCH / 100)", "N": "PATCH mod 100"},
                "examples": {"26.10.01": "26.10.100", "26.10.01-2": "26.10.102", "05.03.09-4": "5.3.904", "26.10.01 (major offset 100)": "126.10.100", "2100.01.01": "100.1.100", "2345.06.07-1": "345.6.701"},
                "compare_date_versions_with_semver_rules": False,
            },
        }

    def build_home(self) -> None:
        title_h1, lead, sections, h2s = render_spec(self.spec)
        summary = next(html_ for sid, html_ in sections if sid == "summary")
        rest = "".join(html_ for sid, html_ in sections if sid != "summary")
        entries = [("summary", "Summary", []), ("try", "Try it", [])]
        for tok in h2s:
            if tok["id"] == "summary":
                continue
            entries.append((tok["id"], tok["name"], [(c["id"], c["name"]) for c in tok.get("children", [])]))
        entries += [("use-it", "Use it in your project", []), ("ai", "Using Date Versioning with AI tools and programs", [])]
        content = fill(
            read(ROOT / "templates" / "home.html"),
            spec_version=self.spec_version, lead=lead, summary=summary, spec_rest=rest,
            toc=toc_html(entries), accent_hex=ACCENT_HEX,
        )
        data = json.dumps({"regex": {"named": self.regex_named, "plain": self.regex_plain}, "version": self.spec_version})
        scripts = (f'  <script type="application/json" id="datever-data">{data.replace("<", chr(92) + "u003c")}</script>\n'
                   '  <script src="/assets/js/datever.js" defer></script>\n')
        self.page("/", "Date Versioning (DateVer): version numbers that are release dates",
                  "Date Versioning (DateVer) is a versioning standard in which a version is the date it was released: YY.MM.DD, "
                  "with -1, -2 and so on for further releases the same day. Created and maintained by Stux.Group.",
                  content, scripts=scripts,
                  sitemap={"label": "Home", "sources": ["SPEC.md", "templates/home.html", "templates/base.html"], "priority": "1.0", "freq": "monthly",
                           "blurb": "The specification, a version validator and a next-version tool."})

    def build_spec_pages(self) -> None:
        """/spec/<version>/ for the current SPEC.md, plus any archived specs in spec-archive/<version>.md."""
        specs = {self.spec_version: (self.spec, "SPEC.md")}
        archive = ROOT / "spec-archive"
        if archive.is_dir():
            for f in sorted(archive.glob("*.md")):
                text = read(f)
                _name, ver = spec_info(text)
                if ver != f.stem:
                    sys.exit(f"{f.name}: its heading says {ver}")
                if ver != self.spec_version:
                    specs[ver] = (text, f"spec-archive/{f.name}")
                    write(f"spec/{ver}.md", text)
        for ver, (text, source) in specs.items():
            title_h1, lead, sections, h2s = render_spec(text)
            entries = [(t["id"], t["name"], [(c["id"], c["name"]) for c in t.get("children", [])]) for t in h2s]
            latest = ver == self.spec_version
            note = (f'This is the permanent page for Date Versioning <strong>{esc(ver)}</strong>, which '
                    + ("is the current specification. " if latest else f'has been superseded by <a href="/spec/{esc(self.spec_version)}/">{esc(self.spec_version)}</a>. ')
                    + f'Also as {formats_links("spec/" + ver)}. The latest version is always at <a href="/spec/latest/">/spec/latest/</a>.')
            body = (f'<div class="doc-layout"><aside class="toc" aria-label="Table of contents"><p class="toc-title">On this page</p>{toc_html(entries)}</aside>'
                    f'<div class="prose doc-body"><div class="permalink-note"><p>{note}</p></div>'
                    f'{title_h1}{lead}{"".join(s for _i, s in sections)}</div></div>')
            content = (f'    <section class="section" style="padding-top: 36px;"><div class="container">\n{body}\n    </div></section>')
            self.page(f"/spec/{ver}/", f"Date Versioning {ver}: specification",
                      f"The permanent page for version {ver} of the Date Versioning specification.", content,
                      sitemap={"label": f"Specification {ver}", "sources": [source], "priority": "0.8", "freq": "yearly",
                               "blurb": "The permanent page for this version of the specification."})
            self.write_formats(f"spec/{ver}", text, ver, f"/spec/{ver}/")
            if latest:
                # /spec/latest/ always renders the current specification (not a redirect, so tools that
                # fetch it get the spec itself); /spec/latest.md is its plain text.
                latest_note = (f'This page always shows the latest Date Versioning specification, currently '
                               f'<strong>{esc(ver)}</strong>. To refer to this exact version, link its permanent page, '
                               f'<a href="/spec/{esc(ver)}/">/spec/{esc(ver)}/</a>. Also as {formats_links("spec/latest")}.')
                latest_body = body.replace(f'<div class="permalink-note"><p>{note}</p></div>',
                                           f'<div class="permalink-note"><p>{latest_note}</p></div>', 1)
                self.page("/spec/latest/", "Date Versioning: latest specification",
                          f"The latest version of the Date Versioning specification, currently {ver}.",
                          content.replace(body, latest_body, 1),
                          sitemap={"label": "Latest specification", "sources": [source], "priority": "0.9", "freq": "monthly",
                                   "blurb": f"Always the current specification, now {ver}."})
                self.write_formats("spec/latest", text, ver, "/spec/latest/")
                self.write_formats("spec", text, ver, "/spec/latest/")

    def write_formats(self, base: str, text: str, ver: str, page: str) -> None:
        """<base>.md/.txt/.json/.xml/.html for one specification: change the extension, get that format."""
        urls = {fmt: f"{BASE_URL}/{base}.{fmt}" for fmt in spec_formats.FORMATS}
        urls.update({"page": BASE_URL + page, "permanent": f"{BASE_URL}/spec/{ver}/", "latest": f"{BASE_URL}/spec/latest/"})
        name, _v = spec_info(text)
        data = spec_formats.structure(
            text, name=name, version=ver, latest=self.spec_version, urls=urls, regex=spec_regexes(text),
            license_={"id": "CC-BY-4.0", "name": "Creative Commons Attribution 4.0 International",
                      "url": "https://creativecommons.org/licenses/by/4.0/"},
            prepare=prepare_markdown)
        header = "\n".join([
            f"Plain-text version of {BASE_URL}{page}",
            f"Other formats: change the extension of {BASE_URL}/{base}.txt to .md, .json, .xml or .html.",
            f"Latest specification: {BASE_URL}/spec/latest.txt",
            f"Copyright (c) {YEAR_START} Stux.Group. Licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).",
        ])
        write(base + ".md", text)
        write(base + ".txt", spec_formats.to_text(text, prepare_markdown, header))
        write(base + ".json", spec_formats.to_json(data))
        write(base + ".xml", spec_formats.to_xml(data))
        shutil.copyfile(SITE / page.strip("/") / "index.html", SITE / (base + ".html"))

    def build_changelogs(self) -> None:
        cards = render_changelog(read(ROOT / "CHANGELOG.md"))
        body = (f'<div class="cl-wrap"><p class="cl-current">Current version: <span class="mono">v{esc(self.site_version)}</span></p>'
                f'<div>{cards}</div></div>')
        desc = ('What changed on this site and in the specification, release by release, newest first. Source: '
                '<a href="https://github.com/StuxGroup/DateVersioning/blob/main/CHANGELOG.md">CHANGELOG.md</a>.')
        self.page("/changelogs/", "Changelogs - Date Versioning", "Release notes for Date Versioning, release by release.",
                  self.subpage([], "Changelogs", desc, body),
                  sitemap={"label": "Changelogs", "sources": ["CHANGELOG.md"], "priority": "0.3", "freq": "monthly",
                           "blurb": "Release notes, release by release, newest first."})
        # /changelog/ -> /changelogs/
        write("changelog/index.html", f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Changelogs - Date Versioning</title>
<link rel="canonical" href="{BASE_URL}/changelogs/">
<meta name="robots" content="noindex">
<!-- /changelog/ moved to /changelogs/; keep any #hash when redirecting. -->
<script>location.replace("/changelogs/" + location.hash);</script>
<meta http-equiv="refresh" content="0; url=/changelogs/">
</head>
<body><p>Redirecting to <a href="/changelogs/">/changelogs/</a>.</p></body>
</html>
""")

    def build_legal(self) -> None:
        cards = "".join(
            f'<a href="/legal/{slug}/" class="legal-card"><div class="legal-card-name">{esc(title)}</div>'
            f'<div class="legal-card-desc">{esc(desc)}</div></a>' for slug, title, desc in LEGAL)
        body = (f'<div class="legal-grid">{cards}</div>'
                '<p style="margin-top: 2rem; font-size: 0.85rem; color: var(--text-faint);">Questions about any of this? Contact '
                '<a href="mailto:legal@stux.group">legal@stux.group</a>.</p>')
        self.page("/legal/", "Boring Legal Stuff - Date Versioning",
                  "Privacy, terms, cookies, imprint, disclaimer and opt-out preferences for Date Versioning.",
                  self.subpage([], "Boring Legal Stuff", "The stuff nobody reads but everybody needs. All of it, in one place, in plain English.", body),
                  sitemap={"label": "Boring Legal Stuff", "sources": ["scripts/build.py"], "priority": "0.3", "freq": "yearly",
                           "blurb": "Privacy, terms, cookies, imprint, disclaimer and opt-out preferences."})
        for slug, title, desc in LEGAL:
            src = ROOT / "pages" / f"legal-{slug}.html"
            meta, _, page_body = read(src).partition("\n---\n")
            fm = dict(line.split(": ", 1) for line in meta.strip().splitlines())
            inner = ('<div class="prose-page"><p class="prose-meta">Effective: 1 October 2026</p>'
                     f'<div class="prose-body">\n{page_body.strip()}\n</div></div>')
            self.page(f"/legal/{slug}/", f"{fm['title']} - Date Versioning", fm["description"],
                      self.subpage([("/legal/", "Boring Legal Stuff")], fm["title"], esc(fm["description"]), inner),
                      sitemap={"label": fm["title"], "sources": [f"pages/legal-{slug}.html"], "priority": "0.2", "freq": "yearly",
                               "blurb": fm["description"]})

    def build_404(self) -> None:
        content = """    <section class="not-found">
      <div class="code">404</div>
      <h1>Page not found</h1>
      <p>Whatever you were looking for isn't here: the link might be old, or the page might have moved.</p>
      <a class="btn btn-primary" href="/">&larr; Back to Date Versioning</a>
    </section>"""
        self.page("/404.html", "Page Not Found - Date Versioning", "Page not found: Date Versioning.", content,
                  robots=False, filename="404.html")

    def build_sitemap(self) -> None:
        self.pages.sort(key=lambda p: (-float(p["priority"]), p["path"]))
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for p in self.pages + [self.sitemap_self()]:
            lines.append("  <url>")
            lines.append(f"    <loc>{esc(BASE_URL + p['path'])}</loc>")
            mod = git_date(*p["sources"])
            if mod:
                lines.append(f"    <lastmod>{mod}</lastmod>")
            lines.append(f"    <changefreq>{p['freq']}</changefreq>")
            lines.append(f"    <priority>{p['priority']}</priority>")
            lines.append("  </url>")
        lines.append("</urlset>")
        write("sitemap.xml", "\n".join(lines) + "\n")

        cards = "".join(
            f'<a href="{esc(p["path"])}" class="legal-card"><div class="legal-card-desc">{esc(BASE_URL + p["path"])}</div>'
            f'<div class="legal-card-name">{esc(p["label"])}</div><div class="legal-card-desc">{esc(p["blurb"])}</div></a>'
            for p in self.pages + [self.sitemap_self()])
        extras = ('<p style="margin-top: 2rem; font-size: 0.9rem; color: var(--text-muted);">Also: '
                  '<a href="/spec.md">/spec.md</a>, <a href="/llms.txt">/llms.txt</a>, <a href="/datever.json">/datever.json</a>.</p>')
        body = f'<div class="legal-grid">{cards}</div>{extras}'
        # The sitemap page itself is listed; build it last so the list is complete.
        write("sitemap/index.html", fill(
            self.base_tpl,
            title="Sitemap - Date Versioning", description="Every page on Date Versioning, with a link to the XML sitemap.",
            canonical=BASE_URL + "/sitemap/", robots="", scripts="", year_text=self.year_text, site_version=esc(self.site_version),
            content=self.subpage([], "Sitemap", 'Every page on this site. Looking for the XML version? <a href="/sitemap.xml">sitemap.xml</a>', body),
        ))

    def sitemap_self(self) -> dict:
        return {"path": "/sitemap/", "label": "Sitemap", "blurb": "Every page on this site, with a link to the XML version.",
                "sources": ["scripts/build.py"], "priority": "0.1", "freq": "monthly"}

    def build_text_files(self) -> None:
        write("llms.txt", fill(read(ROOT / "templates" / "llms.txt"), spec_version=self.spec_version, base=BASE_URL))
        write("datever.json", json.dumps(self.descriptor(), indent=2, ensure_ascii=False) + "\n")

    def run(self) -> None:
        self.build_assets()
        self.build_home()
        self.build_spec_pages()
        self.build_changelogs()
        self.build_legal()
        self.build_404()
        self.build_text_files()
        self.build_sitemap()
        print(f"Built {SITE} for {BASE_URL}: spec {self.spec_version}, site v{self.site_version}, {len(self.pages) + 1} sitemap pages")


if __name__ == "__main__":
    Site().run()
