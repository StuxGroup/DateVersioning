"""Date Versioning (https://datevers.ing): VERSION.md is the UTC release date as YY.MM.DD, plus -1, -2...
for later releases the same day, and it matches the newest CHANGELOG.md entry."""
import datetime
import re
import unittest

from helpers import DATEVER, ROOT


def version() -> str:
    return (ROOT / "VERSION.md").read_text(encoding="utf-8").strip()


class VersionTest(unittest.TestCase):
    def test_version_is_a_real_date_version(self):
        v = version()
        self.assertRegex(v, DATEVER)
        yy, mm, dd = (int(p) for p in v.split("-")[0].split("."))
        try:
            datetime.date(2000 + yy, mm, dd)
        except ValueError:
            self.fail(f"{v} isn't a real calendar date")

    def test_version_is_not_in_the_future(self):
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%y.%m.%d")
        self.assertLessEqual(version().split("-")[0], today, "a Date Version can't be dated after today (UTC)")

    def test_changelog_leads_with_the_current_version(self):
        m = re.search(r"(?m)^## v(\S+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(m, "CHANGELOG.md has no '## v...' heading")
        self.assertEqual(version(), m.group(1), "the newest CHANGELOG.md entry should be the version in VERSION.md")

    def test_version_md_is_bare(self):
        raw = (ROOT / "VERSION.md").read_text(encoding="utf-8")
        self.assertFalse(raw.lstrip().startswith(("v", "#")), "VERSION.md holds the bare version only")


if __name__ == "__main__":
    unittest.main()
