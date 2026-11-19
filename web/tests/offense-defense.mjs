// Browser acceptance: V8 Offense & Defense destination at five widths (real published data).
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection, openDestination, chooseSchool } from './section-navigation.mjs';

const PORT = 4199, base = `http://127.0.0.1:${PORT}/`;
const evidence = 'docs/evidence/v8-offense-defense';
await mkdir(evidence, { recursive: true });
const stats = JSON.parse(await readFile('web/public/v8-team-stats.json', 'utf8'));
const TEAM = 'Texas Tech', OPP = 'Baylor';
const nonPower = Object.entries(stats.teams).find(([, t]) => !t.power)[0];
const ttEpa = stats.teams[TEAM].offense.epa;

async function contrastProblems(page, selector) {
  return page.locator(selector).evaluate(root => {
    const rgb = c => (c.match(/[\d.]+/g) || []).map(Number);
    const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const bg = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length === 3 || (c.length === 4 && c[3] > 0.9)) return c.slice(0, 3); } return [11, 22, 38]; };
    return [...root.querySelectorAll('h2,h3,p,th,td,small,strong,label,legend,button,li,span,caption,summary')]
      .filter(e => e.childNodes.length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getClientRects().length)
      .map(e => { const a = lum(rgb(getComputedStyle(e).color).slice(0, 3)), b = lum(bg(e)); return { text: e.textContent.trim().slice(0, 40), ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) }; })
      .filter(x => x.ratio < 4.5);
  });
}

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  for (const width of [375, 390, 430, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: width === 390 || width === 1536 ? 2 : 1 });
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(base, { waitUntil: 'networkidle' });
    // Reached as a Teams section (one destination, no duplicate navigation).
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Offense & Defense');
    const od = page.locator('.offense-defense');
    await od.getByRole('heading', { name: 'Offense & Defense', level: 2 }).waitFor();
    assert.ok(page.url().endsWith('#/stats'));
    await chooseSchool(page, 'Choose team', TEAM);
    const offense = od.locator('table', { has: page.locator('caption', { hasText: 'Offense · Opponent-adjusted' }) });
    await offense.waitFor();
    const epaRow = offense.locator('tr', { has: page.getByRole('rowheader', { name: /^Expected points added per play/ }) });
    const epaText = (await epaRow.innerText()).replace(/\s+/g, ' ');
    assert.ok(epaText.includes(ttEpa[5].toFixed(2)) && epaText.includes(`#${ttEpa[7]} of ${stats.fbs_teams}`), epaText);
    // Keyboard switch to Traditional, then Power Four only (arrow keys move within the radio group).
    await od.getByRole('radio', { name: 'Opponent-adjusted' }).focus();
    await page.keyboard.press('ArrowLeft');
    assert.ok(await od.getByRole('radio', { name: 'Power Four only' }).isChecked());
    const p4Text = (await od.locator('table', { has: page.locator('caption', { hasText: 'Offense · Power Four only' }) }).locator('tr', { hasText: 'Expected points added per play' }).innerText()).replace(/\s+/g, ' ');
    assert.ok(p4Text.includes(`#${ttEpa[3]} of ${stats.power_teams}`) && p4Text.includes(`${ttEpa[4]} games`), p4Text);
    await od.getByRole('radio', { name: 'Traditional' }).check();
    const rawText = (await od.locator('table', { has: page.locator('caption', { hasText: 'Offense · Traditional' }) }).locator('tr', { hasText: 'Expected points added per play' }).innerText()).replace(/\s+/g, ' ');
    assert.ok(rawText.includes(`#${ttEpa[1]} of ${stats.fbs_teams}`), rawText);
    // Recent form and consistency are present with uncertainty-gated labels.
    await od.getByRole('heading', { name: 'Recent form and consistency' }).waitFor();
    // Matchup panel against an opponent.
    await chooseSchool(page, 'Choose opponent', OPP);
    await od.getByRole('heading', { name: `How ${TEAM} and ${OPP} match up` }).waitFor();
    assert.equal(await od.locator('caption', { hasText: `${TEAM} offense vs ${OPP} defense` }).count(), 1);
    if (width === 390 || width === 1536) {
      await od.screenshot({ path: `${evidence}/offense-defense-${width}.png` });
    }
    // Non-power team: Power Four view explains why it does not apply.
    await chooseSchool(page, 'Choose team', nonPower);
    await od.getByRole('radio', { name: 'Power Four only' }).check();
    await od.getByText('is not in a power conference', { exact: false }).waitFor();
    // Leaderboard ranks match the data and selecting a row changes the team.
    await od.getByRole('radio', { name: 'Opponent-adjusted' }).check();
    const first = Object.entries(stats.teams).find(([, t]) => t.offense.epa[7] === 1)[0];
    const board = od.locator('table', { has: page.locator('caption', { hasText: 'Offense: Expected points added per play · Opponent-adjusted' }) });
    assert.equal((await board.locator('tbody tr').first().innerText()).split(/\s+/)[0], '1');
    await board.getByRole('button', { name: first, exact: true }).click();
    assert.equal(await page.getByLabel('Choose team', { exact: true }).inputValue(), first);
    // Layout and accessibility.
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `horizontal overflow ${overflow}px at ${width}`);
    assert.deepEqual(await contrastProblems(page, '.offense-defense'), [], `contrast at ${width}`);
    // Contextual entry points: Team Profile, Rankings, Compare.
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Team Profiles');
    await chooseSchool(page, 'Choose school', TEAM);
    await page.getByRole('button', { name: 'Offense & Defense', exact: true }).click();
    assert.equal(await page.getByLabel('Choose team', { exact: true }).inputValue(), TEAM);
    await openDestination(page, 'Rankings');
    await page.getByRole('button', { name: 'Offense and defense rankings' }).click();
    await od.getByRole('heading', { name: 'Leaders' }).waitFor();
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Compare & What If');
    await chooseSchool(page, 'First school', TEAM);
    await chooseSchool(page, 'Second school', OPP);
    await page.getByRole('button', { name: 'See how these offenses and defenses match up' }).click();
    await od.getByRole('heading', { name: `How ${TEAM} and ${OPP} match up` }).waitFor();
    assert.deepEqual(errors, [], `page errors at ${width}`);
    await page.close();
    console.log(`Offense & Defense passed at ${width}px`);
  }
  // Missing data file: graceful message, no crash.
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.route('**/v8-team-stats.json', route => route.fulfill({ status: 404, body: 'missing' }));
  await page.goto(base + '#/stats', { waitUntil: 'networkidle' });
  await page.getByText('Offense and defense statistics are not available right now.', { exact: false }).waitFor();
  await page.close();
  console.log('Offense & Defense acceptance passed');
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}
