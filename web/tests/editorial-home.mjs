import { chooseSection, assertSection, assertNavigationFits } from './section-navigation.mjs';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright';
import { setTimeout as delay } from 'node:timers/promises';

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4179', '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
const url = 'http://127.0.0.1:4179/';
let browser;
let activePage;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(url)).ok) break; } catch {} await delay(500); }
  browser = await chromium.launch({ headless: true });
  await mkdir('web/editorial-evidence', { recursive: true });
  const results = [];
  for (const width of [375,390,430,768,1536]) {
    const context = await browser.newContext({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: 1 });
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
    assert.equal(await page.locator('.editorial-game:visible').count(), width < 768 ? 2 : 3);
    assert.equal(await page.locator('.editorial-team-row').count(), 3);
    assert.equal(await page.locator('.editorial-rankings li').count(), 5);
    const data = await page.evaluate(async () => ({ season: await (await fetch('./season-report.json')).json(), cards: await (await fetch('./v5-program-report-cards.json')).json() }));
    const tech = data.cards.programs.find(row => row.team === 'Texas Tech');
    const spotlight = await page.locator('.editorial-spotlight').innerText();
    for (const window of ['3','10']) assert.ok(spotlight.includes((100*tech.trajectory.windows[window]).toFixed(1)+'%'));
    const dimensions = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight, homeHeight: document.querySelector('.editorial-home').getBoundingClientRect().height }));
    assert.ok(dimensions.scrollWidth <= width+1, JSON.stringify(dimensions));
    if (width < 768) {
      const position = await nav.evaluate(element => ({ position: getComputedStyle(element).position, bottom: element.getBoundingClientRect().bottom }));
      assert.equal(position.position, 'fixed'); assert.ok(Math.abs(position.bottom-dimensions.height)<=1);
      assert.ok(dimensions.scrollHeight <= 2*844, 'Homepage exceeds two phone screens: '+JSON.stringify(dimensions));
    }
    await page.evaluate(() => window.scrollTo(0,0));
    await page.mouse.move(0,0);
    await page.screenshot({ path: `web/editorial-evidence/home-${width}.png`, fullPage: false });
    await page.screenshot({ path: `web/editorial-evidence/home-${width}-full.png`, fullPage: true });
    if (width < 768) {
      await page.evaluate(() => window.scrollTo(0,document.documentElement.scrollHeight));
      await page.screenshot({ path: `web/editorial-evidence/home-bottom-${width}.png` });
      await page.evaluate(() => window.scrollTo(0,0));
    }
    // Keyboard operation of primary destinations and scrollable secondary tabs.
    const rankingsButton = nav.getByRole('button', { name: 'Rankings', exact: true });
    await rankingsButton.focus(); await page.keyboard.press('Enter');
    await assertSection(page, 'Rankings sections', 'Model Rankings');
    await nav.getByRole('button', { name: 'Teams', exact: true }).click();
    for (const label of ['Overview','Schedule & Predictions','Historical Intelligence','Program Report Card']) {
      await chooseSection(page, 'Team Profile sections', label);
      await assertNavigationFits(page, 'Team Profile sections', width);
      await page.screenshot({ path: `web/editorial-evidence/profile-${label.split(' ')[0].toLowerCase()}-${width}.png`, fullPage: true });
    }
    for (const destination of ['Rankings','Teams','Playoffs','Research']) {
      await nav.getByRole('button', { name: destination, exact: true }).click();
      const group = `${destination} sections`;
      const dropdown = await assertNavigationFits(page, group, width);
      if (width === 1536) assert.equal(dropdown, false, 'Desktop tabs should fit');
      const lastLabel = dropdown ? await page.getByRole('combobox', { name: group, exact: true }).locator('option').last().textContent()
        : await page.getByRole('tablist', { name: group, exact: true }).getByRole('tab').last().textContent();
      await chooseSection(page, group, lastLabel);
      await page.evaluate(() => window.scrollTo(0,0));
      await page.screenshot({ path: `web/editorial-evidence/secondary-${destination.toLowerCase()}-${width}.png` });
    }
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    // Links open the existing, actual detailed application views.
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
    await assertSection(page, 'Team Profile sections', 'Historical Intelligence');
    if (width === 390) {
      await page.setViewportSize({ width: 1536, height: 900 });
      await page.getByRole('tablist', { name: 'Team Profile sections', exact: true }).waitFor();
      await assertSection(page, 'Team Profile sections', 'Historical Intelligence');
      await page.setViewportSize({ width: 390, height: 844 });
      await page.getByRole('combobox', { name: 'Team Profile sections', exact: true }).waitFor();
      await assertSection(page, 'Team Profile sections', 'Historical Intelligence');
    }
    assert.equal(await page.getByLabel('Choose school').inputValue(), 'Texas Tech');
    if (width === 1536) {
      // Constrained desktop containers must also use a picker, regardless of viewport.
      const constrained = await page.addStyleTag({ content: '.team-profile{max-width:420px}' });
      await page.getByRole('combobox', { name: 'Team Profile sections', exact: true }).waitFor();
      await assertSection(page, 'Team Profile sections', 'Historical Intelligence');
      await assertNavigationFits(page, 'Team Profile sections', width);
      await page.screenshot({ path: 'web/editorial-evidence/secondary-narrow-container-1536.png' });
      await constrained.evaluate(element => element.remove());
      await page.getByRole('tablist', { name: 'Team Profile sections', exact: true }).waitFor();
      await assertSection(page, 'Team Profile sections', 'Historical Intelligence');
    }
    await nav.getByRole('button', { name: 'Home', exact: true }).click();
    await page.locator('summary[aria-label="App menu"]').click();
    const about = page.getByLabel('About, privacy and getting started');
    await about.locator('summary').click();
    await about.getByText('Favorites are stored only in this browser', { exact: false }).waitFor();
    assert.deepEqual(errors, []);
    results.push({ width, dimensions, featured: matchupText, spotlight, favoriteTeams: ['Texas Tech','Texas A&M','Georgia'], detailedLinks: 'passed', browserErrors: errors });
    console.log(`Editorial homepage acceptance passed at ${width}px: ${dimensions.scrollHeight}px document`);
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
