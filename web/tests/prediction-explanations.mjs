// Browser acceptance: "Why This Prediction?" inside Game Predictions cards, five widths plus an Android-sized phone.
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium, devices } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { openDestination } from './section-navigation.mjs';

const PORT = 4208, base = process.env.BASE || `http://127.0.0.1:${PORT}/`;
const evidence = process.env.EVIDENCE || 'docs/evidence/prediction-explanations';
await mkdir(evidence, { recursive: true });
const data = JSON.parse(await readFile(process.env.DATA || 'web/public/prediction-explanations.json', 'utf8'));
// Explain only games the served report still lists as upcoming with the same official margin.
const report = JSON.parse(await readFile(process.env.REPORT || 'web/public/season-report.json', 'utf8'));
const upcoming = new Set(report.schedule.filter(g => !g.completed).map(g => g.game_id));
const shown = new Map(report.predictions.map(p => [p.game_id, p]));
const usable = data.games.filter(g => upcoming.has(g.game_id) && Math.abs(shown.get(g.game_id).home_margin - g.official.home_margin) < 0.01);
// Exact audit wording applies only to the audited pregame snapshot; other data gets the structural checks.
const auditCase = data.data_retrieved_at === '2026-11-20T06:48:33.393964+00:00' ? usable.find(g => g.home === 'Baylor' && g.away === 'Texas Tech') : undefined;
const tt = auditCase || usable[0];
const other = usable.find(g => ![g.home, g.away].some(t => [tt.home, tt.away].includes(t)));
assert.ok(tt && other, 'at least two current explained games');
if (!auditCase) console.log(`Texas Tech at Baylor is no longer upcoming in the served report; verifying ${tt.away} at ${tt.home} instead`);

async function contrast(root) {
  return root.evaluate(el => {
    const rgb = c => (c.match(/[\d.]+/g) || []).map(Number);
    const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const bg = e => { for (; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length === 3 || (c.length === 4 && c[3] > 0.9)) return c.slice(0, 3); } return [11, 22, 38]; };
    return [...el.querySelectorAll('*')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getClientRects().length)
      .map(e => { const a = lum(rgb(getComputedStyle(e).color).slice(0, 3)), b = lum(bg(e)); return { text: e.textContent.trim().slice(0, 30), ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) }; })
      .filter(x => x.ratio < 4.5);
  });
}

async function openPredictions(page) {
  await page.goto(base, { waitUntil: 'networkidle' });
  await openDestination(page, 'Home');
  await page.getByRole('button', { name: 'All Games', exact: false }).click();
  await page.getByRole('heading', { name: 'Game Predictions', level: 2 }).waitFor();
}

async function cardFor(page, g) {
  const search = page.getByLabel('Search teams');
  await search.fill(g.away);
  const card = page.locator('article.prediction-card').filter({ hasText: g.away }).filter({ hasText: g.home }).first();
  await card.waitFor();
  return card;
}

async function openWhy(page, card) {
  const why = card.locator('details.pick-explanation');
  assert.ok(!(await why.evaluate(d => d.open)), 'collapsed by default');
  await why.locator(':scope > summary').focus(); await page.keyboard.press('Enter');   // keyboard-operable
  await why.locator('.why-prediction').waitFor();
  return why;
}

const server = process.env.BASE ? { pid: 0 } : spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  if (!process.env.BASE) for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  const contexts = [375, 390, 430, 768, 1536].map(width => ({ label: `${width}px`, options: { viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: width === 390 || width === 1536 ? 2 : 1 } }));
  contexts.push({ label: 'Android Pixel 7', options: { ...devices['Pixel 7'] } });
  for (const { label, options } of contexts) {
    const ctx = await browser.newContext(options), page = await ctx.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await openPredictions(page);
    // Texas Tech at Baylor: the audit case.
    const card = await cardFor(page, tt);
    const fav = tt.official.home_margin >= 0 ? tt.home : tt.away;
    assert.equal((await card.locator('.prediction-pick strong').innerText()).trim(), fav);
    const why = await openWhy(page, card);
    assert.equal(await why.locator(':scope > summary').innerText(), 'Why This Prediction?');
    const text = (await why.innerText()).replace(/\s+/g, ' ');
    assert.ok(text.includes(`Official forecast: ${fav} by ${Math.abs(tt.official.home_margin).toFixed(1)} points.`), text);
    if (auditCase) {
      assert.match(text, /Texas Tech's carry-over from last season is the main reason Texas Tech is favored; this season's games alone rate the teams almost even; Baylor's home field \(3\.0 points\) works against Texas Tech\./);
      assert.match(text, /Official forecast: Texas Tech by 1\.1 points\. Standard: Texas Tech by 0\.9\. Momentum: Texas Tech by 2\.3\./);
      assert.match(text, /win over FCS Abilene Christian counts as its weakest game/);
    }
    for (const title of ['Team Strength', 'Schedule and Quality of Opponents', 'Offense vs. Defense', 'Recent Performance', 'Home Field'])
      assert.ok(new RegExp(title, 'i').test(text), `${title} at ${label}`);
    assert.match(text, /Not included in any model: Quarterback changes/);
    // The numbers sit behind a second expander; each row adds up to its forecast.
    const numbers = why.locator('details.wp-numbers');
    await numbers.locator(':scope > summary').click();
    const rows = await numbers.locator('tbody tr').allInnerTexts();
    assert.equal(rows.length, 3);
    for (const row of rows) {
      const v = row.split(/\s+/).slice(1).map(x => Number(x.replace('−', '-')));
      assert.ok(Math.abs(v[0] + v[1] + v[2] - v[3]) <= 0.15, row);
    }
    if (auditCase) assert.match(rows[0], /^Official\s+−0\.4\s+\+4\.5\s+−3\.0\s+\+1\.1$/);
    if (label === '390px' || label === '1536px') {
      await why.evaluate(e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 70));
      await page.screenshot({ path: `${evidence}/texas-tech-baylor-${label}.png` });
    }
    // Layout and accessibility with the explanation open.
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert.ok(overflow <= 1, `overflow ${overflow} at ${label}`);
    const tableOverflow = await numbers.locator('.table-wrap').evaluate(e => e.scrollWidth - e.clientWidth);
    assert.ok(tableOverflow <= 1, `numbers table overflow ${tableOverflow} at ${label}`);
    assert.deepEqual(await contrast(why), [], `contrast at ${label}`);
    // A different matchup gets its own, different explanation.
    const card2 = await cardFor(page, other);
    const why2 = await openWhy(page, card2);
    const text2 = (await why2.locator('.wp-bottom').innerText());
    assert.ok(text2.includes(other.home) || text2.includes(other.away), text2);
    assert.notEqual(text2, (await why.locator('.wp-bottom').count()) ? await why.locator('.wp-bottom').innerText() : '', 'explanations differ');
    // Existing card features remain.
    for (const name of ['Share Prediction', 'Compare Teams', 'Market Analysis']) assert.equal(await card2.getByRole('button', { name }).count(), 1, name);
    assert.deepEqual(errors, [], `page errors at ${label}`);
    await ctx.close();
    console.log(`Why this prediction passed at ${label}`);
  }
  if (!process.env.BASE) {
    // Missing data: the card keeps its published one-line summary.
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.route('**/prediction-explanations.json', route => route.fulfill({ status: 404, body: 'missing' }));
    await openPredictions(page);
    const card = await cardFor(page, tt);
    await card.locator('details.pick-explanation > summary').click();
    await card.getByText('The model projects', { exact: false }).waitFor();
    await page.close();
    // Stale data (margin differs from the card): the card keeps its published summary, never mismatched numbers.
    const stale = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await stale.route('**/prediction-explanations.json', route => route.fulfill({ contentType: 'application/json',
      body: JSON.stringify({ ...data, games: data.games.map(g => ({ ...g, official: { ...g.official, home_margin: g.official.home_margin + 2 } })) }) }));
    await openPredictions(stale);
    const staleCard = await cardFor(stale, tt);
    await staleCard.locator('details.pick-explanation > summary').click();
    await staleCard.getByText('The model projects', { exact: false }).waitFor();
    assert.equal(await staleCard.locator('.why-prediction').count(), 0);
    await staleCard.getByText('being refreshed with the latest results', { exact: false }).waitFor();
    await stale.close();
    console.log('Missing or stale explanation data falls back to the published summary');
  }
  console.log('Why this prediction acceptance passed');
} finally {
  await browser?.close();
  if (server.pid) { try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; } }
}
