// Cross-browser device-profile acceptance (preserved from V9): the owner's device checklist automated on WebKit (Safari
// engine: iPhone SE, 13, 14 Pro Max, iPad Mini) and Chromium (Pixel 7, Galaxy S9+) profiles. EMULATION: real browser
// engines with device viewports, touch and mobile user agents; not physical hardware. Offline-app steps are recorded
// but not asserted on WebKit, whose headless Linux build crashes after a service worker registers (a test-engine
// limitation; see docs/V9-DEVICE-TESTING.md). Exits non-zero on any journey defect, overflow or page error.
// Usage: node web/tests/device-profiles.mjs <evidence-dir>   (after node scripts/v9_preview.mjs)
import { writeFile, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium, webkit, devices } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection, openDestination } from './section-navigation.mjs';

const out = process.argv[2];
const PORT = 4391, base = `http://127.0.0.1:${PORT}/`;
const DEST = ['Home', 'Rankings', 'Teams', 'Playoffs', 'Research'];
const PROFILES = [['iPhone SE', webkit], ['iPhone 13', webkit], ['iPhone 14 Pro Max', webkit], ['iPad Mini', webkit], ['Pixel 7', chromium], ['Galaxy S9+', chromium]];
const server = spawn('npx', ['vite', 'preview', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
// Freeze the clock to the actual staged data; choose only games it still lists as unplayed.
const fixtureReport = JSON.parse(await readFile('web/dist/season-report.json', 'utf8'));
const fixtureIntelligence = JSON.parse(await readFile('web/dist/team-intelligence.json', 'utf8'));
const fixtureAccountability = JSON.parse(await readFile('web/dist/v9-accountability.json', 'utf8'));
const pendingIds = new Set(fixtureReport.schedule.filter(g => !g.completed).map(g => g.game_id));
const fieldChance = new Map((fixtureReport.cfp?.teams || []).map(t => [t.team, t.cfp_field]));
const pendingPredictions = fixtureReport.predictions.filter(p => pendingIds.has(p.game_id));
const bubbleDistance = g => Math.min(...[g.home, g.away].map(t => Math.abs((fieldChance.get(t) ?? 0) - 0.5)));
const scenarioGame = pendingPredictions.find(g => [g.home, g.away].includes('Texas Tech'))
  || [...pendingPredictions].sort((a, b) => bubbleDistance(a) - bubbleDistance(b))[0];
const results = {}, defects = [];
const overflow = p => p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
async function pick(page, label, team) {
  const field = page.getByLabel(new RegExp('^' + label + '$', 'i')).locator('visible=true').first();
  if (await field.evaluate(e => e.tagName) === 'SELECT') return field.selectOption(team);
  await field.fill(team); await page.waitForTimeout(250);
  const list = await field.getAttribute('aria-controls');
  const option = list ? page.locator(`#${list.replace(/:/g, '\\:')}`).getByRole('option', { name: team, exact: true }) : null;
  if (option && await option.count()) await option.tap();
}
const openDetails = async (loc) => { if (!(await loc.evaluate(s => s.parentElement.open))) await loc.tap(); };
try {
  for (let i = 0; i < 60; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(300); }
  for (const [name, engine] of PROFILES) {
    const browser = startAsDeclinedVisitor(await engine.launch());
    const ctx = await browser.newContext({ ...devices[name] });
    const page = await ctx.newPage(); await page.clock.setFixedTime(fixtureReport.retrieved_at); const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const R = { engine: engine.name(), viewport: devices[name].viewport, destinations: {}, journeys: {} };
    await page.goto(base, { waitUntil: 'networkidle' });
    for (const d of DEST) {
      await page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: d, exact: true }).tap();
      await page.waitForTimeout(700);
      R.destinations[d] = { overflow: await overflow(page) };
      if (R.destinations[d].overflow > 1) defects.push(`${name}: ${d} overflow ${R.destinations[d].overflow}px`);
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${out}/${name.replace(/\W+/g, '-').toLowerCase()}-${d.toLowerCase()}.png` });
    }
    const J = R.journeys;
    // Favorites: save, browse another school, persists across reload.
    await openDestination(page, 'Home'); await page.waitForTimeout(300);
    await openDetails(page.locator('summary', { hasText: 'Edit Teams' }));
    await openDetails(page.locator('summary', { hasText: '+ Add Team' }));
    await pick(page, 'Add Favorite Team', 'Texas Tech');
    await page.getByRole('button', { name: 'Save Team', exact: true }).tap(); await page.waitForTimeout(500);
    await openDestination(page, 'Teams'); await chooseSection(page, 'Teams sections', 'Team Profiles');
    await pick(page, 'Choose School', 'Baylor'); await page.waitForTimeout(400);
    await openDestination(page, 'Home'); await page.waitForTimeout(400);
    await page.reload({ waitUntil: 'networkidle' });
    J.favoritePersistsAndIndependent = /Texas Tech/.test(await page.locator('section.editorial-my-teams').innerText());
    // Rankings evaluation filter.
    await openDestination(page, 'Rankings'); await chooseSection(page, 'Rankings sections', 'Model Rankings');
    await page.getByLabel(/^Evaluation/).locator('visible=true').first().selectOption({ label: 'Current Playing Level · Last Three' });
    await pick(page, 'Find School in Intelligence', 'Texas Tech');
    await openDetails(page.locator('main details > summary', { hasText: 'Current Playing Level · Last Three' }).first());
    J.rankingsFilter = (await page.locator('main').innerText()).includes(fixtureIntelligence.teams.find(t => t.team === 'Texas Tech').current_level.value.toFixed(1));
    // Teams: trajectory, matchup, projections.
    await openDestination(page, 'Teams'); await chooseSection(page, 'Teams sections', 'Team Profiles'); await pick(page, 'Choose School', 'Texas Tech');
    const traj = page.locator('details.profile-more', { hasText: 'Team Trajectory' }).first();
    await openDetails(traj.locator(':scope > summary'));
    { // One retained observation: no trend claimed. Several: retained-observation wording, one plotted point each.
      const n = await traj.locator('select option').count(), text = await traj.innerText();
      const points = await traj.locator('svg.intelligence-chart circle').count();
      J.trajectory = n === 1 ? /cannot establish a trend/i.test(text) : n > 1 && /retained model observations, not a reconstructed season/i.test(text) && points === n;
      R.trajectoryObservations = n; }
    await chooseSection(page, 'Teams sections', 'Compare & What If');
    await pick(page, 'First School', 'Texas Tech'); await pick(page, 'Second School', 'Baylor');
    await page.getByLabel(/^game location$/i).selectOption('neutral'); await page.waitForTimeout(300);
    J.matchup = (await page.locator('.matchup-result').innerText()).includes(Math.abs(fixtureReport.rankings.find(t => t.team === 'Texas Tech').rating - fixtureReport.rankings.find(t => t.team === 'Baylor').rating).toFixed(2));
    await chooseSection(page, 'Teams sections', 'Model Projections');
    await page.locator('label', { hasText: 'Momentum' }).first().tap(); await page.waitForTimeout(300);
    J.projections = /Momentum/.test(await page.locator('main').innerText()) && await overflow(page) <= 1;
    await chooseSection(page, 'Teams sections', 'Offense & Defense'); await page.waitForTimeout(500);
    J.offenseDefenseNoOverflow = await overflow(page) <= 1;
    // Research: calibration and Market.
    await openDestination(page, 'Research'); await chooseSection(page, 'Research sections', 'Prediction Accuracy'); await page.waitForTimeout(400);
    await openDetails(page.locator('details', { hasText: 'Three-Model Prediction Accountability' }).locator(':scope > summary', { hasText: 'Three-Model Prediction Accountability' }).first());
    const cal = page.locator('details.stat-explain', { hasText: 'Probability Calibration' }).first();
    await openDetails(cal.locator(':scope > summary'));
    await cal.getByLabel('Model').selectOption('official'); J.calibration = (await cal.innerText()).includes(`${fixtureAccountability.models.official.games} settled`);
    await chooseSection(page, 'Research sections', 'Market Intelligence'); await page.waitForTimeout(400);
    J.market = /Market/.test(await page.locator('main h2').first().innerText());
    // Playoffs what-if: override and exact reset.
    await openDestination(page, 'Playoffs'); await page.getByRole('button', { name: 'Explore Scenarios' }).tap();
    const sc = page.locator('[aria-label="Playoff what-if scenarios"]');
    await page.waitForFunction(() => document.querySelector('[aria-label="Playoff what-if scenarios"] .table-wrap[aria-busy="false"]'), null, { timeout: 60000 });
    const baseline = await sc.locator('tbody').innerText();
    if (scenarioGame) {
      await page.getByRole('combobox', { name: 'Scenario matchup', exact: true }).selectOption(String(scenarioGame.game_id));
      const forcedWinner = scenarioGame.predicted_winner === scenarioGame.home ? scenarioGame.away : scenarioGame.home;
      await page.getByRole('combobox', { name: 'Scenario winner', exact: true }).selectOption(forcedWinner);
      await page.waitForFunction(() => { const s = document.querySelector('[aria-label="Playoff what-if scenarios"]'); return /1 pick applied/.test(s.innerText) && s.querySelector('.table-wrap[aria-busy="false"]') }, null, { timeout: 60000 });
      await page.waitForTimeout(500);
      const changed = await sc.locator('tbody').innerText();
      R.scenarioDebug = { gameId: scenarioGame.game_id, forcedWinner, status: (await sc.getByRole('status').first().innerText().catch(() => '')).slice(0, 120), baselineHead: baseline.slice(0, 120), changedHead: changed.slice(0, 120), techBaseline: (baseline.split('\n').find(l => l.includes('Texas Tech')) || '').slice(0, 120), techChanged: (changed.split('\n').find(l => l.includes('Texas Tech')) || '').slice(0, 120) };
      await sc.scrollIntoViewIfNeeded(); await page.screenshot({ path: `${out}/${name.replace(/\W+/g, '-').toLowerCase()}-scenario.png` });
      await sc.getByRole('button', { name: 'Reset to Baseline', exact: true }).tap();
      await page.waitForFunction(b => document.querySelector('[aria-label="Playoff what-if scenarios"] tbody')?.innerText === b, baseline, { timeout: 60000 });
      J.scenarioOverrideAndExactReset = changed !== baseline;
    } else {
      J.noRemainingScenarioChoices = await page.getByRole('combobox', { name: 'Scenario matchup', exact: true }).locator('option').count() === 1;
      await sc.getByRole('button', { name: 'Reset to Baseline', exact: true }).tap();
      J.emptySeasonExactReset = await sc.locator('tbody').innerText() === baseline;
      R.scenarioDebug = { reason: 'No unplayed games: override is unavailable; empty-state and exact reset verified' };
    }
    // Touch targets on phones.
    R.smallTargets = await page.evaluate(() => [...document.querySelectorAll('button, select, summary, input')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height && (r.width < 24 || r.height < 24) }).length);
    // Offline app: worker, offline page, recovery.
    try {
      R.serviceWorker = await page.evaluate(async () => !!(await Promise.race([navigator.serviceWorker.ready, new Promise(r => setTimeout(() => r(null), 8000))])));
      await page.goto(base, { waitUntil: 'load' }).catch(e => { R.reloadError = e.message.slice(0, 120) }); await page.waitForTimeout(1000);
      R.controlled = await page.evaluate(() => !!navigator.serviceWorker.controller).catch(e => { R.controlError = e.message.slice(0, 120); return null });
      await ctx.setOffline(true);
      await page.goto(base, { waitUntil: 'domcontentloaded' }).catch(e => { R.offlineNavError = e.message.slice(0, 120) }); await page.waitForTimeout(1500);
      R.offlineText = (await page.locator('body').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 160);
      R.offlinePage = /offline/i.test(R.offlineText);
      await page.screenshot({ path: `${out}/${name.replace(/\W+/g, '-').toLowerCase()}-offline.png` }).catch(() => {});
      await ctx.setOffline(false); await page.goto(base, { waitUntil: 'networkidle' });
      R.onlineRecovered = /College Football/.test(await page.locator('h1').first().innerText());
    } catch (e) { R.pwaError = e.message.slice(0, 160); }
    for (const [k, v] of Object.entries(J)) if (!v) defects.push(`${name}: journey ${k} failed`);
    R.errors = errors; if (errors.length) defects.push(`${name}: page errors ${errors.join(' | ').slice(0, 200)}`);
    results[name] = R;
    await browser.close();
  }
} finally {
  try { process.kill(-server.pid, 'SIGTERM'); } catch {}
  await writeFile(`${out}/device-profile-results.json`, JSON.stringify({ results, defects }, null, 1));
  if (defects.length) process.exitCode = 1;
  console.log(JSON.stringify({ defects, summary: Object.fromEntries(Object.entries(results).map(([k, v]) => [k, { engine: v.engine, journeys: v.journeys, sw: v.serviceWorker, controlled: v.controlled, offline: v.offlinePage, offlineText: v.offlineText, offlineNavError: v.offlineNavError, reloadError: v.reloadError, recovered: v.onlineRecovered, pwaError: v.pwaError, scenario: v.scenarioDebug }])) }, null, 1));
}
