// Renders the 1200x630 social cards in assets/og/ from scripts/og-cards.json using scripts/og-card.html.
// Dev-time only (needs Node and Playwright; nothing here is deployed). From the repo root:
//   node scripts/make-og.cjs            (set NODE_PATH to a node_modules folder that has playwright)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const cards = JSON.parse(fs.readFileSync(path.join(__dirname, 'og-cards.json'), 'utf8'));
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  fs.mkdirSync(path.join(root, 'assets', 'og'), { recursive: true });
  for (const c of cards) {
    const q = new URLSearchParams({ eyebrow: c.eyebrow, title: c.title, left: c.left, right: c.right });
    await page.goto('file://' + path.join(__dirname, 'og-card.html') + '?' + q.toString());
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(root, 'assets', 'og', c.file + '.png') });
    console.log('rendered', c.file);
  }
  await browser.close();
})();
