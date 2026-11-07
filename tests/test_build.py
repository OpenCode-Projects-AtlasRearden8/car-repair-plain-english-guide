"""Test suite for the Car Repair, in Plain English guide build.

Run with:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build as build_mod  # noqa: E402

DOCS = ROOT / "docs"

EXPECTED_DOCS = {
    "index.md": "Car Repair, in Plain English",
    "estimates.md": "Decode the Estimate",
    "obd-codes.md": "Understand OBD-II Codes",
    "questions.md": "Confident Questions",
    "ai-translator.md": "AI Quote Translator",
    "maintenance-primer.md": "Maintenance Primer",
    "about.md": "Questions, About",
}

TRACKING_PATTERNS = [
    r"googletagman", r"gtag\(", r"hotjar", r"mixpanel", r"segment\.io",
    r"cdn\.jsdelivr", r"fonts\.googleapis", r"unpkg\.com",
    r"amazon-adsystem", r"amzn\.to", r"utm_source=", r"utm_medium=",
    r"<script", r"<iframe", r"<img ", r"fetch\(", r"XMLHttpRequest",
    r"localStorage", r"document\.cookie",
]


class _HTMLWellFormedness(HTMLParser):
    """Collect a shallow well-formedness report for an HTML page."""

    VOID = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: D102
        if tag not in self.VOID:
            self._open.append(tag)

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        if getattr(self, "_open", None) is None:
            self._open = []
        if tag in self.VOID:
            return
        if not self._open:
            self.errors.append(f"closing </{tag}> with empty stack")
            return
        if self._open[-1] == tag:
            self._open.pop()
        elif tag in self._open:
            while self._open and self._open[-1] != tag:
                unclosed = self._open.pop()
                self.errors.append(f"unclosed <{unclosed}> before </{tag}>")
            if self._open:
                self._open.pop()
        else:
            self.errors.append(f"stray </{tag}>")


class TestBuild(unittest.TestCase):
    def test_all_docs_present_with_h1(self) -> None:
        for name, title in EXPECTED_DOCS.items():
            path = DOCS / name
            self.assertTrue(path.is_file(), f"missing doc: docs/{name}")
            first = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertTrue(first.startswith("# "), f"{name} missing H1")
            joined = "\n".join(path.read_text(encoding="utf-8").splitlines()[:3])
            self.assertIn(title[:24], joined, f"{name} H1 mismatch: {title}")

    def test_build_outputs_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_tmp = Path(tmp)
            real_site = build_mod.SITE
            build_mod.SITE = site_tmp
            try:
                built = build_mod.build()
            finally:
                build_mod.SITE = real_site
            expected = {n[:-3] + ".html" for n in EXPECTED_DOCS} | {"styles.css"}
            got = {Path(b).name for b in built}
            self.assertEqual(expected, got, f"got={got}")

    def test_markdown_conversion_basics(self) -> None:
        html_out = build_mod.md_to_html(
            "# Title\n\nA **bold** claim with [a link](other.md) and `code`.\n\n"
            "| A | B |\n| --- | --- |\n| 1 | 2 |\n\n```js\nvar x = 1;\n```\n"
        )
        self.assertIn("<h1>Title</h1>", html_out)
        self.assertIn("<strong>bold</strong>", html_out)
        self.assertIn('href="other.html"', html_out)
        self.assertIn("<code>code</code>", html_out)
        self.assertIn("<table>", html_out)
        self.assertIn("<pre>", html_out)


class TestGeneratedSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import subprocess

        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build.py")],
            cwd=ROOT, check=True, capture_output=True,
        )

    def _all_pages(self) -> list[Path]:
        return sorted((ROOT / "site").glob("*.html"))

    def test_every_internal_link_resolves(self) -> None:
        pages = {p.name for p in self._all_pages()} | {"styles.css"}
        for page in self._all_pages():
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="([^"#]+)"', text):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                self.assertIn(href, pages, f"{page.name}: broken href {href}")

    def test_no_local_markdown_links_left_behind(self) -> None:
        for page in self._all_pages():
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="([^"]+\.md)"', text):
                self.fail(f"{page.name} has un-rewritten .md href: {href}")

    def test_no_tracking_keywords(self) -> None:
        joined = "\n".join(p.read_text(encoding="utf-8") for p in self._all_pages())
        for pattern in TRACKING_PATTERNS:
            self.assertIsNone(
                re.search(pattern, joined, re.IGNORECASE),
                f"site contains tracking/affiliate pattern: {pattern}",
            )

    def test_no_external_script_or_style_requests(self) -> None:
        for page in self._all_pages():
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("<script", text, f"{page.name} contains script tag")
            for src in re.findall(r'(?:src|href)="(https?://[^"]+)"', text):
                self.assertIn("dylanasdale.github.io", src, f"{page.name}: external {src}")

    def test_pages_are_well_formed_enough(self) -> None:
        for page in self._all_pages():
            parser = _HTMLWellFormedness()
            parser._open = []
            try:
                parser.feed(page.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                self.fail(f"{page.name} failed to parse: {exc}")
            leftover = [t for t in parser._open if t not in {"html", "body"}]
            self.assertLessEqual(
                len(leftover), 1,
                f"{page.name}: malformed tags, leftover={leftover}, errors={parser.errors[:5]}",
            )
            self.assertLessEqual(len(parser.errors), 2, f"{page.name}: {parser.errors[:5]}")

    def test_every_page_has_nav_footer_disclaimer(self) -> None:
        for page in self._all_pages():
            text = page.read_text(encoding="utf-8")
            self.assertIn("site-nav", text, page.name)
            self.assertIn("site-footer", text, page.name)
            self.assertIn("Education, never diagnosis", text, page.name)
            self.assertIn("Asdale Dynamics, LLC", text, page.name)

    def test_index_nav_links_all_docs(self) -> None:
        idx = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        for name in EXPECTED_DOCS:
            href = name[:-3] + ".html"
            self.assertIn(href, idx, f"index nav missing {href}")


if __name__ == "__main__":
    unittest.main()
