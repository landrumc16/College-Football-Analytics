// Browser acceptance for the V7 Market Analysis Calculator at five widths.
// Covers published vs hypothetical model sources, perspective reversal, invalid input, missing model data,
// keyboard use, layout, and that entered market numbers never leave the page (requests, URL, storage).
import assert from 'node:assert/strict';
import { readFile, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection } from './section-navigation.mjs';

const PORT = 4181;
const base = `http://127.0.0.1:${PORT}/`;
const report = JSON.parse(await readFile('web/public/season-report.json', 'utf8'));
const fbs = new Set(report.rankings.map(t => t.team));
const game = report.predictions.find(p => fbs.has(p.home) && fbs.has(p.away) && !p.neutral_site);
assert.ok(game, 'need a scheduled FBS-vs-FBS home/away prediction');
const scheduledNeutral = report.predictions.some(p => p.home === game.home && p.away === game.away && p.neutral_site);
const evidence = 'docs/evidence/v7-market-calculator';
await mkdir(evidence, { recursive: true });

// Independent expectations (plain arithmetic, not the app module).
const fmt = (v, d = 1) => { const r = Number(v.toFixed(d)); return Math.abs(r) < 1e-9 ? (0).toFixed(d) : (r > 0 ? '+' : '') + r.toFixed(d); };
const SPREAD = '-6.5', PROB = '41.3', LINE = '+137';
const homeProbDiff = fmt(100 * (game.home_win_probability - 0.413));
const homeLineDiff = fmt(100 * (game.home_win_probability - 100 / 237));
const awayProbDiff = fmt(100 * ((1 - game.home_win_probability) - 0.587));

async function openCompare(page) {
  await page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: 'Teams', exact: true }).click();
  await chooseSection(page, 'Teams sections', 'Compare & What If');
}

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());

  for (const width of [320, 375, 390, 430, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: width === 390 ? 2 : 1 });
    const outbound = [];
    page.on('request', r => outbound.push(`${r.url()} ${r.postData() || ''}`));
    await page.goto(base);
    await openCompare(page);
    await page.getByLabel('First school').selectOption(game.home);
    await page.getByLabel('Second school').selectOption(game.away);
    await page.getByLabel('Game location').selectOption('home');
    // Compare holds no calculator: it links to the one Market Analysis page and carries the matchup in memory.
    assert.equal(await page.locator('.market-calculator').count(), 0, 'calculator must live only on Market Analysis');
    await page.getByRole('button', { name: 'Compare this matchup with a market line in Market Analysis' }).click();
    await page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 }).waitFor();
    assert.match(await page.locator('.market-selected-game').textContent(), new RegExp(game.home), 'selected matchup transferred');
    assert.ok(page.url().endsWith('#/market') && !/[?&]/.test(new URL(page.url()).hash), 'only the view name is in the URL');
    const calc = page.locator('.market-calculator');
    await calc.getByRole('heading', { name: 'Market Analysis Calculator' }).waitFor();
    await calc.getByText('Published forecast', { exact: true }).waitFor();
    assert.match(await calc.locator('.market-source').textContent(), new RegExp(`Week ${game.week} pregame forecast`));

    // Accessible names, touch targets, keyboard-reachable radios.
    const spread = calc.getByLabel(`${game.home} point spread`);
    const prob = calc.getByLabel(`${game.home} prediction-market win probability (%)`);
    const line = calc.getByLabel(`${game.home} American moneyline`);
    for (const input of [spread, prob, line]) assert.ok((await input.boundingBox()).height >= 44);
    assert.equal(await calc.getByRole('group', { name: '1. Analyze for' }).count(), 1);

    await spread.fill(SPREAD); await prob.fill(PROB); await line.fill(LINE);
    const results = calc.locator('.market-result');
    await assert.doesNotReject(results.nth(2).waitFor());
    const text = async i => (await results.nth(i).textContent()).replace(/\s+/g, ' ');
    assert.ok((await text(0)).includes('Our prediction') && (await text(0)).includes('What this means') && (await text(0)).includes('Our take'), await text(0));
    assert.ok((await text(1)).includes(`Difference${homeProbDiff} percentage points`), await text(1));
    assert.ok((await text(2)).includes(`Difference${homeLineDiff} percentage points`), await text(2));
    assert.ok((await text(2)).includes('42.2% raw implied'));
    assert.equal(await calc.getByText('Market number entered by you; not retrieved or verified by this app.').count(), 2);
    assert.match(await calc.textContent(), /not removed/);
    assert.match(await calc.textContent(), /not a forecast of profit or a recommendation to wager/);

    // Switch perspective with the keyboard: spread and probability are re-expressed, moneyline cleared.
    await calc.getByRole('radio', { name: game.home }).focus();
    await page.keyboard.press('ArrowRight');
    assert.ok(await calc.getByRole('radio', { name: game.away }).isChecked());
    const awaySpread = calc.getByLabel(`${game.away} point spread`);
    assert.equal(await awaySpread.inputValue(), '+6.5');
    assert.equal(await calc.getByLabel(`${game.away} prediction-market win probability (%)`).inputValue(), '58.7');
    assert.equal(await calc.getByLabel(`${game.away} American moneyline`).inputValue(), '');
    await calc.getByText(`Moneyline cleared: enter ${game.away}'s own moneyline`, { exact: false }).waitFor();
    assert.ok((await text(0)).includes('Our take'), await text(0));
    assert.ok((await text(1)).includes(`Difference${awayProbDiff} percentage points`), await text(1));
    if (width === 390 || width === 1536) await calc.screenshot({ path: `${evidence}/calculator-${width}.png` });

    // Invalid entries are explained, flagged and produce no comparison.
    const awayLine = calc.getByLabel(`${game.away} American moneyline`);
    await awayLine.fill('50');
    await calc.getByText('American odds must be +100 or higher, or -100 or lower.').waitFor();
    assert.equal(await awayLine.getAttribute('aria-invalid'), 'true');
    await calc.getByLabel(`${game.away} prediction-market win probability (%)`).fill('120');
    await calc.getByText('A probability cannot be more than 100%.').waitFor();
    assert.equal(await results.count(), 1);
    await awaySpread.fill('PK');
    assert.ok((await text(0)).includes('pick’em'));

    // Accessibility: WCAG AA contrast for every calculator text element and visible keyboard focus.
    // Reflow: 320px is WCAG 1.4.10 (1280px at 400%); 200% zoom of a 768px window is a 384px layout (covered by 375/390).
    const contrast = await calc.evaluate(root => {
      const rgb = c => (c.match(/[\d.]+/g) || []).map(Number);
      const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
      const bg = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length === 3 || (c.length === 4 && c[3] > 0.9)) return c.slice(0, 3); } return [11, 18, 32]; };
      return [...root.querySelectorAll('h3,p,label,small,dt,dd,legend,.market-badge,.market-error,strong')].filter(e => e.textContent.trim() && e.getClientRects().length)
        .map(e => { const a = lum(rgb(getComputedStyle(e).color).slice(0, 3)), b = lum(bg(e)); return { text: e.textContent.trim().slice(0, 40), ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) }; });
    });
    const low = contrast.filter(c => c.ratio < 4.5);
    assert.deepEqual(low, [], `contrast below 4.5:1 at ${width}: ${JSON.stringify(low)}`);
    await awaySpread.focus();
    assert.notEqual(await awaySpread.evaluate(e => getComputedStyle(e).outlineStyle), 'none', 'visible focus outline');
    // Layout: no horizontal overflow at any width.
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `horizontal overflow ${overflow}px at ${width}`);

    // Privacy: entered numbers never appear in requests, the URL or storage.
    const stored = await page.evaluate(() => JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }) + location.href);
    for (const value of ['6.5', '41.3', '58.7', '137', '120']) {
      assert.ok(!stored.includes(value), `entered value ${value} persisted`);
      assert.ok(!outbound.some(r => { const [url, body] = r.split(' '); return new URL(url).search.includes(value) || (body || '').includes(value); }), `entered value ${value} transmitted`);
    }

    // A different venue is not the scheduled game: hypothetical source, entries reset.
    if (!scheduledNeutral) {
      // Browser Back returns to Compare with the matchup intact; a non-scheduled venue carries over as a hypothetical.
      await page.goBack();
      await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
      assert.equal(await page.getByLabel('First school').inputValue(), game.home);
      await page.getByLabel('Game location').selectOption('neutral');
      await page.getByRole('button', { name: 'Compare this matchup with a market line in Market Analysis' }).click();
      await calc.getByText('Hypothetical matchup', { exact: true }).waitFor();
      assert.match(await page.locator('.market-selected-game').textContent(), new RegExp(game.home));
      assert.equal(await calc.getByLabel(`${game.home} point spread`).inputValue(), '');
    }
    await page.close();
    console.log(`Market calculator passed at ${width}px`);
  }

  // Missing model output: remove the scheduled game's published probability. The calculator must say so and never estimate it.
  const page = await browser.newPage({ viewport: { width: 390, height: 900 } });
  await page.route('**/season-report.json', async route => {
    const body = JSON.parse(await (await route.fetch()).text());
    body.predictions = body.predictions.map(p => p.game_id === game.game_id ? { ...p, home_win_probability: null } : p);
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
  });
  await page.goto(base);
  await openCompare(page);
  await page.getByLabel('First school').selectOption(game.home);
  await page.getByLabel('Second school').selectOption(game.away);
  await page.getByLabel('Game location').selectOption('home');
  await page.getByRole('button', { name: 'Compare this matchup with a market line in Market Analysis' }).click();
  const missing = page.locator('.market-calculator');
  await missing.getByText('Model prediction unavailable for this matchup', { exact: false }).waitFor();
  assert.equal(await missing.locator('input[inputmode]').count(), 0);
  console.log('Market calculator shows unavailable (no estimate) when the model output is missing');
  await page.close();
  console.log('Market calculator acceptance passed');
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}
