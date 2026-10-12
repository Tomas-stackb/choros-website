# Choros website — redesign concept

Static HTML/CSS/JS concept for the restructured choros.io. Not live on choros.io.

- **Preview:** GitHub Pages (see the repo's About link). Every page is `noindex`; CSS/JS are minified at deploy time.
- **Run locally:** `python3 -m http.server 4321` from this folder, then open http://localhost:4321
- **After editing pages:** `python3 scripts/build-seo-files.py` regenerates `sitemap.xml` and `llms.txt`.

Structure: `index.html` (home), `ai-implementation/`, `software-development/`, `marketing/` (+ 3 sector pages), `solutions/`, `work/` (3 case studies), `about/`, `insights/`, `contact/`. Styles in `assets/css/main.css`, script in `assets/js/main.js`, self-hosted fonts in `assets/fonts/`.

`_headers` holds caching/security headers for Netlify or Cloudflare Pages (GitHub Pages ignores it).
