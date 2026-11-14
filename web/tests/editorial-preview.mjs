import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { setTimeout as delay } from 'node:timers/promises';

const server = spawn('npm', ['run', 'preview', '--', '--config', 'vite.editorial.config.ts', '--host', '127.0.0.1', '--port', '4179', '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
const url = 'http://127.0.0.1:4179/editorial-preview.html';
let browser;
let activePage;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(url)).ok) break; } catch {} await delay(500); }
  browser = await chromium.launch({ headless: true });
  await mkdir('web/editorial-evidence', { recursive: true });
  const results = [];
  for (const width of [390,1536]) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    activePage = page;
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Featured Matchups', exact: true }).waitFor();
    const editor = page.locator('.editorial-favorite-editor');
    await editor.locator(':scope > summary').click();
    for (const team of ['Texas Tech','Texas A&M','Georgia']) {
      const add = editor.locator('.favorite-add');
      if (!(await add.evaluate(element => element.open))) await add.locator('summary').click();
      await editor.getByLabel('Add favorite team').fill(team);
      await editor.getByRole('button', { name: 'Save Team', exact: true }).click();
      await editor.getByRole('button', { name: `Remove ${team} from favorites`, exact: true }).waitFor();
    }
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByText('Texas Tech is trending up.', { exact: true }).waitFor();
    for (const name of ['Featured Matchups','My Teams','Rankings Snapshot','Playoff Watch','Program Spotlight']) await page.getByRole('heading', { name, exact: true }).waitFor();
    const nav = page.getByRole('navigation', { name: 'Main navigation', exact: true });
    assert.deepEqual(await nav.getByRole('button').allTextContents(), ['Home','Rankings','Teams','Playoffs','Research']);
    assert.equal(await page.getByRole('tab', { name: 'This Week', exact: true }).count(), 0);
    assert.equal(await page.getByRole('tab', { name: 'Game Predictions', exact: true }).count(), 0);
    assert.equal(await page.locator('.editorial-game:visible').count(), width === 390 ? 2 : 3);
    assert.equal(await page.locator('.editorial-team-row').count(), 3);
    assert.equal(await page.locator('.editorial-rankings li').count(), 5);
    const data = await page.evaluate(async () => ({ season: await (await fetch('./season-report.json')).json(), cards: await (await fetch('./v5-program-report-cards.json')).json() }));
    const tech = data.cards.programs.find(row => row.team === 'Texas Tech');
    const spotlight = await page.locator('.editorial-spotlight').innerText();
    for (const window of ['3','10']) assert.ok(spotlight.includes((100*tech.trajectory.windows[window]).toFixed(1)+'%'));
    const dimensions = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight, homeHeight: document.querySelector('.editorial-home').getBoundingClientRect().height }));
    assert.ok(dimensions.scrollWidth <= width+1, JSON.stringify(dimensions));
    if (width === 390) {
      const position = await nav.evaluate(element => ({ position: getComputedStyle(element).position, bottom: element.getBoundingClientRect().bottom }));
      assert.equal(position.position, 'fixed'); assert.ok(Math.abs(position.bottom-844)<=1);
      assert.ok(dimensions.scrollHeight <= 2*844, 'Homepage exceeds two phone screens: '+JSON.stringify(dimensions));
    }
    await page.screenshot({ path: `web/editorial-evidence/home-${width}.png`, fullPage: false });
    await page.screenshot({ path: `web/editorial-evidence/home-${width}-full.png`, fullPage: true });
    // Preview links open the existing, actual detailed application views.
    const featured = page.locator('.editorial-game:visible').first();
    const matchupText = await featured.innerText();
    await featured.click();
    await page.getByRole('heading', { name: 'Game Predictions', exact: true }).waitFor();
    assert.ok(await page.locator('.prediction-card').count());
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'Open Texas Tech Team Profile', exact: true }).click();
    await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
    assert.equal(await page.getByLabel('Choose school').inputValue(), 'Texas Tech');
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'Full rankings', exact: false }).click();
    await page.getByRole('heading', { name: 'Model Rankings', exact: true }).waitFor();
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'CFP outlook', exact: false }).click();
    await page.getByRole('heading', { name: 'Projected 12-Team CFP Field', exact: true }).waitFor();
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    await page.locator('.editorial-spotlight button').click();
    await page.getByRole('tab', { name: 'Historical Intelligence', exact: true, selected: true }).waitFor();
    assert.equal(await page.getByLabel('Choose school').inputValue(), 'Texas Tech');
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'App menu', exact: true }).click();
    const about = page.getByLabel('About, privacy and getting started');
    await about.locator('summary').click();
    await about.getByText('Favorites are stored only in this browser', { exact: false }).waitFor();
    assert.deepEqual(errors, []);
    results.push({ width, dimensions, featured: matchupText, spotlight, favoriteTeams: ['Texas Tech','Texas A&M','Georgia'], detailedLinks: 'passed', browserErrors: errors });
    console.log(`Editorial browser preview passed at ${width}px: ${dimensions.scrollHeight}px document`);
    await context.close();
  }
  await writeFile('web/editorial-evidence/preview-checks.json', JSON.stringify(results,null,2));
} catch (error) {
  if (activePage && !activePage.isClosed()) await activePage.screenshot({ path: 'web/editorial-evidence/preview-failure.png', fullPage: true });
  throw error;
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}
