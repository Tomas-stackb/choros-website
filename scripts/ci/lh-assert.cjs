#!/usr/bin/env node
/* scripts/ci/lh-assert.cjs — fail the build when Lighthouse (v13 CLI JSON) regresses.
   usage: node scripts/ci/lh-assert.cjs lh/*.json
   Budgets are deliberately a little looser than today's results (perf 99-100, LCP 1.7-2.0 s mobile) to absorb runner noise. */
const fs = require('fs');
const B = { performance: 0.95, accessibility: 1, 'best-practices': 1, seo: 1,
            lcpMs: 2500, clsMax: 0.05, tbtMs: 200 };
const MUST_PASS = ['agent-accessibility-tree', 'llms-txt'];          // Agentic Browsing audits that apply to a static site
let failed = 0;
for (const f of process.argv.slice(2)) {
  const j = JSON.parse(fs.readFileSync(f, 'utf8')), a = j.audits, out = [];
  for (const c of ['performance', 'accessibility', 'best-practices', 'seo'])
    if ((j.categories[c]?.score ?? 0) < B[c]) out.push(`${c} ${Math.round((j.categories[c]?.score ?? 0) * 100)} < ${B[c] * 100}`);
  const lcp = a['largest-contentful-paint'].numericValue, cls = a['cumulative-layout-shift'].numericValue, tbt = a['total-blocking-time'].numericValue;
  if (lcp > B.lcpMs) out.push(`LCP ${Math.round(lcp)} ms > ${B.lcpMs}`);
  if (cls > B.clsMax) out.push(`CLS ${cls.toFixed(3)} > ${B.clsMax}`);
  if (tbt > B.tbtMs) out.push(`TBT ${Math.round(tbt)} ms > ${B.tbtMs}`);
  for (const id of MUST_PASS) { const x = a[id]; if (x && x.scoreDisplayMode !== 'notApplicable' && x.score !== 1) out.push(`agentic audit ${id} failed`); }
  // never ship with the SEO audits that guard indexing
  for (const id of ['is-crawlable', 'canonical', 'meta-description', 'document-title', 'http-status-code', 'robots-txt', 'link-text', 'hreflang'])
    if (a[id] && a[id].scoreDisplayMode !== 'notApplicable' && a[id].score !== 1) out.push(`seo audit ${id} failed`);
  console.log(`${out.length ? 'FAIL' : 'ok  '} ${j.finalDisplayedUrl}  perf ${Math.round(j.categories.performance.score * 100)}  LCP ${Math.round(lcp)}ms  CLS ${cls.toFixed(3)}  TBT ${Math.round(tbt)}ms${out.length ? '  -> ' + out.join('; ') : ''}`);
  failed += out.length ? 1 : 0;
}
process.exit(failed ? 1 : 0);
