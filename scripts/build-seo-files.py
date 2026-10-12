#!/usr/bin/env python3
"""Regenerate sitemap.xml and llms.txt from the pages themselves.

Run from the repo root after editing pages:  python3 scripts/build-seo-files.py
- <lastmod> is the date the page was last committed (today if it has uncommitted changes).
- llms.txt titles/descriptions come straight from each page's <title>-adjacent meta description.
"""
import datetime, html, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://choros.io'
TODAY = datetime.date.today().isoformat()

GROUPS = [
    ('Services', [('/ai-implementation/', 'AI Implementation'), ('/software-development/', 'Software Development'), ('/marketing/', 'Marketing')]),
    ('Marketing sectors', [('/marketing/home-services-trades/', 'Home Services & Trades'), ('/marketing/kitchen-bathroom-showrooms/', 'Kitchen & Bathroom Showrooms'), ('/marketing/restaurants-hospitality/', 'Restaurants & Hospitality')]),
    ('Work', [('/work/', 'Work'), ('/work/hedgepoint/', 'HedgePoint'), ('/work/curveball/', 'Curveball'), ('/work/altitude-28/', 'Altitude 28')]),
    ('Products', [('/solutions/', 'Solutions'), ('/solutions/instant-website-builder/', 'Instant Website Builder')]),
    ('Company', [('/about/', 'About'), ('/insights/', 'Insights'), ('/contact/', 'Contact')]),
]

def page_file(path):
    return ROOT / ('index.html' if path == '/' else path.strip('/') + '/index.html')

def lastmod(f):
    rel = str(f.relative_to(ROOT))
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', rel], cwd=ROOT).returncode != 0:
        return TODAY
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or TODAY

def description(f):
    m = re.search(r'<meta name="description" content="([^"]*)"', f.read_text(encoding='utf-8'))
    return html.unescape(m.group(1)) if m else ''

paths = ['/'] + [p for _, items in GROUPS for p, _ in items]
urls = ''.join(f'  <url><loc>{SITE}{p}</loc><lastmod>{lastmod(page_file(p))}</lastmod></url>\n' for p in paths)
(ROOT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding='utf-8')

lines = ['# Choros', '', f'> {description(page_file("/"))}', '']
for title, items in GROUPS:
    lines.append(f'## {title}')
    lines += [f'- [{name}]({SITE}{p}): {description(page_file(p))}' for p, name in items]
    lines.append('')
(ROOT / 'llms.txt').write_text('\n'.join(lines), encoding='utf-8')
print(f'sitemap.xml: {len(paths)} urls · llms.txt: {len(lines)} lines')
