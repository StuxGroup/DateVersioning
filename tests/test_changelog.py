"""The changelogs page: Date Version headings render, and sections use the fixed order and colours."""
import re
import unittest

from helpers import ROOT, build

ORDER = ["Added", "Changed", "Fixed", "Removed", "Security", "Deprecated"]
COLOURS = {"added": "#2ecc71", "changed": "#3ba7ff", "fixed": "#ffa64d", "removed": "#ff4d4d",
           "security": "#b06bff", "deprecated": "#8a8a94"}


class ChangelogTest(unittest.TestCase):
    def test_order_array(self):
        self.assertEqual(ORDER, build.CHANGELOG_ORDER)

    def test_date_version_headings_render(self):
        md = ("# Changelog\n\n## v26.10.23-1\n\n### Fixed\n\n- b\n\n## v26.10.23\n\n### Added\n\n- a\n\n"
              "## v99.12.31\n\n### Changed\n\n- c\n")
        out = build.render_changelog(md)
        self.assertEqual(["v26.10.23-1", "v26.10.23", "v99.12.31"], re.findall(r"<h2>(.*?)</h2>", out))
        self.assertEqual(3, out.count('<article class="cl-entry">'))

    def test_sections_sorted_into_the_fixed_order(self):
        md = ("## v26.10.23\n\n### Deprecated\n\n- d\n\n### Security\n\n- s\n\n### Something else\n\n- x\n\n"
              "### Removed\n\n- r\n\n### Fixed\n\n- f\n\n### Changed\n\n- c\n\n### Added\n\n- a\n")
        labels = re.findall(r'<span class="cl-label[^"]*">(.*?)</span>', build.render_changelog(md))
        self.assertEqual(ORDER + ["Something else"], labels)

    def test_badge_colours(self):
        css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
        for name, hexcode in COLOURS.items():
            found = re.findall(r"\.cl-label-" + name + r"\s*\{\s*--cl:\s*(#[0-9a-fA-F]{6})", css)
            self.assertTrue(found, f"no colour for .cl-label-{name}")
            self.assertEqual({hexcode}, {f.lower() for f in found}, f".cl-label-{name} should be {hexcode}")

    def test_real_changelog_sections_are_in_order(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        for release in re.split(r"(?m)^## ", text)[1:]:
            names = re.findall(r"(?m)^### (.+)$", release)
            ranks = [ORDER.index(n.strip()) for n in names if n.strip() in ORDER]
            self.assertEqual(sorted(ranks), ranks, f"sections out of order in '## {release.splitlines()[0]}'")


if __name__ == "__main__":
    unittest.main()
