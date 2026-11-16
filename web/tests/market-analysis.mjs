// Browser acceptance for the V7 Market Analysis page: discoverability, the 10-second flow, perspective,
// game switching, lazy secondary history, entry points and privacy, at 375/390/430/768/1536px.
import assert from 'node:assert/strict';
import { readFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { openDestination, PRIMARY } from './section-navigation.mjs';

const PORT = 4183;
const base = `http://127.0.0.1:${PORT}/`;
const report = JSON.parse(await readFile('web/public/season-report.json', 'utf8'));
const metrics = JSON.parse(await readFile('web/public/v7-market-metrics.json', 'utf8'));
const byId = new Map(report.predictions.map(p => [String(p.game_id), p]));
const evidence = 'docs/evidence/v7-market-analysis';
await mkdir(evidence, { recursive: true });
const fmt = (v, d = 1) => { const r = Number(v.toFixed(d)); return Math.abs(r) < 1e-9 ? (0).toFixed(d) : (r > 0 ? '+' : '') + r.toFixed(d); };

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  for (const width of [375, 390, 430, 768, 1536]) {
    const height = width === 1536 ? 900 : 844;
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: [390, 768, 1536].includes(width) ? 2 : 1 });
    const requests = [];
    page.on('request', r => requests.push({ url: r.url(), body: r.postData() || '' }));
    await page.goto(base);

    // Discoverable from the homepage without scrolling.
    const entry = page.getByRole('region', { name: 'Market Analysis', exact: true });
    const box = await entry.boundingBox();
    assert.ok(box && box.y >= 0 && box.y + box.height <= height, `entry card must be in the first screen at ${width}: ${JSON.stringify(box)}`);
    if (width === 390 || width === 1536) await page.screenshot({ path: `${evidence}/home-entry-${width}.png` });

    // One tap opens the calculator with an upcoming published forecast already selected.
    await entry.getByRole('button', { name: 'Open calculator' }).click();
    await page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 }).waitFor();
    const game = page.getByLabel('Game', { exact: true });
    const first = byId.get(await game.inputValue());
    assert.ok(first, 'selected game must be a published prediction');
    const calc = page.locator('.market-calculator');
    await calc.getByText('Published forecast', { exact: true }).waitFor();
    assert.match(await calc.locator('.market-source').textContent(), new RegExp(`Week ${first.week} pregame forecast`));
    assert.ok(await calc.getByRole('radio', { name: first.home }).isChecked(), 'home team analysed by default');
    assert.equal(requests.filter(r => r.url.includes('v7-market-metrics.json')).length, 0, 'history must load only when opened');

    // Type a number and read the result immediately: no submit step. The ± button supplies the minus sign.
    const spread = calc.getByLabel(`${first.home} point spread`);
    await spread.fill('6.5');
    await calc.getByRole('button', { name: 'Switch spread sign (plus/minus)' }).click();
    assert.equal(await spread.inputValue(), '-6.5');
    const result = calc.locator('.market-result').first();
    const d = fmt(first.home_margin - 6.5);
    assert.ok((await result.textContent()).replace(/\s+/g, ' ').includes(`Difference${d} points`));
    const headline = await result.locator('.market-headline').textContent();
    assert.match(headline, Math.abs(Number(d)) < 0.05 ? /matches/ : new RegExp(`${Math.abs(Number(d)).toFixed(1)} points? ${Number(d) > 0 ? 'more' : 'less'} favourable to ${first.home}`));
    await calc.getByLabel(`${first.home} American moneyline`).fill('130');
    await calc.getByRole('button', { name: 'Switch moneyline sign (plus/minus)' }).click();
    assert.equal(await calc.getByLabel(`${first.home} American moneyline`).inputValue(), '-130');
    assert.ok((await calc.locator('.market-result').nth(1).textContent()).includes('56.5% raw implied'));
    if (width === 390 || width === 768 || width === 1536) await page.screenshot({ path: `${evidence}/market-analysis-${width}.png`, fullPage: true });

    // Team switch: the same market from the other side; differences reverse.
    await calc.getByText(first.away, { exact: true }).click();
    assert.equal(await calc.getByLabel(`${first.away} point spread`).inputValue(), '+6.5');
    assert.ok((await calc.locator('.market-result').first().textContent()).replace(/\s+/g, ' ').includes(`Difference${fmt(-first.home_margin + 6.5)} points`));

    // Changing the game resets entries and re-labels provenance.
    const options = await game.locator('option').evaluateAll(os => os.map(o => o.value));
    if (options.length > 1) {
      await game.selectOption(options[1]);
      const second = byId.get(options[1]);
      assert.equal(await calc.getByLabel(`${second.home} point spread`).inputValue(), '');
      assert.match(await calc.locator('.market-source').textContent(), new RegExp(`Week ${second.week} pregame forecast`));
      await game.selectOption(options[0]);
    }

    // Secondary history: lazily loaded aggregates that match the published metrics.
    await page.getByText(`Historical ATS and over/under records for ${first.away} and ${first.home}`).click();
    const table = page.locator('.market-history table');
    await table.waitFor();
    for (const team of [first.home, first.away]) {
      const t = metrics.teams[team]?.overall;
      if (t) assert.ok((await table.getByRole('row', { name: new RegExp(team.replace(/[()]/g, '\\$&')) }).textContent()).includes(`${t.ats.w}-${t.ats.l}-${t.ats.p}`));
    }

    // No horizontal overflow.
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 1, `overflow at ${width}`);

    // Privacy: entered values never leave the page or persist.
    const stored = await page.evaluate(() => JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }) + location.href);
    for (const value of ['6.5', '130']) {
      assert.ok(!stored.includes(value));
      assert.ok(!requests.some(r => new URL(r.url).search.includes(value) || r.body.includes(value)), `${value} transmitted`);
    }

    // Other entry points: "Other matchup" opens Compare; a prediction card opens this game directly.
    await page.getByRole('button', { name: 'Other matchup' }).click();
    await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
    await page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: 'Home', exact: true }).click();
    await page.getByRole('button', { name: 'All games', exact: false }).click();
    const card = page.locator('.prediction-card').filter({ has: page.getByRole('button', { name: 'Market analysis' }) }).first();
    const cardText = (await card.locator('.prediction-matchup').textContent()).replace(/\s+/g, ' ');
    await card.getByRole('button', { name: 'Market analysis' }).click();
    const opened = byId.get(await page.getByLabel('Game', { exact: true }).inputValue());
    assert.ok(cardText.includes(opened.home) && cardText.includes(opened.away), 'card opens its own game');
    await page.close();
    console.log(`Market Analysis page passed at ${width}px`);
  }
  // Information architecture: five-item bottom bar, Market as a destination, Research & Data in the menu,
  // deep links and Back/Forward, and the calculator present only on Market Analysis.
  for (const width of [390, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1536 ? 900 : 844 } });
    const nav = page.getByRole('navigation', { name: 'Main navigation', exact: true });
    await page.goto(base);
    await nav.getByRole('button', { name: 'Home', exact: true }).waitFor();
    assert.deepEqual(await nav.getByRole('button').allTextContents(), PRIMARY);
    assert.equal(await page.locator('.market-calculator').count(), 0, 'homepage links to the calculator but never embeds it');
    await nav.getByRole('button', { name: 'Market', exact: true }).click();
    await page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 }).waitFor();
    assert.equal(await nav.getByRole('button', { name: 'Market', exact: true }).getAttribute('aria-current'), 'page');
    assert.ok(page.url().endsWith('#/market'));
    await openDestination(page, 'Research');
    await page.getByRole('region', { name: 'Independent pregame forecast verification', exact: true }).waitFor();
    assert.ok(page.url().endsWith('#/research'));
    assert.equal(await page.locator('details.editorial-menu').evaluate(d => d.open), false, 'menu closes after choosing Research & Data');
    await page.goBack();
    await page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 }).waitFor();
    await page.goBack();
    await page.getByRole('heading', { name: 'Featured Matchups', exact: true }).waitFor();
    await page.goForward();
    await page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 }).waitFor();
    for (const [hash, check] of [['#/market', () => page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 })],
                                 ['#/research', () => page.getByRole('region', { name: 'Independent pregame forecast verification', exact: true })],
                                 ['#/compare', () => page.getByRole('heading', { name: 'Compare Teams', exact: true })],
                                 ['#/cfp', () => page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: 'Playoffs', exact: true, pressed: undefined })],
                                 ['#/not-a-view', () => page.getByRole('heading', { name: 'Featured Matchups', exact: true })]]) {
      await page.goto(base + hash);
      await check().waitFor();
    }
    assert.equal(await nav.getByRole('button', { name: 'Playoffs', exact: true }).count(), 1);
    await page.close();
    console.log(`Navigation, deep links and Back/Forward passed at ${width}px`);
  }
  console.log('Market Analysis acceptance passed');
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}
