import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4178'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch('http://127.0.0.1:4178/');
      if (response.ok) { ready = true; break; }
    } catch {}
    await delay(500);
  }
  if (!ready) throw new Error('Dashboard development server did not start');
  browser = await chromium.launch({ headless: true });
  await mkdir('web/mobile-evidence', { recursive: true });
  for (const width of [375, 390, 768]) {
    const page = await browser.newPage({ viewport: { width, height: 844 }, deviceScaleFactor: 1 });
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:4178/', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /College Football Analytics/i }).waitFor();
    await page.getByLabel('Choose dashboard section').waitFor();
    if (await page.getByText('Waiting for live data').count()) throw new Error('Dashboard failed to load season report');
    const report = await page.evaluate(async () => { const response = await fetch('./season-report.json'); return response.ok ? response.json() : null; });
    if (!report?.rankings?.length || !report?.predictions?.length) throw new Error('Published report missing usable rankings or predictions');
    for (const section of ['rankings', 'predictions', 'conferences', 'cfp', 'schedule', 'matchup']) {
      await page.getByLabel('Choose dashboard section').selectOption(section);
      if (section === 'predictions') await page.getByRole('heading', { name: 'Game Predictions' }).waitFor();
      if (section === 'cfp') await page.getByRole('heading', { name: 'Projected 12-Team CFP Field' }).waitFor();
      if (section === 'schedule') {
        await page.getByRole('heading', { name: 'School Season Schedule' }).waitFor();
        await page.getByLabel('School Schedule').waitFor();
      }
      if (section === 'matchup') {
        await page.getByRole('heading', { name: 'Hypothetical Matchup' }).waitFor();
        await page.getByLabel('First school').waitFor();
        await page.getByLabel('Second school').waitFor();
      }
      if (await page.getByLabel('Choose dashboard section').inputValue() !== section) {
        throw new Error(`Navigation failed for ${section} at ${width}px`);
      }
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
      if (horizontalOverflow) throw new Error(`Page-wide horizontal overflow in ${section} at ${width}px`);
      if (section === 'rankings' || section === 'predictions' || section === 'cfp') {
        await page.screenshot({ path: `web/mobile-evidence/${section}-${width}.png`, fullPage: true });
      }
      if (errors.length) throw new Error(`Browser error in ${section}: ${errors.join('; ')}`);
    }
    console.log(`Mobile navigation smoke passed at ${width}px`);
    await page.close();
    const failedPage = await browser.newPage({ viewport: { width, height: 844 } });
    await failedPage.route('**/season-report.json', route => route.fulfill({ status: 503, body: 'Unavailable' }));
    await failedPage.goto('http://127.0.0.1:4178/');
    await failedPage.getByText('Waiting for live data').waitFor();
    await failedPage.close();
  }
} finally {
  await browser?.close();
  // npm launches Vite as a child; terminate the entire process group so
  // inherited handles cannot keep the GitHub Actions job alive.
  if (server.pid) {
    try { process.kill(-server.pid, 'SIGTERM'); } catch (error) {
      if (error.code !== 'ESRCH') throw error;
    }
  }
}
