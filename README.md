# Choros website — redesign concept

Static HTML/CSS/JS, no framework. A concept for the restructured choros.io; **not live on choros.io**. The GitHub Pages preview is `noindex`.

## Structure

`index.html` (home) · `ai-implementation/` · `ai-operations-audit/` · `software-development/` · `marketing/` (+ 3 sector pages) · `solutions/` (shown as "Products"; + `instant-website-builder/`) · `work/` (+ 3 case studies) · `about/` · `wales/` · `contact/` · `insights/` and `privacy/` (both `noindex` until ready) · `404.html`.

Styles `assets/css/main.css` · behaviour `assets/js/main.js` · self-hosted fonts `assets/fonts/` · icons `assets/img/` + `favicon.ico` · social cards `assets/og/` (one per page).

## Working on it

| Task | Command |
|---|---|
| Header, mobile menu, footer or sticky bar changed | edit `scripts/sync-chrome.py`, then `python3 scripts/sync-chrome.py` (`--check` in CI) |
| Pages added or edited | `python3 scripts/build-seo-files.py` (regenerates `sitemap.xml` + `llms.txt`) |
| Social cards (titles live in `scripts/og-cards.json`) | `node scripts/make-og.cjs` (needs Node + Playwright; dev-time only) |
| Build exactly what production would serve | `bash scripts/build-site.sh production` then `python3 scripts/ci/check-site.py _site --mode production` |
| Look at it like Netlify/Cloudflare would serve it | `python3 scripts/ci/serve.py _site 4321` |

`python3 -m http.server` is fine for a quick look, but it is case-insensitive on macOS and shows its own 404 page; trust the production-like server and CI for links and 404 behaviour.

## Deploys: preview vs production (never mix them)

- **Preview** (`.github/workflows/pages.yml`): `scripts/build-site.sh preview <base-path>` adds `noindex`, `Disallow: /` and the sub-path; a guard refuses to run if the Pages site has a custom domain.
- **Production** (Netlify or Cloudflare Pages, not decided): `bash scripts/build-site.sh production` — strips comments, minifies, stamps CSS/JS with a content hash so `_headers` can serve them `immutable`.
- **Quality gate** (`.github/workflows/quality.yml`): production build + `check-site.py` (canonicals, OG, JSON-LD, sitemap, links, leaks), lychee, Lighthouse 13 (perf ≥ 95, a11y/best-practices/SEO = 100) and axe at WCAG 2.2 AA.

## House rules

1. **No HTML comments in pages.** They have carried internal notes before. CI fails on them in source and strips them at build.
2. **Only facts that are on the site.** Figures, client details, prices and credentials come from the owner; anything unverified is marked in the analysis report, not written as true.
3. **`<main>` is hand-written; the chrome is generated.** Never hand-edit the header, footer or sticky bar — change `scripts/sync-chrome.py`.
4. **Ember (orange) means an action, or "what Choros delivered".** Nothing decorative.
5. Keep `main.css` under 40 KB and `main.js` under 6 KB (CI budgets).

## Before go-live

`_headers` (security headers + caching, Netlify/Cloudflare format) is ready. Still open: hosting choice; where the product app lives while the marketing site takes over choros.io; the 301 map for the old URLs; analytics choice; and the owner's confirmations listed in the analysis report.
