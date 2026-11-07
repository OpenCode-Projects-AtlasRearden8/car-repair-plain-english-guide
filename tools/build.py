#!/usr/bin/env python3
"""Build the static HTML site from the Markdown docs in docs/.

Output: site/*.html (one page per doc) + site/styles.css.
No network access, no dependencies beyond Python 3.9+ and the
`markdown` package (with a stdlib-only fallback for most features used).
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = ROOT / "site"

NAV_ORDER = [
    ("index.md", "Start Here"),
    ("estimates.md", "Decode the Estimate"),
    ("obd-codes.md", "OBD-II Codes"),
    ("questions.md", "Confident Questions"),
    ("ai-translator.md", "AI Quote Translator"),
    ("maintenance-primer.md", "Maintenance Primer"),
    ("about.md", "About & Disclaimer"),
]

FOOTER = (
    "Education, never diagnosis — always ask a qualified mechanic about your specific car. "
    "No tracking, no cookies, no affiliate links. "
    'Content licensed <a href="about.html">MIT</a> · '
    '<a href="https://dylanasdale.github.io" rel="noopener">Asdale Dynamics, LLC</a> · 2026'
)


def md_to_html(text: str) -> str:
    """Convert markdown to HTML, mapping internal `.md` hrefs to `.html`."""
    try:
        import markdown  # type: ignore

        body = markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "sane_lists", "smarty"],
            output_format="html5",
        )
    except ImportError:  # pragma: no cover - fallback path
        body = _fallback_markdown(text)

    return _rewrite_links(body, lambda href: href[:-3] + ".html") + "\n"


_LINK_RE = re.compile(r'(<a\s[^>]*?href=")([^"]+?)(")')


def _rewrite_links(body: str, rewrite: Callable[[str], str]) -> str:
    def _sub(m: re.Match[str]) -> str:
        href = m.group(2)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        if href.endswith(".md"):
            return f"{m.group(1)}{rewrite(href)}{m.group(3)}"
        return m.group(0)

    return _LINK_RE.sub(_sub, body)


def _escape_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def _fallback_markdown(text: str) -> str:  # pragma: no cover - stdlib fallback
    out_lines: list[str] = []
    in_code = False
    code_lines: list[str] = []
    list_open: str | None = None
    in_table: bool = False
    table_rows: list[list[str]] = []

    def flush_table() -> str:
        if not table_rows:
            return ""
        html_rows = ["<table>", "<thead>"]
        html_rows.append("<tr>" + "".join(f"<th>{c}</th>" for c in table_rows[0]) + "</tr>")
        html_rows.append("</thead><tbody>")
        for row in table_rows[1:]:
            html_rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
        html_rows.append("</tbody></table>")
        return "\n".join(html_rows)

    def close_list() -> str:
        nonlocal list_open
        if list_open:
            tag = list_open
            list_open = None
            return f"</{tag}>\n"
        return ""

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                code = html.escape("\n".join(code_lines))
                out_lines.append(f"<pre><code>{code}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                out_lines.append(close_list() + flush_table())
                table_rows.clear()
                in_table = False
                in_code = True
            continue
        if in_code:
            code_lines.append(raw)
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [ _escape_inline(c.strip()) for c in line.strip("|").split("|") ]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue  # separator row
            if not in_table:
                in_table = True
                table_rows.append(cells)
            else:
                table_rows.append(cells)
            continue
        if in_table:
            out_lines.append(close_list() + flush_table())
            table_rows.clear()
            in_table = False
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = _escape_inline(stripped[level:].strip())
            out_lines.append(close_list() + f"<h{level}>{title}</h{level}>")
        elif re.match(r"^[-*]\s+", stripped):
            if list_open != "ul":
                out_lines.append(close_list() + "<ul>")
                list_open = "ul"
            out_lines.append(f"<li>{_escape_inline(re.sub(chr(94) + r'[-*]\\s+', '', stripped))}</li>")
        elif re.match(r"^\d+\.\s+", stripped):
            if list_open != "ol":
                out_lines.append(close_list() + "<ol>")
                list_open = "ol"
            out_lines.append(f"<li>{_escape_inline(re.sub(chr(94) + r'\\d+\\.\\s+', '', stripped))}</li>")
        elif not stripped:
            out_lines.append(close_list())
        elif stripped.startswith(">"):
            out_lines.append(f"<blockquote><p>{_escape_inline(stripped.lstrip('> ').strip())}</p></blockquote>")
        elif stripped == "---":
            out_lines.append(close_list() + "<hr>")
        else:
            out_lines.append(f"<p>{_escape_inline(stripped)}</p>")
    out_lines.append(close_list() + flush_table())
    return "\n".join(out_lines)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index, follow, noai">
<title>{title} · Car Repair, in Plain English</title>
<meta name="description" content="{description}">
<!-- Static site: no tracking, no cookies, no ads, no affiliate links, no external requests. -->
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="index.html">Car Repair, <span>in Plain English</span></a>
  <p class="tagline">Education, never diagnosis · like a friend would explain it</p>
</header>
<nav class="site-nav" aria-label="Guide contents">
{nav}
</nav>
<main class="content">
{body}
</main>
<footer class="site-footer">
  <p>{footer}</p>
</footer>
</body>
</html>
"""


def render_nav(active: str) -> str:
    items = []
    for md_name, label in NAV_ORDER:
        href = md_name[:-3] + ".html"
        cls = ' class="active"' if md_name == active else ""
        items.append(f'  <a href="{href}"{cls}>{html.escape(label)}</a>')
    return "\n".join(items)


def build(dry_run: bool = False) -> list[str]:
    if not DOCS.is_dir():
        raise SystemExit(f"docs/ not found at {DOCS}")
    SITE.mkdir(parents=True, exist_ok=True)

    built: list[str] = []
    for md_path in sorted(DOCS.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        body = md_to_html(text)
        if md_path.name == "index.md":
            title, description = "Start Here", (
                "Decode estimate line items, ask confident questions, understand "
                "OBD-II codes, and translate repair quotes into plain English."
            )
        else:
            h1 = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            first_p = re.search(r"^\*\*(.{20,160}?)\*\*", text, re.MULTILINE)
            title = h1.group(1).strip() if h1 else md_path.stem
            description = (first_p.group(1).strip() if first_p else title)[:200]
        page = PAGE_TEMPLATE.format(
            title=html.escape(title),
            description=html.escape(description, quote=True),
            nav=render_nav(md_path.name),
            body=body,
            footer=FOOTER,
        )
        out_path = SITE / (md_path.stem + ".html")
        if not dry_run:
            out_path.write_text(page, encoding="utf-8")
        built.append(f"{out_path.parent.name}/{out_path.name}")

    css_src = ROOT / "styles.css"
    css_dst = SITE / "styles.css"
    if css_src.exists():
        if not dry_run:
            shutil.copy(css_src, css_dst)
        built.append(f"{css_dst.parent.name}/{css_dst.name}")
    return built


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="don't write files; just report")
    args = ap.parse_args(argv)
    built = build(dry_run=args.dry_run)
    verb = "would build" if args.dry_run else "built"
    print(f"{verb} {len(built)} files:")
    for b in built:
        print(f"  {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
