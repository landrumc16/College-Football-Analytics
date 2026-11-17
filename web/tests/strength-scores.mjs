// Browser acceptance: Team Profile three-score strength breakdown at five widths (descriptive; official outputs unchanged).
import assert from 'node:assert/strict';
import { readFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import vm from 'node:vm';
import ts from 'typescript';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection, openDestination, chooseSchool } from './section-navigation.mjs';

const PORT = 4184, base = `http://127.0.0.1:${PORT}/`, TEAM = 'Texas Tech';
const report = JSON.parse(await readFile('web/public/season-report.json', 'utf8'));
const mod = { exports: {} };
vm.runInNewContext(ts.transpileModule(await readFile('web/src/strengthScores.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: mod.exports, Number, Math, Object });
const ratings = Object.fromEntries(report.rankings.map(t => [t.team, t.rating]));
const expected = mod.exports.rankedStrength(report.rankings, report.schedule)[TEAM];
const evidence = 'docs/evidence/dynamic-strength';
await mkdir(evidence, { recursive: true });
const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  for (const width of [375, 390, 430, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: width === 390 || width === 1536 ? 2 : 1 });
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(base, { waitUntil: 'networkidle' });
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Team Profiles');
    await chooseSchool(page, 'Choose school', TEAM);
    const panel = page.getByRole('region', { name: 'Strength breakdown', exact: true });
    await panel.waitFor();
    // Headline: one badge + plain sentence with FBS ranks; details closed by default (compact on phones).
    const word = { rising: 'Rising', steady: 'Steady', declining: 'Declining' }[expected.direction];
    const headline = (await panel.locator('.strength-headline').innerText()).replace(/\s+/g, ' ');
    assert.ok(headline.includes(word), headline);
    assert.ok(headline.includes(`last 3 games rank #${expected.momentumRank} of ${expected.teams}, season #${expected.seasonRank}`), headline);
    assert.equal(await panel.locator(`.trend-badge.${expected.direction}`).count(), 1);
    const details = panel.locator('details.strength-details');
    assert.equal(await details.evaluate(d => d.open), false, 'breakdown collapsed by default');
    const closedHeight = (await panel.boundingBox()).height;
    if (width < 768) assert.ok(closedHeight <= 260, `compact on phones: ${closedHeight}px`);
    await details.locator('summary').click();
    const values = await panel.locator('.strength-tile strong').allTextContents();
    assert.deepEqual(values, [`#${expected.seasonRank}`, `#${expected.momentumRank}`, `#${expected.combinedRank}`]);
    const labels = await panel.locator('.strength-tile small').allTextContents();
    assert.deepEqual(labels, ['Season Strength', 'Recent Momentum', 'Combined Strength']);
    const text = await panel.innerText();
    assert.match(text, /official predictions, rankings and playoff odds use Season Strength/);
    assert.match(text, /80% season, 20% recent momentum/);
    assert.ok(text.includes(`Rating ${expected.season.toFixed(1)} (the Current Strength above)`), 'season value referenced, not repeated as a headline number');
    // One trend label on the page: the older win-based trend is no longer shown on the Team Profile.
    assert.equal(await page.locator('#profile-panel').getByText('Season trend:', { exact: false }).count(), 0);
    assert.equal(await page.locator('.team-profile-tile').filter({ hasText: 'Current-Season Form Trend' }).count(), 0);
    // The official Current Strength tile is unchanged and equals Season Strength.
    const official = await page.locator('#profile-panel > .team-profile-grid .team-profile-tile').filter({ hasText: 'Current Strength' }).locator('strong').textContent();
    assert.equal(official, report.rankings.find(t => t.team === TEAM).rating.toFixed(1));
    assert.equal(await page.locator('#profile-panel > .team-profile-grid .team-profile-tile').count(), 6, 'released overview grid unchanged');
    // Recent form consolidated: no separate card in the default flow; everything reachable inside the collapsed details.
    assert.equal(await page.locator('#profile-panel .recent-form').count(), 0, 'no separate Recent form card');
    const more = page.locator('#profile-panel details.profile-more');
    assert.equal(await more.evaluate(d => d.open), false, 'Form, conference and postseason details collapsed by default');
    assert.equal(await more.locator('.profile-more-form').isVisible(), false);
    const summary = more.locator('summary').first();
    await summary.scrollIntoViewIfNeeded();
    const nav = await page.getByRole('navigation', { name: 'Main navigation', exact: true }).boundingBox();
    const sum = await summary.boundingBox();
    if (width < 768) assert.ok(sum.y + sum.height <= nav.y + 1, 'bottom navigation does not cover the details control');
    await summary.focus(); await page.keyboard.press('Enter');                       // keyboard opens it
    assert.equal(await more.evaluate(d => d.open), true);
    const form = more.locator('.profile-more-form');
    await form.getByRole('heading', { name: 'Form and forecasts' }).waitFor();
    assert.match(await form.innerText(), /Against forecasts:/);
    assert.equal(await more.locator('.team-profile-tile').filter({ hasText: 'Last Five Completed Games' }).count(), 1, 'last-five record remains available');
    const howTo = form.locator('details').filter({ hasText: 'How to read form and forecasts' });
    await howTo.locator('summary').click();
    assert.match(await howTo.innerText(), /Last five completed games:/);
    await summary.focus(); await page.keyboard.press('Enter');                       // and closes it
    assert.equal(await more.evaluate(d => d.open), false);
    const contrast = await panel.evaluate(root => {
      const rgb = c => (c.match(/[\d.]+/g) || []).map(Number);
      const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
      const bg = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length === 3 || (c.length === 4 && c[3] > 0.9)) return c.slice(0, 3); } return [11, 18, 32]; };
      return [...root.querySelectorAll('h4,small,strong,span,p')].map(e => { const a = lum(rgb(getComputedStyle(e).color).slice(0, 3)), b = lum(bg(e)); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); });
    });
    assert.ok(Math.min(...contrast) >= 4.5, `contrast ${Math.min(...contrast).toFixed(2)}`);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 1, `overflow at ${width}`);
    assert.deepEqual(errors, []);
    if (width === 390 || width === 1536) await panel.screenshot({ path: `${evidence}/strength-breakdown-${width}.png` });
    await page.close();
    console.log(`Strength breakdown passed at ${width}px`);
  }
  console.log(`Strength breakdown acceptance passed (${TEAM}: ${expected.direction}, recent #${expected.momentumRank}, season #${expected.seasonRank}, combined #${expected.combinedRank} of ${expected.teams})`);
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}
