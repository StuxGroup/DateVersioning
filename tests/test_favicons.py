"""The favicon set: files at the site root, the web app manifest, and the same tags in every <head>."""
import json
import struct
import unittest

from helpers import ROOT, build, built_site, html_pages

TAGS = [
    '<link rel="icon" href="/favicon.ico" sizes="48x48">',
    '<link rel="icon" type="image/png" sizes="512x512" href="/assets/img/icon-512.png">',
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
    '<link rel="manifest" href="/site.webmanifest">',
]


def png_info(path):
    """(width, height, colour type) from a PNG's IHDR; colour types 0 and 2 have no alpha channel."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} isn't a PNG"
    width, height, _depth, colour = struct.unpack(">IIBB", data[16:26])
    return width, height, colour


class FaviconTest(unittest.TestCase):
    def test_root_files_are_built(self):
        site = built_site()
        for name in ("favicon.ico", "apple-touch-icon.png", "site.webmanifest"):
            self.assertTrue((site / name).is_file(), f"/{name} is missing from the built site")

    def test_favicon_ico_is_png_in_ico_with_16_32_48(self):
        data = (ROOT / "static" / "favicon.ico").read_bytes()
        reserved, kind, count = struct.unpack("<HHH", data[:6])
        self.assertEqual((0, 1), (reserved, kind))
        sizes = set()
        for i in range(count):
            w, h = data[6 + 16 * i], data[7 + 16 * i]
            offset = struct.unpack("<I", data[18 + 16 * i:22 + 16 * i])[0]
            self.assertEqual(b"\x89PNG", data[offset:offset + 4], "each image is PNG data")
            sizes.add((w or 256, h or 256))
        self.assertLessEqual({(16, 16), (32, 32), (48, 48)}, sizes)

    def test_apple_touch_icon_is_opaque_180(self):
        w, h, colour = png_info(ROOT / "static" / "apple-touch-icon.png")
        self.assertEqual((180, 180), (w, h))
        self.assertIn(colour, (0, 2), "iOS fills transparency with black: it must be opaque")

    def test_manifest(self):
        m = json.loads((ROOT / "static" / "site.webmanifest").read_text(encoding="utf-8"))
        for key in ("name", "short_name", "theme_color", "background_color"):
            self.assertTrue(m.get(key), f"site.webmanifest has no {key}")
        self.assertEqual("/", m["start_url"])
        self.assertEqual("browser", m["display"])
        icons = {(i["sizes"], i.get("purpose", "any")): i["src"] for i in m["icons"]}
        self.assertIn(("192x192", "any"), icons)
        self.assertIn(("512x512", "any"), icons)
        self.assertIn(("512x512", "maskable"), icons)
        for (sizes, purpose), src in icons.items():
            path = ROOT / src.lstrip("/")
            self.assertTrue(path.is_file(), f"{src} is missing")
            w, h, colour = png_info(path)
            self.assertEqual(sizes, f"{w}x{h}", src)
            if purpose == "maskable":
                self.assertIn(colour, (0, 2), "the maskable icon needs an opaque background")

    def test_every_head_has_the_tags(self):
        self.assertEqual(TAGS, [line.strip() for line in build.FAVICON_TAGS.splitlines() if "svg+xml" not in line])
        for page in html_pages():
            text = page.read_text(encoding="utf-8")
            if "<head" not in text:
                continue
            head = text.split("</head>", 1)[0]
            for tag in TAGS:
                self.assertIn(tag, head, f"{page.relative_to(built_site())}: missing {tag}")


if __name__ == "__main__":
    unittest.main()
