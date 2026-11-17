// Browser acceptance: shared school search (combobox) on Team Profile, Compare, Market hand-off and Favorites at five widths.
// Covers typing, ranking, touch and keyboard selection, ARIA semantics, empty/no-match states, clipping, overflow, persistence.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';
import { startAsDeclinedVisitor } from './consent-prompt.mjs';
import { chooseSection, openDestination } from './section-navigation.mjs';

const PORT = 4192, base = `http://127.0.0.1:${PORT}/`;
const evidence = 'docs/evidence/school-search';
await mkdir(evidence, { recursive: true });

const field = (page, label) => page.getByLabel(label, { exact: true }).locator('visible=true').first();
const listFor = async (page, input) => page.locator(`[id="${await input.getAttribute('aria-controls')}"]`);
const status = async input => (await input.page().locator(`[id="${await input.getAttribute('aria-describedby')}"]`).innerText()).replace(/\s+/g, ' ').trim();

// Every option is on screen, not under the fixed bottom navigation, and is the top element at its centre (not clipped/covered).
async function assertListVisible(page, list, where) {
  const problems = await list.evaluate(ul => {
    const nav = document.querySelector('.editorial-navigation');
    const limit = nav && getComputedStyle(nav).position === 'fixed' ? nav.getBoundingClientRect().top : window.innerHeight;
    return [...ul.querySelectorAll('[role=option]')].flatMap(li => {
      const r = li.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
      const issues = [];
      if (r.top < 0 || r.bottom > limit + 0.5 || r.left < 0 || r.right > window.innerWidth + 0.5) issues.push(`${li.textContent} outside visible area (${Math.round(r.top)}–${Math.round(r.bottom)}, limit ${Math.round(limit)})`);
      else if (!li.contains(document.elementFromPoint(x, y))) issues.push(`${li.textContent} covered`);
      if (r.height < 44) issues.push(`${li.textContent} target ${r.height}px`);
      return issues;
    });
  });
  assert.deepEqual(problems, [], `${where}: ${problems.join('; ')}`);
}

async function assertNoOverflow(page, where) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 1, `horizontal overflow ${overflow}px (${where})`);
}

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(PORT), '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(base)).ok) break; } catch {} await delay(500); }
  browser = startAsDeclinedVisitor(await chromium.launch());
  for (const width of [375, 390, 430, 768, 1536]) {
    const phone = width < 600;
    const context = await browser.newContext({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: width === 390 || width === 1536 ? 2 : 1, hasTouch: width <= 768, isMobile: phone });
    const page = await context.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    const pick = async option => (width <= 768 ? option.tap() : option.click());
    await page.goto(base, { waitUntil: 'networkidle' });
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Team Profiles');

    // Team Profile: prominent search, placeholder, combobox semantics, empty state.
    const school = field(page, 'Choose school');
    assert.equal(await school.getAttribute('role'), 'combobox');
    assert.equal(await school.getAttribute('aria-autocomplete'), 'list');
    assert.ok((await school.boundingBox()).height >= 44, 'touch-sized input');
    const initial = await school.inputValue();
    assert.ok(initial, 'Team Profile opens with a school selected');
    assert.equal(await status(school), `Selected: ${initial}`);
    await school.focus();
    assert.equal(await school.inputValue(), '', 'focus clears the query so typing starts fresh');
    assert.equal(await school.getAttribute('placeholder'), 'Search for a school...');
    assert.equal(await school.getAttribute('aria-expanded'), 'false');
    assert.equal(await status(school), `Current: ${initial} · type a school name or abbreviation, like TTU`);

    // "Tex" → Texas Tech, picked by touch (phones/tablet) or mouse (desktop).
    await school.pressSequentially('Tex');
    const list = await listFor(page, school);
    await list.waitFor();
    assert.equal(await list.getAttribute('role'), 'listbox');
    assert.equal(await school.getAttribute('aria-expanded'), 'true');
    const names = await list.getByRole('option').allInnerTexts();
    assert.ok(names.includes('Texas Tech') && names.length <= 8, names.join(','));
    assert.ok(names.indexOf('Texas Tech') < names.indexOf('North Texas'), 'prefix matches rank first');
    assert.equal(await school.getAttribute('aria-activedescendant'), await list.getByRole('option').first().getAttribute('id'));
    assert.match(await status(school), new RegExp(`^Current: ${initial} · ${names.length} found$`));
    const statusBox = async () => (await page.locator(`[id="${await school.getAttribute('aria-describedby')}"]`).boundingBox()).height;
    const editingHeight = await statusBox();
    await assertListVisible(page, list, `Team Profile at ${width}`);
    await assertNoOverflow(page, `suggestions at ${width}`);
    if (width === 390 || width === 1536) await page.screenshot({ path: `${evidence}/profile-suggestions-${width}.png` });
    await pick(list.getByRole('option', { name: 'Texas Tech', exact: true }));
    assert.equal(await school.inputValue(), 'Texas Tech');
    assert.equal(await status(school), 'Selected: Texas Tech');
    assert.equal(await statusBox(), editingHeight, 'status keeps one constant line, so controls below never move mid-click');
    assert.equal(await list.count(), 0, 'list closes after a choice');
    await page.getByRole('region', { name: 'Strength breakdown', exact: true }).waitFor();
    assert.match(await page.locator('.team-profile').innerText(), /Texas Tech/);
    if (width === 390 || width === 1536) await page.screenshot({ path: `${evidence}/profile-selected-${width}.png` });

    // Narrow phones: "Compare this school" sits beneath the search, full search width available.
    const compareButton = page.getByRole('button', { name: 'Compare this school', exact: true });
    const searchBox = await page.locator('.team-profile .profile-tools .school-search').boundingBox(), buttonBox = await compareButton.boundingBox();
    if (phone) assert.ok(buttonBox.y >= searchBox.y + searchBox.height - 1, 'Compare button below search on phones');
    else assert.ok(Math.abs(buttonBox.y - searchBox.y) < searchBox.height, 'Compare button beside search on wider screens');

    // Keyboard only: TCU via Enter, LSU via arrows, no match + Escape keeps the selection.
    await school.focus(); await page.keyboard.type('tcu'); await page.keyboard.press('Enter');
    assert.equal(await school.inputValue(), 'TCU');
    await school.focus(); await page.keyboard.type('LSU');
    await page.keyboard.press('ArrowDown'); await page.keyboard.press('ArrowUp');
    assert.equal(await list.getByRole('option', { selected: true }).innerText(), 'LSU');
    await page.keyboard.press('Enter');
    assert.equal(await school.inputValue(), 'LSU');
    await school.focus(); await page.keyboard.type('zzqx');
    assert.equal(await status(school), 'Current: LSU · no match for “zzqx”');
    assert.equal(await school.getAttribute('aria-expanded'), 'false');
    await page.keyboard.press('Escape');
    assert.equal(await school.inputValue(), 'LSU', 'Escape keeps the selected school');
    await school.focus(); await page.keyboard.type('TTU');
    assert.equal(await list.getByRole('option').first().innerText(), 'Texas Tech', 'TTU abbreviation');
    await page.keyboard.press('Escape');
    assert.equal(await school.inputValue(), 'LSU');

    // Selection survives navigation away and back.
    await openDestination(page, 'Home');
    await openDestination(page, 'Teams');
    await chooseSection(page, 'Teams sections', 'Team Profiles');
    assert.equal(await field(page, 'Choose school').inputValue(), 'LSU', 'selection preserved across navigation');

    // Compare: choose and change both schools; hand the matchup to Market Analysis.
    await compareButton.click();
    await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
    const first = field(page, 'First school'), second = field(page, 'Second school');
    assert.equal(await first.inputValue(), 'LSU', 'Compare this school carries the school over');
    await first.focus(); await page.keyboard.type('TTU'); await page.keyboard.press('Enter');
    await second.focus(); await second.pressSequentially('LS');
    const secondList = await listFor(page, second);
    await assertListVisible(page, secondList, `Compare at ${width}`);
    await pick(secondList.getByRole('option', { name: 'LSU', exact: true }));
    let result = await page.locator('.matchup-result').innerText();
    assert.ok(result.includes('Texas Tech') && result.includes('LSU'), result);
    await second.focus(); await second.pressSequentially('TC');
    await pick((await listFor(page, second)).getByRole('option', { name: 'TCU', exact: true }));
    result = await page.locator('.matchup-result').innerText();
    assert.ok(result.includes('Texas Tech') && result.includes('TCU') && !result.includes('LSU'), result);
    await assertNoOverflow(page, `Compare at ${width}`);
    if (width === 390) await page.locator('.matchup-inputs').screenshot({ path: `${evidence}/compare-selected-390.png` });
    await page.getByRole('button', { name: 'Compare this matchup with a market line in Market Analysis' }).click();
    await page.getByRole('heading', { name: 'Market Analysis', exact: true, level: 2 }).waitFor();
    const selectedGame = await page.locator('.market-selected-game').innerText();
    assert.ok(selectedGame.includes('Texas Tech') && selectedGame.includes('TCU'), selectedGame);
    await page.goBack();
    assert.equal(await field(page, 'Second school').inputValue(), 'TCU', 'Back keeps the Compare selection');

    // Favorites: find with the same search (abbreviation + touch), save, survive reload, remove.
    await openDestination(page, 'Home');
    await page.evaluate(() => localStorage.removeItem('cfba-favorites-v1'));
    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('.editorial-favorite-editor > summary').click();
    await page.getByText('+ Add Team', { exact: true }).first().click();
    const fav = field(page, 'Add favorite team');
    await fav.focus(); await fav.pressSequentially('TTU');
    const favList = await listFor(page, fav);
    await assertListVisible(page, favList, `Favorites at ${width}`);
    await pick(favList.getByRole('option', { name: 'Texas Tech', exact: true }));
    await page.getByRole('button', { name: 'Save Team' }).click();
    await page.getByRole('button', { name: 'Remove Texas Tech from favorites' }).waitFor();
    await page.reload({ waitUntil: 'networkidle' });
    assert.ok((await page.evaluate(() => localStorage.getItem('cfba-favorites-v1'))).includes('Texas Tech'), 'favorite persisted');
    await page.locator('.editorial-favorite-editor > summary').click();
    await page.getByRole('button', { name: 'Remove Texas Tech from favorites' }).click();
    await page.reload({ waitUntil: 'networkidle' });
    assert.equal(await page.getByRole('button', { name: 'Remove Texas Tech from favorites' }).count(), 0);
    await assertNoOverflow(page, `Home at ${width}`);

    assert.deepEqual(errors, [], `page errors at ${width}`);
    await context.close();
    console.log(`School search passed at ${width}px`);
  }
  console.log('School search acceptance passed');
} finally {
  await browser?.close();
  try { process.kill(-server.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}
