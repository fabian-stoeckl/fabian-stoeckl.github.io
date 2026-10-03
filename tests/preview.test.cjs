const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const baseURL = process.env.PREVIEW_URL || 'http://127.0.0.1:4000';
const outputDir = process.env.SCREENSHOT_DIR || 'artifacts/screenshots';
const pages = [
  { name: 'homepage', path: '/', ready: 'h1' },
  { name: 'dashboard', path: '/Privat/', ready: '.grid' },
  { name: 'etf-dashboard', path: '/Privat/ETFs/', ready: '.year-key' },
];
const viewports = [
  { name: 'desktop', width: 1440, height: 1000 },
  { name: 'mobile', width: 390, height: 844 },
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const viewport of viewports) {
    for (const target of pages) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/chart.umd.min.js', route => route.fulfill({
        contentType: 'application/javascript',
        body: fs.readFileSync(path.join(__dirname, '..', 'node_modules/chart.js/dist/chart.umd.js')),
      }));
      const response = await page.goto(baseURL + target.path, { waitUntil: 'networkidle' });
      if (!response?.ok()) throw new Error(`${target.path} returned ${response?.status()}`);
      await page.waitForSelector(target.ready);
      if (errors.length) throw new Error(`${target.path}: ${errors.join('; ')}`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow) throw new Error(`${target.path} has horizontal overflow at ${viewport.width}px`);
      await page.screenshot({
        path: path.join(outputDir, `${target.name}-${viewport.name}.png`),
        fullPage: true,
      });
      if (target.name === 'homepage') {
        const layout = () => page.locator('section').evaluate(section => ({
          height: section.getBoundingClientRect().height,
          links: Array.from(section.querySelectorAll('a')).map(link => {
            const range = document.createRange();
            range.selectNodeContents(link);
            return {
              weight: getComputedStyle(link).fontWeight,
              fragments: Array.from(range.getClientRects()).map(rect => [
                rect.x, rect.y + scrollY, rect.width, rect.height,
              ]),
            };
          }),
        }));
        const baseline = JSON.stringify(await layout());
        const links = page.locator('section a');
        for (const link of await links.all()) {
          await link.hover();
          if (JSON.stringify(await layout()) !== baseline) {
            throw new Error(`Link hover changes homepage layout at ${viewport.width}px: ${await link.innerText()}`);
          }
          await link.focus();
          if (JSON.stringify(await layout()) !== baseline) {
            throw new Error(`Link focus changes homepage layout at ${viewport.width}px: ${await link.innerText()}`);
          }
        }
        const ministry = page.getByRole('link', { name: 'Ministry of Finance', exact: true });
        await page.getByRole('heading', { name: 'Welcome!', exact: true }).click();
        await ministry.hover();
        const style = await ministry.evaluate(link => ({
          color: getComputedStyle(link).color,
          background: getComputedStyle(link).backgroundColor,
        }));
        if (style.color !== 'rgb(0, 102, 153)' || style.background === 'rgba(0, 0, 0, 0)') {
          throw new Error(`Link hover highlight is missing at ${viewport.width}px`);
        }
        await page.screenshot({
          path: path.join(outputDir, `homepage-hover-${viewport.name}.png`),
          fullPage: true,
        });
        console.log(`PASS stable link hover/focus at ${viewport.width}px`);
      }
      console.log(`PASS ${target.path} at ${viewport.width}px`);
      await page.close();
    }
  }
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});
