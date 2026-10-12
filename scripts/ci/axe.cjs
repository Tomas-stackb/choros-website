#!/usr/bin/env node
/* scripts/ci/axe.cjs — Playwright + axe-core, WCAG 2.2 AA + best-practice, every page in sitemap.xml plus 404, at 390 and 1280.
   usage: node scripts/ci/axe.cjs http://localhost:4321   (needs playwright + @axe-core/playwright installed)  */
const { chromium } = require('playwright'); const { AxeBuilder } = require('@axe-core/playwright');
const base = (process.argv[2] || 'http://localhost:4321').replace(/\/$/, '');
(async () => {
  const sm = await (await fetch(base + '/sitemap.xml')).text();
  const paths = [...sm.matchAll(/<loc>https?:\/\/[^/]+(\/[^<]*)<\/loc>/g)].map(m => m[1]).concat('/404.html');
  const b = await chromium.launch(); let bad = 0;
  for (const w of [390, 1280]) {
    const ctx = await b.newContext({ viewport: { width: w, height: 800 }, reducedMotion: 'reduce' }), pg = await ctx.newPage();
    for (const p of paths) {
      await pg.goto(base + p); await pg.waitForTimeout(200);
      const r = await new AxeBuilder({ page: pg }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']).analyze();
      for (const v of r.violations) { bad++; console.log(`[${w}] ${p} :: ${v.id} (${v.impact}) x${v.nodes.length} ${v.nodes[0].target.join(' ')}`); }
    }
    await ctx.close();
  }
  await b.close(); console.log(`axe: ${paths.length} pages x 2 widths -> ${bad} violations`); process.exit(bad ? 1 : 0);
})();
