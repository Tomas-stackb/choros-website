#!/usr/bin/env python3
"""scripts/ci/serve.py — tiny static server that behaves like Netlify/Cloudflare Pages for testing:
 - applies rules from the site's own _headers file (glob '*' semantics)
 - gzip for text types when the client accepts it
 - directory index + 301 /dir -> /dir/ ; serves 404.html with a real 404 status
 - optional extra header(s) via --header 'Name: value' (e.g. a candidate CSP)
Usage: prodlike_server.py ROOT PORT [--header 'K: V']..."""
import sys, os, re, gzip, mimetypes, fnmatch, http.server, socketserver
root = os.path.abspath(sys.argv[1]); port = int(sys.argv[2])
extra = [a.split(': ', 1) for a in sys.argv[3:] if ': ' in a and not a.startswith('--')]
extra += [sys.argv[i+1].split(': ', 1) for i, a in enumerate(sys.argv) if a == '--header']
rules = []
hp = os.path.join(root, '_headers')
if os.path.exists(hp):
    cur = None
    for line in open(hp, encoding='utf-8'):
        if not line.strip() or line.lstrip().startswith('#'): continue
        if not line.startswith((' ', '\t')): cur = (line.strip(), []); rules.append(cur)
        elif cur and ':' in line: k, v = line.strip().split(':', 1); cur[1].append((k.strip(), v.strip()))
def match(pat, path): return fnmatch.fnmatchcase(path, pat.replace('*', '*')) if '*' in pat else path == pat
TEXT = ('text/', 'application/javascript', 'application/xml', 'application/json', 'image/svg+xml')
class H(http.server.BaseHTTPRequestHandler):
    server_version = 'prodlike'
    def log_message(self, *a): pass
    def _send(self, code, body, ctype, path):
        hdrs = {}
        for pat, items in rules:
            if match(pat, path):
                for k, v in items: hdrs[k] = (hdrs[k] + ', ' + v) if (k in hdrs and k.lower() != 'cache-control') else v
        for k, v in extra: hdrs[k] = v
        enc = self.headers.get('Accept-Encoding', '')
        if 'gzip' in enc and ctype.startswith(TEXT) and len(body) > 512:
            body = gzip.compress(body, 6); hdrs['Content-Encoding'] = 'gzip'; hdrs['Vary'] = 'Accept-Encoding'
        self.send_response(code)
        self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
        if 'Cache-Control' not in hdrs and ctype.startswith('text/html'): hdrs['Cache-Control'] = 'public, max-age=0, must-revalidate'
        for k, v in hdrs.items(): self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(body)
    def do_HEAD(self): self.do_GET()
    def do_GET(self):
        path = self.path.split('?', 1)[0].split('#', 1)[0]
        fs = os.path.normpath(os.path.join(root, path.lstrip('/')))
        if not fs.startswith(root): return self._send(403, b'no', 'text/plain', path)
        if os.path.isdir(fs):
            if not path.endswith('/'):
                self.send_response(301); self.send_header('Location', path + '/'); self.send_header('Content-Length', '0'); self.end_headers(); return
            fs = os.path.join(fs, 'index.html')
        if os.path.isfile(fs) and os.path.basename(fs) != '_headers':
            ct = mimetypes.guess_type(fs)[0] or 'application/octet-stream'
            if fs.endswith('.html'): ct = 'text/html; charset=utf-8'
            elif ct.startswith('text/') or ct.endswith(('javascript', 'xml', 'json')): ct += '; charset=utf-8'
            if fs.endswith('.woff2'): ct = 'font/woff2'
            return self._send(200, open(fs, 'rb').read(), ct, path)
        nf = os.path.join(root, '404.html')
        body = open(nf, 'rb').read() if os.path.isfile(nf) else b'Not found'
        return self._send(404, body, 'text/html; charset=utf-8', path)
class S(socketserver.ThreadingMixIn, http.server.HTTPServer): allow_reuse_address = True; daemon_threads = True
S(('127.0.0.1', port), H).serve_forever()
