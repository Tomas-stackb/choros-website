#!/usr/bin/env python3
"""Cache-busting without a build tool.
Appends ?v=<first 10 hex of sha256(file)> to local CSS/JS references in every HTML file of a built
site directory, so those files can safely be served with `Cache-Control: ... immutable`.

  python3 scripts/ci/stamp-assets.py _site            # stamp in place (run AFTER minification)
  python3 scripts/ci/stamp-assets.py _site --check    # fail if any local css/js ref is unstamped or stale

Run it on the deployable folder, not on the source tree, so source HTML stays clean."""
import hashlib, pathlib, re, sys
root = pathlib.Path(sys.argv[1]).resolve()
check = '--check' in sys.argv
ref = re.compile(r'''((?:href|src)=")(/assets/(?:css|js)/[^"?#]+\.(?:css|js))(\?v=[0-9a-f]+)?(")''')
digest = {}
def h(rel):
    if rel not in digest:
        digest[rel] = hashlib.sha256((root / rel.lstrip('/')).read_bytes()).hexdigest()[:10]
    return digest[rel]
bad, changed, total = [], 0, 0
for f in sorted(root.rglob('*.html')):
    s = f.read_text(encoding='utf-8')
    def sub(m):
        global total
        total += 1
        want = f'?v={h(m.group(2))}'
        if check and m.group(3) != want: bad.append(f'{f.relative_to(root)}: {m.group(2)}{m.group(3) or ""} (want {want})')
        return f'{m.group(1)}{m.group(2)}{want}{m.group(4)}'
    n = ref.sub(sub, s)
    if n != s and not check: f.write_text(n, encoding='utf-8'); changed += 1
if check:
    print(f'{total} asset refs checked, {len(bad)} unstamped/stale')
    for b in bad: print('  ', b)
    sys.exit(1 if bad else 0)
print(f'stamped {total} refs in {changed} files; hashes: ' + ', '.join(f'{k.split("/")[-1]}={v}' for k, v in digest.items()))
