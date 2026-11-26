// Browser acceptance: the Bowls and College Football Playoff section on Game Predictions (five widths + Android).
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium, devices } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { openDestination } from './section-navigation.mjs';

const PORT = 4210, base = `http://127.0.0.1:${PORT}/`;
const DATA = { season: 2026, retrieved_at: '2026-12-20T03:00:00Z', games: [
  { game_id: 2, home: 'Texas Tech', away: 'Utah', neutral_site: false, start_date: '2026-12-20T01:00:00Z', label: 'CFP First Round', completed: true, home_score: 31, away_score: 24 },
  { game_id: 1, home: 'Georgia', away: 'Miami (FL)', neutral_site: true, start_date: '2027-01-01T21:00:00Z', label: 'Rose Bowl - CFP Quarterfinal', completed: false, home_score: null, away_score: null,
    prediction: { home_margin: 2.5, home_win_probability: 0.5797, predicted_winner: 'Georgia' } },
  { game_id: 3, home: 'Army', away: 'Some FCS U', neutral_site: true, start_date: '2026-12-27T20:00:00Z', label: 'Independence Bowl', completed: false, home_score: null, away_score: null } ] };

async function open(page) {
  await page.goto(base, { waitUntil: 'networkidle' });
  await openDestination(page, 'Home');
  await page.getByRole('button', { name: 'All Games', exact: false }).click();
  await page.getByRole('heading', { name: 'Game Predictions', level: 2 }).waitFor();
}

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  const contexts = [375, 390, 430, 768, 1536].map(w => ({ label: `${w}px`, options: { viewport: { width: w, height: 844 } } }));
  contexts.push({ label: 'Android Pixel 7', options: { ...devices['Pixel 7'] } });
  for (const { label, options } of contexts) {
    const ctx = await browser.newContext(options), page = await ctx.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.route('**/postseason-2026.json', r => r.fulfill({ contentType: 'application/json', body: JSON.stringify(DATA) }));
    await open(page);
    const section = page.getByRole('region', { name: 'Bowls and College Football Playoff' });
    await section.waitFor();
    const text = (await section.innerText()).replace(/\s+/g, ' ');
    assert.match(text, /ROSE BOWL - CFP QUARTERFINAL/); assert.match(text, /Model Pick Georgia/); assert.match(text, /Win Probability 58%/);
    assert.match(text, /CFP FIRST ROUND · FINAL/); assert.match(text, /Utah 24 @ Texas Tech 31/);
    assert.match(text, /No model pick: one team is outside the rated FBS field/);
    assert.match(text, /do not change the ratings/);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth) <= 1, `overflow at ${label}`);
    assert.ok(await page.locator('.prediction-card').count() > 3, 'regular-season predictions still listed');
    assert.deepEqual(errors, []);
    await ctx.close();
    console.log(`Postseason section passed at ${label}`);
  }
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.route('**/postseason-2026.json', r => r.fulfill({ status: 404, body: 'none' }));
  await open(page);
  assert.equal(await page.getByRole('region', { name: 'Bowls and College Football Playoff' }).count(), 0);
  console.log('No postseason games: section hidden; postseason acceptance passed');
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch {}
}
