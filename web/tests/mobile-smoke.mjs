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
    // Guard the approved four-section mobile homepage against regressions.
    for (const title of ['My Teams', 'Featured Games', 'Upset Watch', 'Games That Matter']) {
      await page.getByRole('heading', { name: title, exact: true }).waitFor();
    }
    if (await page.getByRole('heading', { name: 'Competitive Games', exact: true }).count()) throw new Error('Redundant Competitive Games section returned');
    if (await page.getByText('Prediction model:', { exact: false }).count()) throw new Error('Redundant model notice returned');
    await page.getByText('Our Model Rankings', { exact: false }).first().waitFor();
    await page.screenshot({ path: `web/mobile-evidence/home-${width}.png`, fullPage: true });
    // Exercise favorites persistence without changing the user's actual browser storage.
    await page.evaluate(() => localStorage.removeItem('cfba-favorites-v1'));
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByText('+ Add Team', { exact: true }).first().click();
    const firstTeam = await page.evaluate(async () => {
      const response = await fetch('./season-report.json');
      if (!response.ok || !response.headers.get('content-type')?.includes('json')) throw new Error('Season report JSON not served at ' + response.url);
      return (await response.json()).rankings[0].team;
    });
    await page.getByLabel('Add favorite team').fill(firstTeam);
    await page.getByRole('button', { name: 'Save Team' }).click();
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).waitFor();
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).waitFor();
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).click();
    await page.reload({ waitUntil: 'networkidle' });
    if (await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).count()) throw new Error('Favorite removal did not persist');

    const report = await page.evaluate(async () => { const response = await fetch('./season-report.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; });
    if (!report?.rankings?.length || !report?.predictions?.length) throw new Error('Published report missing usable rankings or predictions');
    for (const section of ['rankings', 'predictions', 'conferences', 'cfp', 'schedule', 'matchup', 'programs', 'hype', 'trajectory', 'profile']) {
      await page.getByLabel('Choose dashboard section').selectOption(section);
      if (section === 'predictions') await page.getByRole('heading', { name: 'Game Predictions' }).waitFor();
      const v4Headings = { programs: 'Historical Program Rankings', hype: 'Historical Hype Index', trajectory: 'Program Trajectory & Momentum', profile: 'Team Profile' };
      if (v4Headings[section]) await page.getByRole('heading', { name: v4Headings[section], exact: true }).waitFor();
      if (section === 'profile') {
        await page.getByLabel('Choose school').selectOption(firstTeam);
        await page.getByText('Contenders & Pretenders', { exact: true }).waitFor();
        await page.getByText('Team Stock Watch', { exact: true }).waitFor();
        await page.getByText('Full Season Schedule and Model Outlook').waitFor();
      }
      if (['programs', 'hype', 'trajectory'].includes(section)) {
        // The asset is optional until its historical sources are independently verified.
        // A missing asset must show an honest unavailable state, not crash the page.
        const published = page.getByText('Descriptive research only', { exact: false });
        const unavailable = page.getByRole('status').filter({ hasText: /historical|research|published|format/i });
        await page.waitForFunction(() => {
          const section = document.querySelector('section.notice');
          return !!section && (/historical program data|historical research format/i.test(section.textContent || '') ||
            /descriptive research only/i.test(section.textContent || ''));
        }, { timeout: 10000 });
        if (await published.count()) {
          const link = page.getByRole('button', { name: firstTeam, exact: true }).first();
          if (await link.count()) {
            await link.click();
            await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
            await page.getByLabel('Choose dashboard section').selectOption(section);
          }
        }
      }
      if (section === 'cfp') {
        await page.getByRole('heading', { name: 'Projected 12-Team CFP Field' }).waitFor();
        await page.getByRole('heading', { name: 'Our Top 25 vs. Official CFP Top 25' }).waitFor();
        await page.getByRole('heading', { name: 'Playoff Bubble' }).waitFor();
        const poll = await page.evaluate(async () => { try { const response = await fetch('./poll-snapshot.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; } catch { return null; } });
        if (!poll?.cfp_published_at || !poll?.cfp_top25?.length) {
          await page.getByText('A verified, publication-dated official CFP Top 25 is not available', { exact: false }).waitFor();
        }
      }
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
