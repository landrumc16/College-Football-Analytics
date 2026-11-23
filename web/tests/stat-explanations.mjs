// Browser acceptance: visible numbers -> plain-English takeaway -> collapsed "What do these numbers mean?" explanation,
// across Teams, Rankings, Polls and Playoffs at five widths. Numbers must equal the published report.
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection, chooseSchool, openDestination } from './section-navigation.mjs';

const PORT = 4211, base = `http://127.0.0.1:${PORT}/`;
const evidence = process.env.EVIDENCE || 'docs/evidence/stat-explanations';
await mkdir(evidence, { recursive: true });
const report = JSON.parse(await readFile('web/public/season-report.json', 'utf8'));
const TEAM = 'Texas Tech';
const row = report.rankings.find(r => r.team === TEAM);
const perf = report.performance?.[TEAM];
const num = v => v.toFixed(2);

// The standard: a takeaway, then the numbers, then a collapsed explainer that opens and closes from the keyboard.
async function standard(page, scope, label) {
  const takeaway = scope.locator('.stat-takeaway').first();
  assert.ok(await takeaway.isVisible(), `${label}: takeaway visible`);
  const text = (await takeaway.innerText()).trim();
  assert.ok(text.length > 20 && !/undefined|NaN|null/.test(text), `${label}: ${text}`);
  const explain = scope.locator('details.stat-explain').first();
  assert.equal(await explain.evaluate(d => d.open), false, `${label}: collapsed by default`);
  const summary = explain.locator(':scope > summary');
  assert.equal((await summary.innerText()).trim(), 'What do these numbers mean?');
  await summary.focus(); await page.keyboard.press('Enter');
  assert.equal(await explain.evaluate(d => d.open), true, `${label}: opens with Enter`);
  assert.ok((await explain.locator('.stat-explain-body').innerText()).length > 80, `${label}: explanation present`);
  await page.keyboard.press('Enter');
  assert.equal(await explain.evaluate(d => d.open), false, `${label}: closes with Enter`);
  return text;
}

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  for (const width of [375, 390, 430, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: 844 }, deviceScaleFactor: width === 390 || width === 1536 ? 2 : 1 });
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(base, { waitUntil: 'networkidle' });
    // Teams: profile overview tiles stay visible with their takeaway and explainer.
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Team Profiles');
    await chooseSchool(page, 'Choose school', TEAM);
    const profile = page.locator('.team-profile');
    const tile = profile.locator('.team-profile-tile').filter({ hasText: 'Current Model Rank' }).first();
    assert.equal((await tile.locator('strong').innerText()).trim(), `#${row.rank}`);
    assert.match(await standard(page, profile, 'profile overview'), new RegExp(`No\\. ${row.rank}`));
    // Schedule & Predictions: Performance vs. Expectations (approved reference design) and the season outlook.
    await chooseSection(page, 'Team Profile sections', 'Schedule & Predictions');
    const panel = page.locator('.performance-panel');
    await panel.waitFor();
    if (perf?.games_with_forecasts) {
      const boxes = (await panel.locator('.schedule-summary').innerText()).replace(/\s+/g, ' ');
      assert.ok(boxes.includes(`GAMES WON ${perf.actual_wins}`) && boxes.includes(`EXPECTED WINS ${num(perf.expected_wins)}`)
        && boxes.includes(`ABOVE EXPECTED ${perf.wins_above_expected > 0 ? '+' : ''}${num(perf.wins_above_expected)}`), boxes);
      const said = await standard(page, panel, 'performance vs expectations');
      assert.ok(perf.wins_above_expected >= 0.25 ? /ahead/.test(said) : perf.wins_above_expected <= -0.25 ? /behind/.test(said) : /in line/.test(said), said);
      await panel.locator('details.stat-explain > summary').click();
      assert.match(await panel.locator('.stat-explain-body').innerText(), new RegExp(`${perf.games_with_forecasts} completed games? for which our prediction was saved before kickoff`));
      if (width === 390 || width === 1536) {
        await panel.evaluate(e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 70));
        await page.screenshot({ path: `${evidence}/performance-${width}.png` });
      }
      await panel.locator('details.stat-explain > summary').click();
    }
    const outlook = page.locator('.matchup-panel').filter({ hasText: 'Full Season Schedule' }).first();
    assert.match(await outlook.locator('.stat-takeaway').first().innerText(), new RegExp(`projected for about ${row.projected_wins.toFixed(1)} wins|finished its regular season`));
    // Rankings: takeaway above the table, one explainer below it.
    await openDestination(page, 'Rankings');
    await chooseSection(page, 'Rankings sections', 'Model Rankings');
    const top = [...report.rankings].sort((a, b) => a.rank - b.rank)[0];
    assert.match(await standard(page, page.locator('main'), 'model rankings'), new RegExp(`^${top.team} leads our rankings`));
    assert.equal(await page.locator('main details.stat-explain').count(), 1, 'one explanation for the rankings group');
    // Polls.
    await chooseSection(page, 'Rankings sections', 'Poll Rankings');
    assert.match(await standard(page, page.locator('.poll-rankings'), 'poll rankings'), /AP and Coaches polls share/);
    // Playoffs: simulation table.
    await openDestination(page, 'Playoffs');
    await page.locator('.stat-takeaway').filter({ hasText: 'simulated seasons' }).first().waitFor();
    const playoffs = page.locator('main');
    const said = await standard(page, playoffs, 'playoff simulations');
    assert.match(said, /make the field in at least 95% of simulated seasons/);
    if (width === 390 || width === 1536) await page.screenshot({ path: `${evidence}/playoffs-${width}.png`, fullPage: false });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert.ok(overflow <= 1, `overflow ${overflow} at ${width}`);
    assert.deepEqual(errors, [], `page errors at ${width}`);
    await page.close();
    console.log(`Statistics explanations passed at ${width}px`);
  }
  console.log('Statistics explanations acceptance passed');
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch {}
}
