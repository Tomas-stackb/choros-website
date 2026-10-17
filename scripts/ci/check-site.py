#!/usr/bin/env python3
"""scripts/ci/check-site.py — fast, dependency-free regression guard for the built site (_site/).

  python3 scripts/ci/check-site.py _site --mode production
  python3 scripts/ci/check-site.py _site --mode preview

Fails (exit 1) on errors; prints warnings. Covers: preview-vs-production safety, canonical/OG/sitemap consistency,
JSON-LD sanity against Google's documented requirements, internal links + fragments, leaked internal notes,
icon/OG file existence and size, asset stamping. Set PUBLISH_DENYLIST (comma-separated, from a CI *secret*, never
committed) to block names that must not be published, e.g. clients without sign-off."""
import argparse, hashlib, html, json, os, pathlib, re, struct, sys, datetime

ap = argparse.ArgumentParser()
ap.add_argument('root'); ap.add_argument('--mode', choices=['production', 'preview'], required=True)
ap.add_argument('--origin', default='https://choros.io')
ap.add_argument('--safety-only', action='store_true', help='only the preview-vs-production safety checks (for the preview workflow)')
ap.add_argument('--base', default='', help='sub-path prefix used by the preview build, e.g. /choros-website')
a = ap.parse_args()
ROOT = pathlib.Path(a.root).resolve(); ORIGIN = a.origin.rstrip('/'); PROD = a.mode == 'production'; BASE = a.base.rstrip('/')
errors, warns = [], []
def err(m): errors.append(m)
def warn(m): warns.append(m)

pages = {}   # url path -> (file, text)
for f in sorted(ROOT.rglob('*.html')):
    rel = f.relative_to(ROOT).as_posix()
    if rel == '404.html': path = '/404.html'
    elif rel.endswith('index.html'): path = '/' + rel[:-len('index.html')]
    else: path = '/' + rel
    pages[path] = (f, f.read_text(encoding='utf-8'))
NOINDEX_OK = {'/404.html', '/insights/', '/privacy/'}   # held back on purpose: not in the sitemap, must carry noindex
indexable = {p: v for p, v in pages.items() if p not in NOINDEX_OK}
def local_file(url_path):
    p = url_path.split('#')[0].split('?')[0]
    if BASE and p.startswith(BASE + '/'): p = p[len(BASE):]
    c = ROOT / p.lstrip('/')
    if c.is_dir(): c = c / 'index.html'
    return c if c.is_file() else None
def png_size(f):
    b = f.read_bytes()[:32]
    return struct.unpack('>II', b[16:24]) if b[:8] == b'\x89PNG\r\n\x1a\n' else None

# ---- 1. preview vs production safety -------------------------------------------------------
if '/404.html' not in pages: err('404.html missing (Cloudflare Pages would fall back to SPA mode and answer 200 for every unknown URL)')
robots = (ROOT / 'robots.txt').read_text() if (ROOT / 'robots.txt').exists() else ''
for path, (f, s) in pages.items():
    has_noindex = bool(re.search(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', s, re.I))
    if path in NOINDEX_OK:
        if not has_noindex: err(f'{path} must be noindex')
    elif PROD and has_noindex: err(f'{path}: noindex present in PRODUCTION build')
    elif not PROD and not has_noindex: err(f'{path}: preview page is missing noindex')
if PROD:
    if re.search(r'(?im)^\s*Disallow:\s*/\s*$', robots): err('robots.txt blocks everything in PRODUCTION build')
    if f'Sitemap: {ORIGIN}/sitemap.xml' not in robots: err('robots.txt lacks the absolute Sitemap line')
else:
    if not re.search(r'(?im)^\s*Disallow:\s*/\s*$', robots): err('preview robots.txt must Disallow: /')

def finish():
    print(f'checked {len(pages)} html files in {a.mode} mode')
    for w in warns: print('WARN ', w)
    for e in errors: print('ERROR', e)
    print(f'{len(errors)} errors, {len(warns)} warnings')
    sys.exit(1 if errors else 0)
if a.safety_only: finish()

# ---- 2. per-page head checks -----------------------------------------------------------------
def meta(s, attr, name):
    m = re.search(rf'<meta[^>]+{attr}="{re.escape(name)}"[^>]*content="([^"]*)"', s, re.I)
    return html.unescape(m.group(1)) if m else None
for path, (f, s) in indexable.items():
    want = ORIGIN + path
    if not re.search(r'<html[^>]+lang="en-GB"', s): err(f'{path}: <html lang="en-GB"> missing')
    if not re.search(r'<meta name="viewport"', s): err(f'{path}: viewport meta missing')
    if len(re.findall(r'<title>', s)) != 1: err(f'{path}: need exactly one <title>')
    if len(re.findall(r'<h1[\s>]', s)) != 1: err(f'{path}: need exactly one <h1>')
    desc = meta(s, 'name', 'description')
    if not desc: err(f'{path}: meta description missing')
    elif not 70 <= len(desc) <= 165: warn(f'{path}: meta description {len(desc)} chars')
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    if t and len(html.unescape(t.group(1))) > 65: warn(f'{path}: title {len(html.unescape(t.group(1)))} chars (may truncate)')
    c = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    if not c or c.group(1) != want: err(f'{path}: canonical {c and c.group(1)} != {want}')
    if meta(s, 'property', 'og:url') != want: err(f'{path}: og:url != canonical')
    for k in ('og:title', 'og:description', 'og:image', 'og:type', 'og:site_name'):
        if not meta(s, 'property', k): err(f'{path}: {k} missing')
    if meta(s, 'name', 'twitter:card') != 'summary_large_image': warn(f'{path}: twitter:card != summary_large_image')
    img = meta(s, 'property', 'og:image')
    if img:
        if not img.startswith(ORIGIN + '/'): err(f'{path}: og:image not absolute on {ORIGIN}')
        else:
            lf = local_file(img[len(ORIGIN):])
            if not lf: err(f'{path}: og:image file missing in build')
            else:
                dim = png_size(lf)
                if lf.stat().st_size > 300_000: warn(f'{path}: og:image {lf.stat().st_size//1024} KB (WhatsApp may drop >300 KB)')
                w, h = meta(s, 'property', 'og:image:width'), meta(s, 'property', 'og:image:height')
                if not (w and h): warn(f'{path}: og:image:width/height missing (first-share preview can be blank)')
                elif dim and (int(w), int(h)) != dim: err(f'{path}: og:image:width/height {w}x{h} != file {dim[0]}x{dim[1]}')
                if not meta(s, 'property', 'og:image:alt'): warn(f'{path}: og:image:alt missing')
    for rel_ in re.findall(r'<link[^>]+rel="(?:icon|apple-touch-icon)"[^>]*href="([^"]+)"', s):
        if rel_.startswith('/') and not local_file(rel_): err(f'{path}: icon {rel_} missing in build')
    if PROD and path == '/':
        icons = re.findall(r'<link[^>]+rel="(?:icon|shortcut icon|apple-touch-icon)"[^>]*href="([^"]+)"', s)
        if not any(re.search(r'\.(ico|png)(\?|$)', i) for i in icons): err('/: no PNG/ICO icon link (Google Search favicon docs do not list SVG)')
        if not re.search(r'rel="apple-touch-icon"', s): warn('/: apple-touch-icon missing')

# ---- 3. JSON-LD ------------------------------------------------------------------------------
GOOGLE_APP_CATEGORIES = {'GameApplication', 'SocialNetworkingApplication', 'TravelApplication', 'ShoppingApplication', 'SportsApplication', 'LifestyleApplication', 'BusinessApplication', 'DesignApplication', 'DeveloperApplication', 'DriverApplication', 'EducationalApplication', 'HealthApplication', 'FinanceApplication', 'SecurityApplication', 'BrowserApplication', 'CommunicationApplication', 'DesktopEnhancementApplication', 'EntertainmentApplication', 'MultimediaApplication', 'HomeApplication', 'UtilitiesApplication', 'ReferenceApplication'}
def nodes(j):
    if isinstance(j, list):
        for x in j: yield from nodes(x)
    elif isinstance(j, dict):
        if '@graph' in j: yield from nodes(j['@graph'])
        else: yield j
def walk(o, fn):
    if isinstance(o, dict):
        fn(o); [walk(v, fn) for v in o.values()]
    elif isinstance(o, list): [walk(v, fn) for v in o]
for path, (f, s) in indexable.items():
    blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', s, re.S)
    if not blocks: warn(f'{path}: no JSON-LD'); continue
    visible = re.sub(r'<script.*?</script>', '', s, flags=re.S)
    for b in blocks:
        try: j = json.loads(b)
        except Exception as e: err(f'{path}: JSON-LD does not parse ({e})'); continue
        for n in nodes(j):
            ty = n.get('@type'); tys = ty if isinstance(ty, list) else [ty]
            if '@context' not in n and '@graph' not in (j if isinstance(j, dict) else {}) and not (isinstance(j, dict) and '@context' in j): err(f'{path}: JSON-LD block without @context')
            if 'BreadcrumbList' in tys:
                items = n.get('itemListElement', [])
                if len(items) < 2: err(f'{path}: BreadcrumbList needs >=2 items')
                for i, li in enumerate(items):
                    if li.get('position') != i + 1: err(f'{path}: breadcrumb position {li.get("position")} != {i+1}')
                if items and items[-1].get('item') not in (None, ORIGIN + path): err(f'{path}: last breadcrumb item must be this page')
            if any(t in tys for t in ('Article', 'NewsArticle', 'BlogPosting')):
                for k in ('datePublished', 'dateModified'):
                    d = n.get(k)
                    if d and not re.search(rf'<time[^>]+datetime="{re.escape(d[:10])}', visible): err(f'{path}: {k} {d} is not visible on the page (Google: visible and structured dates must match)')
            if any(t in tys for t in ('SoftwareApplication', 'WebApplication', 'MobileApplication')):
                cat = n.get('applicationCategory')
                if cat not in GOOGLE_APP_CATEGORIES: err(f'{path}: applicationCategory {cat!r} is not one of Google\'s supported values')
            if 'Organization' in tys and n.get('logo'):
                lg = n['logo'] if isinstance(n['logo'], str) else n['logo'].get('url') or n['logo'].get('contentUrl')
                lf = local_file(lg[len(ORIGIN):]) if lg and lg.startswith(ORIGIN) else None
                if lg and not lf: err(f'{path}: Organization.logo file missing')
                elif lf:
                    dim = png_size(lf)
                    if dim and (dim[0] < 112 or dim[1] < 112): err(f'{path}: logo {dim} < 112x112')
                    elif dim and abs(dim[0] / dim[1] - 1) > 0.25: warn(f'{path}: Organization.logo is {dim[0]}x{dim[1]} (not square; looks wrong on a white tile)')
        def urls(o):
            for k, v in o.items():
                if k in ('url', '@id', 'item', 'mainEntityOfPage') and isinstance(v, str) and v.startswith('http') and not v.startswith(ORIGIN) and k != 'url': err(f'{path}: JSON-LD {k} {v} not on {ORIGIN}')
        walk(j, urls)

# ---- 4. sitemap + llms.txt ---------------------------------------------------------------------
sm = (ROOT / 'sitemap.xml').read_text() if (ROOT / 'sitemap.xml').exists() else ''
locs = re.findall(r'<loc>([^<]+)</loc>', sm)
if PROD:
    for l in locs:
        if not l.startswith(ORIGIN + '/') or not local_file(l[len(ORIGIN):]): err(f'sitemap: {l} does not resolve to a built page')
    for p in indexable:
        if ORIGIN + p not in locs: err(f'sitemap: indexable page {p} missing')
    lm = re.findall(r'<lastmod>([^<]+)</lastmod>', sm)
    if any(datetime.date.fromisoformat(x[:10]) > datetime.date.today() for x in lm): err('sitemap: lastmod in the future')
    if len(lm) > 3 and len(set(lm)) == 1: warn(f'sitemap: every lastmod is {lm[0]} (Google ignores lastmod that is not consistently accurate)')
if (ROOT / 'llms.txt').exists():
    t = (ROOT / 'llms.txt').read_text()
    if not re.search(r'^#\s+\S', t, re.M) or not re.search(r'\[.+\]\(.+\)', t) or len(t) < 50: err('llms.txt fails the Lighthouse format audit (H1, a link, >=50 chars)')
    for u in re.findall(r'\]\((https?://[^)]+)\)', t):
        if u.startswith(ORIGIN) and not local_file(u[len(ORIGIN):]): err(f'llms.txt: {u} does not resolve')

# ---- 5. internal links + fragments ---------------------------------------------------------------
ids = {p: set(re.findall(r'\sid="([^"]+)"', s)) for p, (f, s) in pages.items()}
for path, (f, s) in pages.items():
    for h in re.findall(r'(?:href|src)="(/[^"]*)"', re.sub(r'<script type="application/ld\+json">.*?</script>', '', s, flags=re.S)):
        base, _, frag = h.partition('#'); base = base.split('?')[0]
        if base == '': continue
        lf = local_file(base)
        if not lf: err(f'{path}: broken internal link {h}'); continue
        if frag:
            tgt = '/' + lf.relative_to(ROOT).as_posix().replace('index.html', '')
            if frag not in ids.get(tgt, set()): err(f'{path}: fragment #{frag} not found on {tgt}')

# ---- 6. leaked notes / denylist / hygiene ----------------------------------------------------------
BAD = re.compile(r'(TODO|FIXME|XXX|lorem ipsum|spec §|\bsign-off\b|must NOT appear|Do NOT name)', re.I)
deny = [x.strip().lower() for x in os.environ.get('PUBLISH_DENYLIST', '').split(',') if x.strip()]
# Names that must not be published (owner's instruction). Stored as SHA-256 of the lower-case token sequence, so this public file
# does not itself name them. Add one with: python3 -c "import hashlib;print(hashlib.sha256(b'client name').hexdigest())"
BLOCKED_SHA256 = {
    '25a2218bfac3b7eb85a298f7a297440836578c93b359b5b3ebd741e4dc062c13',
    'ce9382984d042eb22c1c2da73ef0060f138f40ad368af20557011b24db2ac591',
    '033d688ef0c0a10f85f47cfc6b4f7446cb40aead93a3dfded38c1c0910549063',
}
def blocked_name_in(text):
    toks = re.findall(r'[a-z0-9]+', text.lower())
    seen = set(toks) | {' '.join(p) for p in zip(toks, toks[1:])}
    return any(hashlib.sha256(x.encode()).hexdigest() in BLOCKED_SHA256 for x in seen)
for f in ROOT.rglob('*'):
    if not f.is_file(): continue
    rel = f.relative_to(ROOT).as_posix()
    if rel.endswith(('.map', '.bak', '.DS_Store')) or rel == 'assets/og/og-card.html': err(f'{rel}: must not be published')
    if blocked_name_in(rel): err(f'{rel}: file name contains a blocked name (hashed list in check-site.py)')
    if f.suffix in ('.html', '.txt', '.xml', '.json', '.css', '.js', '.svg', '.webmanifest'):
        t = f.read_text(encoding='utf-8', errors='replace')
        if PROD and f.suffix == '.html' and '<!--' in t: err(f'{rel}: HTML comment present ({len(re.findall("<!--", t))}) - comments carry internal notes')
        if PROD and BAD.search(t): err(f'{rel}: internal-note marker "{BAD.search(t).group(0)}"')
        tl = t.lower()
        if blocked_name_in(t): err(f'{rel}: contains a blocked name (hashed list in check-site.py)')
        for d in deny:
            if d in tl: err(f'{rel}: contains denylisted term (see PUBLISH_DENYLIST secret)')

# ---- 7. asset stamping + budgets -------------------------------------------------------------------
import subprocess
if PROD and (pathlib.Path(__file__).parent / 'stamp-assets.py').exists():
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / 'stamp-assets.py'), str(ROOT), '--check'], capture_output=True, text=True)
    if r.returncode: err('asset stamping: ' + r.stdout.strip().splitlines()[0])
budgets = {'assets/css/main.css': 40_000, 'assets/js/main.js': 6_000}
for rel, mx in budgets.items():
    f = ROOT / rel
    if f.exists() and f.stat().st_size > mx: err(f'{rel}: {f.stat().st_size} bytes > budget {mx}')

finish()
