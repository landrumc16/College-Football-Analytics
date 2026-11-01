import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const server = spawn('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '4178'], { cwd: 'web', stdio: 'pipe' });
let browser;
try {
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch('http://127.0.0.1:4178/College-Football-Analytics/');
      if (response.ok) { ready = true; break; }
    } catch {}
    await delay(500);
  }
  if (!ready) throw new Error('Dashboard development server did not start');
  browser = await chromium.launch({ headless: true });
  for (const width of [375, 390, 768]) {
    const page = await browser.newPage({ viewport: { width, height: 844 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:4178/College-Football-Analytics/', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /College Football Analytics/i }).waitFor();
    await page.getByLabel('Choose dashboard section').waitFor();
    for (const section of ['rankings', 'predictions', 'conferences', 'cfp', 'schedule', 'matchup']) {
      await page.getByLabel('Choose dashboard section').selectOption(section);
      if (await page.getByLabel('Choose dashboard section').inputValue() !== section) {
        throw new Error(`Navigation failed for ${section} at ${width}px`);
      }
      if (errors.length) throw new Error(`Browser error in ${section}: ${errors.join('; ')}`);
    }
    console.log(`Mobile navigation smoke passed at ${width}px`);
    await page.close();
  }
} finally {
  await browser?.close();
  server.kill('SIGTERM');
}
