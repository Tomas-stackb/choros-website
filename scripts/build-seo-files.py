#!/usr/bin/env python3
"""Regenerate sitemap.xml and llms.txt from the pages themselves.

Run from the repo root after editing pages:  python3 scripts/build-seo-files.py
- Every page is listed in sitemap.xml unless it carries <meta name="robots" content="noindex…"> (404, insights, privacy draft).
- <lastmod> is the date the page was last committed (today if it has uncommitted changes). No <priority>/<changefreq>: Google ignores them.
- llms.txt links come from each page's own meta description, under a fact line built only from facts that are on the site.
"""
import datetime, html, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://choros.io"
TODAY = datetime.date.today().isoformat()

GROUPS = [  # llms.txt sections: (heading, [(path, link name)])
    ("Services", [("/ai-implementation/", "AI Implementation"), ("/ai-operations-audit/", "The AI Operations Audit"), ("/software-development/", "Software Development"), ("/marketing/", "Marketing")]),
    ("Marketing sectors", [("/marketing/kitchen-bathroom-showrooms/", "Kitchen & Bathroom Showrooms"), ("/marketing/home-services-trades/", "Home Services & Trades"), ("/marketing/restaurants-hospitality/", "Restaurants & Hospitality")]),
    ("Work", [("/work/", "Our work"), ("/work/hedgepoint/", "HedgePoint")]),
    ("Company", [("/about/", "About"), ("/wales/", "Choros in Wales"), ("/contact/", "Contact")]),
    ("Optional", [("/solutions/", "Products"), ("/solutions/instant-website-builder/", "Instant Website Builder")]),
]
FACT = ("Choros (CHOROS.IO LIMITED, company no. 16014661) is a software, AI-implementation and marketing company in Carmarthen, Wales, "
        "working with established UK businesses. Fixed scope, fixed price; the client owns the code. "
        "The AI Operations Audit is from £4,950, delivered in two weeks. Contact: team@choros.io, 07494 913569.")


def page_file(path):
    return ROOT / ("index.html" if path == "/" else path.strip("/") + "/index.html")


def discover():
    paths = []
    for f in sorted(ROOT.rglob("index.html")):
        rel = f.relative_to(ROOT)
        if rel.parts[0] in {"assets", "scripts", "node_modules", "_site", "_site-preview"} or rel.parts[0].startswith("."):
            continue
        text = f.read_text(encoding="utf-8")
        if re.search(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', text, re.I):
            continue
        paths.append("/" if rel.as_posix() == "index.html" else "/" + rel.parent.as_posix() + "/")
    return paths


def lastmod(f):
    rel = str(f.relative_to(ROOT))
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode != 0:
        return TODAY
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or TODAY


def description(f):
    m = re.search(r'<meta name="description" content="([^"]*)"', f.read_text(encoding="utf-8"))
    return html.unescape(m.group(1)) if m else ""


paths = discover()
urls = "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{lastmod(page_file(p))}</lastmod></url>\n" for p in paths)
(ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")

lines = ["# Choros", "", f"> {FACT}", ""]
listed = set()
for title, items in GROUPS:
    lines.append(f"## {title}")
    for p, name in items:
        assert p in paths, f"llms.txt lists {p} but it is not an indexable page"
        listed.add(p)
        lines.append(f"- [{name}]({SITE}{p}): {description(page_file(p))}")
    lines.append("")
missing = [p for p in paths if p not in listed and p != "/"]
assert not missing, f"indexable pages missing from llms.txt groups: {missing}"
(ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"sitemap.xml: {len(paths)} urls · llms.txt: {len(lines)} lines")
