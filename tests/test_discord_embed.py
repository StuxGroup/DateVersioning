"""Discord component embeds (https://docs.discord.com/developers/link-previews/component-embeds): every
page but the 404 carries one valid, small-enough embed in its <head>, and data is escaped."""
import json
import re
import unittest

from helpers import build, built_site, html_pages

EMBED = re.compile(r'<script id="discord:component-embed" type="application/json">(.*?)</script>', re.S)
ALLOWED_TYPES = {1, 2, 9, 10, 11, 12, 14, 17}
BUTTON_KEYS = {"id", "type", "url", "style", "label", "emoji", "disabled"}


def walk(component):
    yield component
    for child in component.get("components", []):
        yield from walk(child)
    if isinstance(component.get("accessory"), dict):
        yield from walk(component["accessory"])


def embed_json(path):
    return json.loads(EMBED.search(path.read_text(encoding="utf-8")).group(1))


class DiscordEmbedTest(unittest.TestCase):
    def assert_valid_payload(self, data: str, where: str):
        self.assertLessEqual(len(data.encode("utf-8")), build.DISCORD_EMBED_MAX_BYTES, f"{where}: over 3,000 bytes")
        root = json.loads(data)["component"]
        self.assertEqual(17, root["type"], f"{where}: the root must be one Container")
        nodes = list(walk(root))
        self.assertLessEqual(len(nodes), 40, f"{where}: more than 40 components")
        self.assertEqual(1, sum(1 for c in nodes if c["type"] == 17), f"{where}: nested Container")
        for c in nodes:
            self.assertIn(c["type"], ALLOWED_TYPES, f"{where}: component type {c['type']} isn't allowed")
            if c["type"] == 2:
                self.assertEqual(5, c["style"], f"{where}: buttons must be link buttons")
                self.assertLessEqual(set(c), BUTTON_KEYS, f"{where}: button has keys Discord rejects")
                self.assertRegex(c["url"], r"^https?://", f"{where}: button URL must be http(s)")

    def test_every_page_has_one_valid_embed_except_the_404(self):
        site = built_site()
        checked = 0
        for page in html_pages():
            text = page.read_text(encoding="utf-8")
            if "<head" not in text:
                continue
            where = str(page.relative_to(site))
            if page == site / "404.html":
                self.assertNotIn("discord:component-embed", text, "the 404 page gets no embed")
                continue
            found = EMBED.findall(text)
            self.assertEqual(1, len(found), f"{where}: expected exactly one embed")
            self.assertIn('id="discord:component-embed"', text.split("</head>", 1)[0], f"{where}: belongs in <head>")
            self.assert_valid_payload(found[0], where)
            checked += 1
        self.assertGreaterEqual(checked, 12)

    def test_main_page_types_have_their_own_previews(self):
        site = built_site()
        self.assertIn("Version numbers that are release dates", json.dumps(embed_json(site / "index.html")))
        self.assertIn("Always the current specification", json.dumps(embed_json(site / "spec" / "latest" / "index.html")))
        self.assertIn("release by release", json.dumps(embed_json(site / "changelogs" / "index.html")))
        self.assertIn("Read the specification", json.dumps(embed_json(site / "legal" / "privacy" / "index.html")))

    def test_markdown_is_escaped_with_one_backslash(self):
        self.assertEqual(r"\*\*bold\*\* a\_b", build.discord_md("**bold** a_b"))
        out = build.discord_md("~s~ `c` |p| [l](u) \\ # h\n# head\n> quote\n- item")
        self.assertNotIn("$1", out)
        self.assertEqual(r"\~s\~ \`c\` \|p\| \[l\](u) \\ # h" + "\n" + r"\# head" + "\n" + r"\> quote" + "\n" + r"\- item", out)

    def test_page_data_is_escaped_in_the_embed(self):
        tag = build.discord_page_embed("A *b* _c_ ~d~ `e` |f| > [g]", "#h **i**", "https://datevers.ing/x/")
        content = json.loads(EMBED.search(tag).group(1))["component"]["components"][0]["components"][0]["content"]
        self.assertIn(r"A \*b\* \_c\_ \~d\~ \`e\` \|f\| > \[g\]", content)
        self.assertIn("\n" + r"\#h \*\*i\*\*", content)
        self.assertNotIn("$1", content)

    def test_script_close_in_data_cannot_end_the_tag(self):
        tag = build.discord_page_embed("</script><script>alert(1)</script>", "x", "https://datevers.ing/")
        self.assertEqual(1, tag.count("</script>"), "only the real closing tag")
        self.assertIn("<\\/script>", tag)
        self.assert_valid_payload(EMBED.search(tag).group(1), "script test")

    def test_oversized_payload_falls_back_to_a_comment(self):
        tag = build.discord_page_embed("Big", "x" * 4000, "https://datevers.ing/")
        self.assertNotIn("<script", tag)
        self.assertIn("<!-- discord:component-embed left out", tag)


if __name__ == "__main__":
    unittest.main()
