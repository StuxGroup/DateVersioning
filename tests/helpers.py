"""Shared bits for the tests: the repository root, scripts/build.py as a module, and one site build per run."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402  (scripts/build.py)

# The specification's pattern for 2000-2099 (calendar validity is checked separately).
DATEVER = re.compile(r"^[0-9]{2}\.(0[1-9]|1[0-2])\.(0[1-9]|[12][0-9]|3[01])(?:-[1-9][0-9]*)?$")

_built = False


def built_site() -> Path:
    """Build the site into _site/ once per test run, and return its path."""
    global _built
    if not _built:
        build.Site().run()
        _built = True
    return build.SITE


def html_pages() -> list[Path]:
    """Every HTML page in the built site."""
    return sorted(built_site().rglob("*.html"))
