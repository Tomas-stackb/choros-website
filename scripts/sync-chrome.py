#!/usr/bin/env python3
"""Keep the shared page chrome (skip link, header, mobile menu, footer, sticky bar) identical on every page.

The chrome is defined once, here. Everything between <body> and <main> and everything after </main>
is regenerated on each run; the <head> and the <main> content of each page are never touched.

    python3 scripts/sync-chrome.py            # rewrite every page
    python3 scripts/sync-chrome.py --check    # exit 1 if any page is out of date (for CI)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PHONE_TEL, PHONE_TXT = "+447494913569", "07494 913569"
EMAIL = "team@choros.io"
BOOK = "/contact/#book"

# --- navigation -------------------------------------------------------------------------------
NAV = [  # (label, href)
    ("Work", "/work/"),
    ("AI Implementation", "/ai-implementation/"),
    ("Software", "/software-development/"),
    ("Marketing", "/marketing/"),
    ("Products", "/solutions/"),
    ("About", "/about/"),
]
SECTORS = [  # (label, one-line descriptor from the page itself, href)
    ("Kitchen &amp; bathroom showrooms", "Booked design consultations", "/marketing/kitchen-bathroom-showrooms/"),
    ("Home services &amp; trades", "Jobs booked, not clicks counted", "/marketing/home-services-trades/"),
    ("Restaurants &amp; hospitality", "Covers on quiet nights", "/marketing/restaurants-hospitality/"),
]
# Pages that belong to a nav section even though their URL does not start with it
PARENT = {"/ai-operations-audit/": "/ai-implementation/"}

# --- sticky mobile bar: what each page asks for ------------------------------------------------
# (label, href, kind)  kind: primary | ghost
CALL = ("Call", f"tel:{PHONE_TEL}", "ghost")
STICKY = {
    "default": [("Book a call", BOOK, "primary")],
    "/ai-implementation/": [("Book the AI audit", "/contact/?topic=audit#book", "primary")],
    "/ai-operations-audit/": [("Book the AI audit", "/contact/?topic=audit#book", "primary")],
    "/software-development/": [("Book a call", "/contact/?topic=software#book", "primary")],
    "/marketing/": [CALL, ("Book a call", "/contact/?topic=marketing#book", "primary")],
    "/marketing/kitchen-bathroom-showrooms/": [CALL, ("Book a call", "/contact/?topic=marketing#book", "primary")],
    "/marketing/home-services-trades/": [CALL, ("Book a call", "/contact/?topic=marketing#book", "primary")],
    "/marketing/restaurants-hospitality/": [CALL, ("Book a call", "/contact/?topic=marketing#book", "primary")],
    "/contact/": [(f"Call {PHONE_TXT}", f"tel:{PHONE_TEL}", "primary")],
    "/solutions/instant-website-builder/": [("Try the builder", "https://choros.io/login", "primary")],
}

CHEV = '<svg class="chev" width="10" height="6" viewBox="0 0 10 6" fill="none" aria-hidden="true"><path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5"/></svg>'


def route_of(file: pathlib.Path) -> str:
    rel = file.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def current(route: str, href: str) -> str:
    """aria-current: 'page' on the page itself, 'true' on an ancestor section."""
    route = PARENT.get(route, route) if route != href else route
    if route == href:
        return ' aria-current="page"'
    if href != "/" and route.startswith(href):
        return ' aria-current="true"'
    return ""


def header(route: str) -> str:
    links = []
    for label, href in NAV:
        cur = current(route, href)
        if label == "Marketing":
            panel = "".join(
                f'\n            <a href="{h}">{l}<span>{d}</span></a>' for l, d, h in SECTORS
            ) + '\n            <a href="/marketing/">All marketing<span>Ads, follow-up and tracking</span></a>'
            links.append(
                f'''<div class="nav-drop">
          <a href="{href}"{cur}>{label}</a>
          <button type="button" class="nav-drop-toggle" aria-expanded="false" aria-controls="nav-marketing"><span class="sr-only">Marketing sectors</span>{CHEV}</button>
          <div class="nav-drop-panel" id="nav-marketing">{panel}
          </div>
        </div>'''
            )
        else:
            links.append(f'<a href="{href}"{cur}>{label}</a>')
    nav = "\n        ".join(links)
    return f'''<header class="site-header">
    <div class="container">
      <a class="logo" href="/" aria-label="Choros home">Choros<span class="logo-dot" aria-hidden="true"></span></a>
      <nav class="nav-desktop" aria-label="Primary">
        {nav}
      </nav>
      <div class="header-cta">
        <a class="btn btn--primary btn--sm" href="/contact/">Book a call</a>
        <a class="nojs-menu" href="#site-footer">Menu</a>
        <button class="burger" type="button" aria-expanded="false" aria-controls="nav-mobile" aria-label="Open menu"><span></span><span></span><span></span></button>
      </div>
    </div>
  </header>'''


def mobile_nav(route: str) -> str:
    rows = []
    for label, href in NAV:
        rows.append(f'<a class="nm-link" href="{href}"{current(route, href)}>{label}</a>')
        if label == "Marketing":
            for l, _d, h in SECTORS:
                rows.append(f'<a class="nm-sub" href="{h}"{current(route, h)}>{l}</a>')
    body = "\n    ".join(rows)
    return f'''<nav class="nav-mobile" id="nav-mobile" aria-label="Mobile">
    {body}
    <a class="btn btn--primary nm-cta" href="/contact/">Book a call</a>
    <div class="nm-meta">
      <a href="mailto:{EMAIL}">{EMAIL}</a><br>
      <a href="tel:{PHONE_TEL}">{PHONE_TXT}</a>
    </div>
  </nav>'''


FOOTER = f'''<footer class="site-footer" id="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a class="logo" href="/" aria-label="Choros home">Choros<span class="logo-dot" aria-hidden="true"></span></a>
          <p>Bespoke software, AI implementation and marketing for established UK businesses. Based in Carmarthen, working UK-wide.</p>
        </div>
        <div class="footer-col">
          <p class="footer-heading">Services</p>
          <a href="/ai-implementation/">AI Implementation</a>
          <a href="/ai-operations-audit/">The AI Operations Audit</a>
          <a href="/software-development/">Software Development</a>
          <a href="/marketing/">Marketing</a>
          <a href="/wales/">Choros in Wales</a>
        </div>
        <div class="footer-col">
          <p class="footer-heading">Marketing for</p>
          <a href="/marketing/kitchen-bathroom-showrooms/">Kitchen &amp; bathroom showrooms</a>
          <a href="/marketing/home-services-trades/">Home services &amp; trades</a>
          <a href="/marketing/restaurants-hospitality/">Restaurants &amp; hospitality</a>
        </div>
        <div class="footer-col">
          <p class="footer-heading">Work</p>
          <a href="/work/hedgepoint/">HedgePoint</a>
          <a href="/work/">All work</a>
        </div>
        <div class="footer-col">
          <p class="footer-heading">Company</p>
          <a href="/about/">About</a>
          <a href="/solutions/">Products</a>
          <a href="/contact/">Contact</a>
          <a href="mailto:{EMAIL}">{EMAIL}</a>
          <a href="tel:{PHONE_TEL}">{PHONE_TXT}</a>
          <a href="https://www.linkedin.com/company/choros-io" rel="noopener">LinkedIn</a>
        </div>
      </div>
      <div class="footer-legal">
        CHOROS.IO LIMITED &middot; Registered in England and Wales &middot; Company no. <a href="https://find-and-update.company-information.service.gov.uk/company/16014661" rel="noopener">16014661</a> &middot; Registered office: Parc Dewi Sant, Building 1, Job&rsquo;s Well Road, Carmarthen, Wales, SA31 3HB<br>
        &copy; <span data-year>2026</span> Choros.io Limited. All rights reserved. &middot; <a href="/privacy/">Privacy notice</a>
      </div>
    </div>
  </footer>'''


def sticky(route: str) -> str:
    items = STICKY.get(route, STICKY["default"])
    btns = "".join(
        f'<a class="btn btn--{"ghost-dark" if kind == "ghost" else "primary"}" href="{href}">{label}</a>'
        for label, href, kind in items
    )
    return f'<div class="mobile-cta" role="region" aria-label="Quick actions">{btns}</div>'


def chrome_top(route: str) -> str:
    return f'''<body>
  <a class="skip-link" href="#main">Skip to content</a>

  {header(route)}

  {mobile_nav(route)}

  '''


def chrome_bottom(route: str) -> str:
    return f'''</main>

  {FOOTER}

  {sticky(route)}
  <script src="/assets/js/main.js" defer></script>
</body>
</html>
'''


def pages():
    skip = {"assets", "scripts", "node_modules", ".git", ".github", ".claude", ".agents"}
    for f in sorted(ROOT.rglob("*.html")):
        if skip & set(f.relative_to(ROOT).parts):
            continue
        yield f


def render(file: pathlib.Path) -> str:
    html = file.read_text(encoding="utf-8")
    route = route_of(file)
    m_top = re.search(r"<body>.*?(?=<main[ >])", html, re.S)
    m_bot = re.search(r"</main>.*\Z", html, re.S)
    if not (m_top and m_bot):
        raise SystemExit(f"{file}: could not find <body> … <main> … </main>")
    return html[: m_top.start()] + chrome_top(route) + html[m_top.end(): m_bot.start()] + chrome_bottom(route)


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for f in pages():
        new = render(f)
        if new != f.read_text(encoding="utf-8"):
            stale.append(f.relative_to(ROOT).as_posix())
            if not check:
                f.write_text(new, encoding="utf-8")
    if check:
        print("out of date:", ", ".join(stale) if stale else "none")
        return 1 if stale else 0
    print(f"chrome synced: {len(stale)} page(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
