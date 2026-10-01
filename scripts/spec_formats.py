"""The specification in every format: change a spec URL's extension and you get that format.

    /spec/<version>.md    the Markdown source, byte for byte
    /spec/<version>.txt   plain text, wrapped at 80 columns
    /spec/<version>.json  structured: metadata, the numbered rules, every section (text and Markdown)
    /spec/<version>.xml   the same structure as XML
    /spec/<version>.html  the web page (the same as /spec/<version>/)

build.py writes these for every version, for /spec/latest.* and for /spec.* (both the latest).

Copyright (c) 2026 Stux.Group. All rights reserved.
"""
import json
import re
import textwrap
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import markdown

FORMATS = ("md", "txt", "json", "xml", "html")
WIDTH = 80
_width: int | None = WIDTH  # None while building the .json/.xml text fields, which aren't wrapped


# --------------------------------------------------------------------------- HTML -> plain text

class _Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or []), parent, []


class _TreeBuilder(HTMLParser):
    VOID = {"br", "hr", "img", "input", "meta", "link"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in self.VOID:
            self.cur = node

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def _inline(node) -> str:
    """Text of an inline run: links become 'text (url)' unless the text is the url or the link is
    a same-page anchor; code, emphasis and the rest become their text."""
    if isinstance(node, str):
        return node
    inner = "".join(_inline(c) for c in node.children)
    if node.tag == "br":
        return "\n"
    if node.tag == "a":
        href = node.attrs.get("href", "")
        if href and not href.startswith("#") and href != inner and href.rstrip("/") != inner.rstrip("/"):
            return f"{inner} ({href})"
    return inner


def _squash(s: str) -> str:
    return re.sub(r"[ \t\r\n]+", " ", s).strip()


def _wrap(text: str, indent: str = "", first: str | None = None) -> str:
    first = indent if first is None else first
    if _width is None:  # data formats: one line per paragraph
        return first + _squash(text)
    return textwrap.fill(_squash(text), _width, initial_indent=first, subsequent_indent=indent,
                         break_long_words=False, break_on_hyphens=False)


def _table(node) -> list[str]:
    rows = []
    for tr in _find(node, "tr"):
        rows.append([_squash(_inline(c)) for c in tr.children if not isinstance(c, str) and c.tag in ("th", "td")])
    if not rows:
        return []
    cols = max(len(r) for r in rows)
    rows = [r + [""] * (cols - len(r)) for r in rows]
    widths = [max(len(r[i]) for r in rows) for i in range(cols)]
    line = lambda r: " | ".join(c.ljust(widths[i]) for i, c in enumerate(r)).rstrip()
    out = [line(rows[0]), "-+-".join("-" * w for w in widths)]
    out += [line(r) for r in rows[1:]]
    return out


def _find(node, tag):
    for c in node.children:
        if isinstance(c, str):
            continue
        if c.tag == tag:
            yield c
        else:
            yield from _find(c, tag)


BLOCK = {"p", "h1", "h2", "h3", "h4", "ol", "ul", "pre", "table", "div", "blockquote", "hr", "li"}
UNDERLINE = {"h1": "=", "h2": "-", "h3": "~"}


def _blocks(node, indent: str = "") -> list[str]:
    """Render a node's block children as a list of text blocks (joined by blank lines)."""
    out: list[str] = []
    run: list = []

    def flush():
        if run:
            text = "".join(_inline(c) for c in run)
            if text.strip():
                out.append(_wrap(text, indent))
            run.clear()

    for c in node.children:
        if isinstance(c, str) or c.tag not in BLOCK:
            run.append(c)
            continue
        flush()
        if c.tag in UNDERLINE:
            title = _squash(_inline(c))
            out.append(f"{indent}{title}\n{indent}{UNDERLINE[c.tag] * len(title)}")
        elif c.tag == "h4":
            out.append(f"{indent}{_squash(_inline(c))}")
        elif c.tag == "p":
            out.append(_wrap(_inline(c), indent))
        elif c.tag == "pre":
            code = "".join(_inline(x) for x in c.children).rstrip("\n")
            out.append("\n".join(indent + "    " + ln for ln in code.split("\n")))
        elif c.tag in ("ol", "ul"):
            n = int(c.attrs.get("start", "1"))
            items, tight = [], True
            for li in (x for x in c.children if not isinstance(x, str) and x.tag == "li"):
                marker = f"{n}. " if c.tag == "ol" else "- "
                n += 1
                sub = indent + " " * len(marker)
                parts = _blocks(li, sub)
                if parts:
                    head = parts[0]
                    # Put the marker on the first line of the item's first block.
                    parts[0] = indent + marker + head[len(sub):] if head.startswith(sub) else indent + marker + head.lstrip()
                    tight = tight and _tight(li)
                    items.append("\n".join(parts) if _tight(li) else "\n\n".join(parts))
            # A tight list (no paragraphs in its items) stays one block, one item per line.
            if tight:
                out.append("\n".join(items))
            else:
                out.extend(items)
            continue
        elif c.tag == "table":
            out.append("\n".join(indent + ln for ln in _table(c)))
        elif c.tag == "hr":
            out.append(indent + "-" * 20)
        else:  # div, blockquote, li outside a list
            out.extend(_blocks(c, indent))
    flush()
    return out


def _tight(li) -> bool:
    """A list item whose content is only inline text and nested lists (no paragraphs)."""
    return not any(not isinstance(c, str) and c.tag == "p" for c in li.children)


def html_to_text(fragment: str, wrap: bool = True) -> str:
    global _width
    _width = WIDTH if wrap else None
    tb = _TreeBuilder()
    tb.feed(fragment)
    tb.close()
    blocks = _blocks(tb.root)
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(blocks)).strip() + "\n"


# --------------------------------------------------------------------------- structure

def _render(md_text: str, prepare) -> tuple[str, list]:
    md = markdown.Markdown(extensions=["toc", "tables", "fenced_code", "attr_list"])
    return md.convert(prepare(md_text)), md.toc_tokens


def _md_sections(spec: str) -> list[tuple[int, str, str]]:
    """[(level, title, markdown body)] for each ## and ### heading, outside code fences."""
    out, cur, fence = [], None, False
    for line in spec.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{2,3})\s+(.*?)\s*$", line)
        if m:
            cur = [len(m.group(1)), m.group(2), []]
            out.append(cur)
        elif cur is not None:
            cur[2].append(line)
    return [(lvl, title, "\n".join(body).strip("\n")) for lvl, title, body in out]


def _rules(rules_md: str) -> list[tuple[int, str]]:
    """The numbered rules: top-level '1. ' items with their indented continuation lines."""
    rules, cur = [], None
    for line in rules_md.split("\n"):
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            cur = [int(m.group(1)), [m.group(2)]]
            rules.append(cur)
        elif cur is not None and (line.startswith(" ") or not line.strip()):
            cur[1].append(line[4:] if line.startswith("    ") else line.strip())
        elif cur is not None and line.strip():
            cur = None
    return [(n, "\n".join(body).strip()) for n, body in rules]


def structure(spec: str, *, name: str, version: str, latest: str, urls: dict, regex: tuple[str, str],
              license_: dict, prepare) -> dict:
    """The specification as data, the shared shape of the .json and .xml formats."""
    _html, toc = _render(spec, prepare)
    h2s = toc[0]["children"] if toc and toc[0]["level"] == 1 else toc
    ids = []
    for t in h2s:
        ids.append(t["id"])
        ids.extend(c["id"] for c in t.get("children", []))

    def text_of(md_text: str) -> str:
        return html_to_text(_render(md_text, prepare)[0], wrap=False).strip()

    sections, parent = [], None
    for i, (lvl, title, body) in enumerate(_md_sections(spec)):
        entry = {"id": ids[i] if i < len(ids) else "", "title": title, "text": text_of(body), "markdown": body}
        if lvl == 2:
            entry["subsections"] = []
            sections.append(entry)
            parent = entry
        elif parent is not None:
            parent["subsections"].append(entry)
    for s in sections:
        if not s["subsections"]:
            del s["subsections"]

    rules_md = next((s["markdown"] for s in sections if s["id"] == "date-versioning-specification-datever"), "")
    rules = [{"number": n, "text": text_of(body), "markdown": body} for n, body in _rules(rules_md)]
    return {
        "name": name,
        "short_name": "DateVer",
        "version": version,
        "latest_version": latest,
        "is_latest": version == latest,
        "urls": urls,
        "license": license_,
        "regex": {"named_groups": regex[0], "plain": regex[1]},
        "rules": rules,
        "sections": sections,
        "markdown": spec,
    }


def to_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def to_xml(data: dict) -> str:
    root = ET.Element("specification", {
        "name": data["name"], "short-name": data["short_name"], "version": data["version"],
        "latest-version": data["latest_version"], "is-latest": str(data["is_latest"]).lower(),
    })
    urls = ET.SubElement(root, "urls")
    for fmt, url in data["urls"].items():
        ET.SubElement(urls, "url", {"format": fmt}).text = url
    ET.SubElement(root, "license", {"id": data["license"]["id"], "href": data["license"]["url"]}).text = data["license"]["name"]
    rx = ET.SubElement(root, "regex")
    ET.SubElement(rx, "pattern", {"groups": "named"}).text = data["regex"]["named_groups"]
    ET.SubElement(rx, "pattern", {"groups": "plain"}).text = data["regex"]["plain"]
    rules = ET.SubElement(root, "rules")
    for r in data["rules"]:
        el = ET.SubElement(rules, "rule", {"number": str(r["number"])})
        ET.SubElement(el, "text").text = r["text"]
        ET.SubElement(el, "markdown").text = r["markdown"]

    def add_sections(parent, items):
        for s in items:
            el = ET.SubElement(parent, "section", {"id": s["id"], "title": s["title"]})
            ET.SubElement(el, "text").text = s["text"]
            ET.SubElement(el, "markdown").text = s["markdown"]
            if s.get("subsections"):
                add_sections(el, s["subsections"])

    add_sections(ET.SubElement(root, "sections"), data["sections"])
    ET.SubElement(root, "markdown").text = data["markdown"]
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def to_text(spec: str, prepare, header: str) -> str:
    html_, _ = _render(spec, prepare)
    return header + "\n\n" + html_to_text(html_)
