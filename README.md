# Car Repair, in Plain English

**For drivers who dread the service desk.**

Decode estimate line items, ask confident questions, understand OBD-II codes, and use free AI to translate a quote into plain English before deciding **repair now** versus **wait**. Markdown docs under `docs/` plus a static HTML site under `site/`.

> Education, never diagnosis. This guide explains vocabulary, questions, and decision frameworks — it never tells you what is broken on *your specific car*. Only a qualified mechanic inspecting your actual vehicle can do that.

## What's inside

| Doc | What it covers |
| --- | --- |
| [Decode the Estimate](docs/estimates.md) | Every line item on a repair estimate: diagnostics fees, flat-rate labor, core charges, shop supplies |
| [Understand OBD-II Codes](docs/obd-codes.md) | How to read P/B/C/U codes, famous codes, and the "a code names a neighborhood, not a culprit" trap |
| [Confident Questions](docs/questions.md) | Copy-paste question templates for before/after approval, second opinions, and hard moments |
| [AI Quote Translator](docs/ai-translator.md) | Free prompts to turn a quote into plain English, plus a repair-now vs. wait framework |
| [Maintenance Primer](docs/maintenance-primer.md) | The small amount of car knowledge that prevents big bills |
| [About & Disclaimer](docs/about.md) | Printable second-opinion script, honest disclaimers, credits |

## Run the static site

```bash
make serve          # builds, then serves site/ at http://localhost:8000
```

Or directly:

```bash
python3 tools/build.py   # regenerate site/*.html from docs/*.md
python3 -m http.server 8000 --directory site
```

Or just open `site/index.html` in any browser — no server needed. The whole site is static HTML + one CSS file: **no tracking, no cookies, no analytics, no ads, no affiliate links, no external requests.** It works fully offline.

## Build & test

```bash
make check          # build + run the test suite
python3 -m unittest discover -s tests -v   # tests directly
```

The 10 tests verify: every doc exists with the right heading, the build emits all pages, markdown conversion (headers/links/tables/code fences), every internal link resolves, no leftover `.md` hrefs, no scripts/iframes/CDN/ads/tracking patterns, pages are well-formed, and disclaimer + credit appear on every page.

## Project layout

```
docs/            Markdown source for the guide
site/            Generated static HTML (safe to regenerate/delete)
tools/build.py   Python build script (docs/*.md -> site/*.html)
tests/           Test suite (stdlib unittest)
styles.css       Stylesheet copied into site/ at build time
LICENSE          MIT License
```

- **Requirements:** Python 3.9+ and the `markdown` package (`pip install markdown`). If `markdown` is missing, a minimal stdlib-only fallback converter handles the features used.
- No secrets, API keys, or personal data anywhere in this repo.

## Credits & license

Created by **[Asdale Dynamics, LLC](https://dylanasdale.github.io)** — Dylan Asdale, a registered nurse turned AI author who explains things *like a friend would*: plain English, step by step, never condescending.

Part of the Asdale Dynamics beginner-guides family, alongside `car-buying-calm-guide` (car *buying*) and `free-car-care-pack` (maintenance printables). This one covers the **repair-desk** moment.

Licensed under the [MIT License](LICENSE). Use it, print it, adapt it — the copyright notice stays.

Copyright (c) 2026 Asdale Dynamics, LLC
