#!/usr/bin/env bash
# scripts/build-site.sh — ONE script, two explicit modes, so a production build can never inherit preview-only changes.
#   scripts/build-site.sh production            -> _site/ ready for choros.io (indexable, comments stripped, minified, stamped)
#   scripts/build-site.sh preview /choros-website -> _site/ for GitHub Pages sub-path (noindex + Disallow + base path)
# No framework, no bundler config: it is the same rsync + esbuild minify the Pages workflow already does, plus three small steps.
set -euo pipefail

MODE="${1:?usage: build-site.sh production|preview [base-path]}"
BASE="${2:-}"
ESBUILD="${ESBUILD:-npx --yes esbuild@0.25}"
OUT="${OUT:-_site}"

case "$MODE" in production|preview) ;; *) echo "mode must be production|preview" >&2; exit 2;; esac
[ "$MODE" = production ] && [ -n "$BASE" ] && { echo "production must not use a base path" >&2; exit 2; }

rm -rf "$OUT" && mkdir "$OUT"
# Never publish: git/CI files, scripts, README, the OG-card *source* page, editor junk.
rsync -a --exclude '.git' --exclude '.github' --exclude '.gitignore' --exclude 'README.md' \
      --exclude 'scripts' --exclude '_site*' --exclude 'assets/og/og-card.html' --exclude '.DS_Store' \
      --exclude 'lychee.toml' --exclude 'netlify.toml' --exclude 'node_modules' --exclude 'package*.json' --exclude '.claude' --exclude '.agents' --exclude 'skills-lock.json' ./ "$OUT/"

# 1) Strip HTML comments from every page (they currently carry internal notes, TODOs and client names).
python3 - "$OUT" <<'PY'
import pathlib, re, sys
n = 0
for f in pathlib.Path(sys.argv[1]).rglob('*.html'):
    s = f.read_text(encoding='utf-8')
    t = re.sub(r'<!--.*?-->[ \t]*\n?', '', s, flags=re.S)
    if t != s: f.write_text(t, encoding='utf-8'); n += 1
print(f'stripped comments in {n} files')
PY

# 2) Minify (same tool/version family the Pages workflow already uses).
$ESBUILD "$OUT/assets/css/main.css" --minify --allow-overwrite --outfile="$OUT/assets/css/main.css"
$ESBUILD "$OUT/assets/js/main.js"  --minify --allow-overwrite --outfile="$OUT/assets/js/main.js"

# 3) Cache-bust: ?v=<sha256[:10]> on local css/js refs, so _headers can serve them immutable.
python3 scripts/ci/stamp-assets.py "$OUT"

# 4) Mode-specific. Preview-only behaviour lives HERE and nowhere else.
if [ "$MODE" = preview ]; then
  rm -f "$OUT/_headers" "$OUT/_redirects"                      # GitHub Pages ignores them; do not serve them as files
  find "$OUT" -name '*.html' -exec sed -i.bak -E \
    -e "s#(href|src)=\"/([^/\"]|\")#\1=\"${BASE}/\2#g" \
    -e 's#<head>#<head>\n  <meta name="robots" content="noindex, nofollow">#' {} + && find "$OUT" -name '*.bak' -delete
  printf 'User-agent: *\nDisallow: /\n' > "$OUT/robots.txt"
fi
echo "built $OUT in $MODE mode"
