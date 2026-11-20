// Browser acceptance: dual model projections (Compare / Standard / Momentum) at five widths with real published data.
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection, assertSection, assertNavigationFits, openDestination, chooseSchool } from './section-navigation.mjs';

const PORT = 4206, base = process.env.BASE || `http://127.0.0.1:${PORT}/`;
const evidence = process.env.EVIDENCE || 'docs/evidence/dual-projections';
await mkdir(evidence, { recursive: true });
const data = JSON.parse(await readFile(process.env.DATA || 'web/public/dual-projections.json', 'utf8'));
const firstWeek = Math.min(...data.games.map(g => g.week));
const TEAM = 'Texas Tech';
const ttGames = data.games.filter(g => g.home === TEAM || g.away === TEAM);

async function contrast(page) {
  return page.locator('.model-projections').evaluate(root => {
    const rgb = c => (c.match(/[\d.]+/g) || []).map(Number);
    const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const bg = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length === 3 || (c.length === 4 && c[3] > 0.9)) return c.slice(0, 3); } return [11, 22, 38]; };
    return [...root.querySelectorAll('*')].filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getClientRects().length)
      .map(e => { const a = lum(rgb(getComputedStyle(e).color).slice(0, 3)), b = lum(bg(e)); return { text: e.textContent.trim().slice(0, 30), ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) }; })
      .filter(x => x.ratio < 4.5);
  });
}

const server = process.env.BASE ? { pid: 0 } : spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  if (!process.env.BASE) for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  for (const width of [375, 390, 430, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: width === 390 || width === 1536 ? 2 : 1 });
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(base, { waitUntil: 'networkidle' });
    // One canonical section in the Teams menu (phone dropdown / desktop tabs), still linked from Game Predictions.
    await openDestination(page, 'Home');
    const homeSections = page.getByRole('combobox', { name: 'Home sections', exact: true });
    const homeLabels = await homeSections.isVisible() ? await homeSections.locator('option').allTextContents()
      : await page.getByRole('tablist', { name: 'Home sections', exact: true }).getByRole('tab').allTextContents();
    assert.ok(!homeLabels.includes('Model Projections'), `Home sections still list Model Projections: ${homeLabels}`);
    await page.getByRole('button', { name: 'All games', exact: false }).click();
    await page.getByRole('button', { name: 'Compare the Standard and Momentum projections' }).click();
    const mp = page.locator('.model-projections');
    await mp.getByRole('heading', { name: 'Model Projections', level: 2 }).waitFor();
    assert.ok(page.url().endsWith('#/projections'));
    await assertSection(page, 'Teams sections', 'Model Projections');
    const dropdown = await assertNavigationFits(page, 'Teams sections', width);   // must be a fitting dropdown on phones
    if (width === 1536) assert.equal(dropdown, false, 'desktop shows Teams tabs');
    await chooseSection(page, 'Teams sections', 'Offense & Defense');
    await chooseSection(page, 'Teams sections', 'Model Projections');
    await mp.getByRole('heading', { name: 'Model Projections', level: 2 }).waitFor();
    // The existing direct link opens the same page with data loaded.
    await page.goto(base + '#/projections', { waitUntil: 'networkidle' });
    await mp.locator('.mp-game').first().waitFor();
    await assertSection(page, 'Teams sections', 'Model Projections');
    // Compare (default): next week's games, both models side by side, with an explanation and the official forecast.
    assert.ok(await mp.getByRole('radio', { name: 'Compare' }).isChecked());
    assert.equal(await page.getByLabel('Week', { exact: true }).inputValue(), String(firstWeek));
    const cards = mp.locator('.mp-game');
    const weekGames = data.games.filter(g => g.week === firstWeek);
    assert.equal(await cards.count(), Math.min(12, weekGames.length));
    const first = weekGames[0];
    const text = (await cards.first().innerText()).replace(/\s+/g, ' ');
    assert.ok(text.includes(`${first.away} ${first.neutral_site ? 'vs' : 'at'} ${first.home}`), text);
    assert.ok(/STANDARD/i.test(text) && /MOMENTUM/i.test(text), text);
    const pStd = Math.round(100 * Math.max(first.standard.home_win_probability, 1 - first.standard.home_win_probability));
    assert.ok(text.includes(`${pStd}%`), text);
    // One short explanation sentence; the calculation sits behind a keyboard-operable expander.
    const why = (await cards.first().locator('.mp-why').innerText()).trim();
    assert.ok(/^(The models agree to within a point\.|Momentum favors .+ by \d+\.\d additional points)/.test(why) && why.length <= 160, why);
    const calc = cards.first().locator('details.mp-calc');
    assert.ok(!(await calc.evaluate(d => d.open)));
    await calc.locator('summary').focus(); await page.keyboard.press('Enter');
    assert.match(await calc.innerText(), /Standard margin: .+ Momentum margin: /);
    await calc.locator('summary').click();
    if (first.official) assert.match(text, /Official forecast:/);
    // Standard and Momentum views show one projection per card (keyboard switch).
    await mp.getByRole('radio', { name: 'Compare' }).focus();
    await page.keyboard.press('ArrowRight');
    assert.ok(await mp.getByRole('radio', { name: 'Standard' }).isChecked());
    assert.equal(await cards.first().locator('.mp-model').count(), 1);
    assert.equal(await cards.first().locator('.mp-why').count(), 0);
    await page.keyboard.press('ArrowRight');
    assert.ok(await mp.getByRole('radio', { name: 'Momentum' }).isChecked());
    const momText = (await cards.first().innerText()).replace(/\s+/g, ' ');
    const pMom = Math.round(100 * Math.max(first.momentum.home_win_probability, 1 - first.momentum.home_win_probability));
    assert.ok(/MOMENTUM/i.test(momText) && momText.includes(`${pMom}%`), momText);
    await mp.locator('.mp-views label', { hasText: 'Compare' }).click();   // a tap on the visible option
    assert.ok(await mp.getByRole('radio', { name: 'Compare' }).isChecked());
    // Team search: every remaining Texas Tech game across weeks, and its projected record in both models.
    await chooseSchool(page, 'Find a team', TEAM);
    assert.equal(await cards.count(), ttGames.length);
    // Records: mobile shows a team heading and one separated block per model; desktop keeps the table.
    const mobile = width < 768;
    assert.equal(await mp.locator('.mp-team-cards').isVisible(), mobile);
    assert.equal(await mp.locator('.mp-records').isVisible(), !mobile);
    const record = mobile ? mp.locator('.mp-team-card').first() : mp.locator('.mp-records tbody tr').first();
    const rowText = (await record.innerText()).replace(/\s+/g, ' ');
    const t = data.teams[TEAM];
    const exp = k => `${t[k].expected_wins.toFixed(1)}–${t[k].expected_losses.toFixed(1)}`;
    assert.ok(rowText.includes(exp('standard')) && rowText.includes(exp('momentum')), rowText);
    if (mobile) {
      assert.equal(await record.locator('h4').innerText(), TEAM);
      const blocks = record.locator('.mp-team-model');
      assert.equal(await blocks.count(), 2);
      for (const [i, k] of [[0, 'standard'], [1, 'momentum']]) {
        const b = (await blocks.nth(i).innerText()).replace(/\s+/g, ' ');
        assert.ok(b.includes(exp(k)) && b.includes(`CFP ${Math.round(100 * t[k].cfp_field)}%`) && b.includes(`Conference title ${Math.round(100 * t[k].conference_title)}%`) && /Most likely \d+–\d+/.test(b), b);
      }
    } else assert.ok(rowText.includes(`CFP ${Math.round(100 * t.standard.cfp_field)}%`) && rowText.includes(`CFP ${Math.round(100 * t.momentum.cfp_field)}%`), rowText);
    // Large playoff-odds gaps caused by a tiebreak swap are explained in plain language.
    for (const sw of t.tiebreak_swaps || []) assert.ok(rowText.includes(sw.rival) && /tied conference records go to the higher-rated team/.test(rowText), rowText);
    // The view selection drives games and records alike (Standard only, then back to Compare).
    await mp.locator('.mp-views label', { hasText: 'Standard' }).click();
    const stdText = (await record.innerText()).replace(/\s+/g, ' ');
    assert.ok(stdText.includes(exp('standard')) && !stdText.includes(exp('momentum')) && !/higher-rated team/.test(stdText), stdText);
    assert.equal(await cards.first().locator('.mp-model').count(), 1);
    await mp.locator('.mp-views label', { hasText: 'Compare' }).click();
    if (width === 390 || width === 1536) {
      await mp.locator('#mp-games-title').evaluate(e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 60));
      await page.screenshot({ path: `${evidence}/compare-${width}.png` });
      await mp.locator('#mp-records-title').evaluate(e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 60));
      await page.screenshot({ path: `${evidence}/records-${width}.png` });
    }
    await mp.getByRole('button', { name: 'Show every team' }).click();
    assert.equal(await (mobile ? mp.locator('.mp-team-card') : mp.locator('.mp-records tbody tr')).count(), 25);
    // Methodology and validation behind a keyboard-operable expander.
    const info = mp.locator('details.mp-more-info');
    await info.locator('summary').focus(); await page.keyboard.press('Enter');
    const infoText = await info.innerText();
    assert.ok(/Brier score: lower is better/.test(infoText) && /not archived forecasts/.test(infoText) && /published before kickoff/.test(infoText), infoText);
    // Layout and accessibility.
    const overflow = await page.evaluate(() => ({ page: document.documentElement.scrollWidth - innerWidth,
      tables: [...document.querySelectorAll('.model-projections .table-wrap')].map(e => e.scrollWidth - e.clientWidth).filter(v => v > 1) }));
    assert.ok(overflow.page <= 1 && overflow.tables.length === 0, `overflow at ${width}: ${JSON.stringify(overflow)}`);
    assert.deepEqual(await contrast(page), [], `contrast at ${width}`);
    if (width < 768) {
      await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await delay(300);
      const gap = await page.evaluate(() => document.querySelector('.editorial-navigation').getBoundingClientRect().top - document.querySelector('.model-projections').getBoundingClientRect().bottom);
      assert.ok(gap >= 0, `bottom navigation covers content at ${width}`);
    }
    assert.deepEqual(errors, [], `page errors at ${width}`);
    await page.close();
    console.log(`Model projections passed at ${width}px`);
  }
  if (!process.env.BASE) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.route('**/dual-projections.json', route => route.fulfill({ status: 404, body: 'missing' }));
    await page.goto(base + '#/projections', { waitUntil: 'networkidle' });
    await page.getByText('Model projections are not available right now.', { exact: false }).waitFor();
    await page.close();
  }
  console.log('Model projections acceptance passed');
} finally {
  await browser?.close();
  if (server.pid) { try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; } }
}
