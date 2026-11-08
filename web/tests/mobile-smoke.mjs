import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4178'], { cwd: 'web', stdio: 'ignore', detached: true });
let browser;
try {
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch('http://127.0.0.1:4178/');
      if (response.ok) { ready = true; break; }
    } catch {}
    await delay(500);
  }
  if (!ready) throw new Error('Dashboard development server did not start');
  browser = await chromium.launch({ headless: true });
  await mkdir('web/mobile-evidence', { recursive: true });
  for (const width of [375, 390, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: 1 });
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:4178/', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /College Football Analytics/i }).waitFor();
    await page.getByLabel('Choose dashboard section').waitFor();
    if (await page.getByText('Waiting for live data').count()) throw new Error('Dashboard failed to load season report');
    // Guard the approved four-section mobile homepage against regressions.
    for (const title of ['My Teams', 'Featured Games', 'Upset Watch', 'Games That Matter']) {
      await page.getByRole('heading', { name: title, exact: true }).waitFor();
    }
    if (await page.getByRole('heading', { name: 'Competitive Games', exact: true }).count()) throw new Error('Redundant Competitive Games section returned');
    if (await page.getByText('Prediction model:', { exact: false }).count()) throw new Error('Redundant model notice returned');
    await page.getByText('Our Model Rankings', { exact: false }).first().waitFor();
    await page.screenshot({ path: `web/mobile-evidence/home-${width}.png`, fullPage: true });
    // Exercise favorites persistence without changing the user's actual browser storage.
    await page.evaluate(() => localStorage.removeItem('cfba-favorites-v1'));
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByText('+ Add Team', { exact: true }).first().click();
    const firstTeam = await page.evaluate(async () => {
      const response = await fetch('./season-report.json');
      if (!response.ok || !response.headers.get('content-type')?.includes('json')) throw new Error('Season report JSON not served at ' + response.url);
      return (await response.json()).rankings[0].team;
    });
    await page.getByLabel('Add favorite team').fill(firstTeam);
    await page.getByRole('button', { name: 'Save Team' }).click();
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).waitFor();
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).waitFor();
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).click();
    await page.reload({ waitUntil: 'networkidle' });
    if (await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).count()) throw new Error('Favorite removal did not persist');

    const report = await page.evaluate(async () => { const response = await fetch('./season-report.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; });
    if (!report?.rankings?.length || !report?.predictions?.length) throw new Error('Published report missing usable rankings or predictions');
    for (const section of ['rankings', 'polls', 'predictions', 'conferences', 'cfp', 'schedule', 'matchup', 'programs', 'hype', 'trajectory', 'stock', 'contenders', 'profile']) {
      await page.getByLabel('Choose dashboard section').selectOption(section);
      if (section === 'polls') {
        await page.getByRole('heading', { name: 'Poll Comparison', exact: true }).waitFor();
        const unavailable = await page.getByText('Verified AP and Coaches Poll data is unavailable.', { exact: false }).count();
        if (!unavailable) {
          for (const label of ['Our Model', 'AP', 'Coaches', 'CFP']) {
            const button = page.getByRole('button', { name: `Sort by ${label} ranking` });
            await button.click();
            if (await button.getAttribute('aria-pressed') !== 'true') throw new Error(`Poll sort did not select ${label}`);
            const key = { 'Our Model': 1, AP: 2, Coaches: 3, CFP: 4 }[label];
            const values = await page.locator('section.notice table tbody tr').evaluateAll((rows, index) => rows.map(row => row.querySelectorAll('td')[index]?.textContent?.trim() || '—'), key);
            const ranked = values.filter(value => /^\\d+$/.test(value)).map(Number);
            if (ranked.some((rank, i) => i > 0 && rank < ranked[i - 1])) throw new Error(`${label} poll is not sorted numerically`);
            if (values.length > 30) throw new Error('Poll comparison exceeded 30 rows');
          }
        }
      }
      if (section === 'predictions') await page.getByRole('heading', { name: 'Game Predictions' }).waitFor();
      const v4Headings = { programs: 'Historical Program Rankings', hype: 'Historical Hype Index', trajectory: 'Program Trajectory & Momentum', stock: 'Team Stock Watch', contenders: 'Contenders & Pretenders', profile: 'Team Profile' };
      if (v4Headings[section]) await page.getByRole('heading', { name: v4Headings[section], exact: true }).waitFor();
      if (section === 'hype') {
        await page.getByText('Expectations vs. reality:', { exact: false }).waitFor();
        await page.getByText('Historical AP and Coaches evidence is kept separate', { exact: false }).waitFor();
      }
      if (section === 'trajectory') {
        await page.getByText('Program development:', { exact: false }).waitFor();
        await page.getByText('Poll popularity does not determine trajectory.', { exact: false }).waitFor();
      }
      if (section === 'stock' || section === 'contenders') {
        // These views must remain usable without publishing unsupported metrics.
        const unavailable = section === 'stock'
          ? 'Verified stock movement is unavailable.'
          : 'Independent contender classifications are unavailable.';
        await page.getByText(unavailable, { exact: false }).waitFor();
        await page.getByLabel('Find a team profile').fill(firstTeam);
        const teamRow = page.getByRole('row').filter({ hasText: firstTeam }).first();
        await teamRow.getByRole('button', { name: 'View Team Profile' }).click();
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        if (await page.getByLabel('Choose school').inputValue() !== firstTeam) {
          throw new Error(`Discovery did not preserve the selected team in ${section}`);
        }
        await page.getByLabel('Choose dashboard section').selectOption(section);
      }
      if (section === 'profile') {
        await page.getByLabel('Choose school').selectOption(firstTeam);
        await page.locator('small').getByText('Contenders & Pretenders', { exact: true }).waitFor();
        await page.locator('small').getByText('Team Stock Watch', { exact: true }).waitFor();
        for (const heading of ['Head Coach & Coordinators', 'Roster Continuity & Transfers', 'Opponent-Specific Matchup Factors']) {
          await page.getByText(heading, { exact: true }).waitFor();
        }
        await page.getByText('Full Season Schedule and Model Outlook').waitFor();
      }
      if (['programs', 'hype', 'trajectory'].includes(section)) {
        // The optional historical asset is deliberately not published without
        // verified source coverage. Check its absence is explicit and safe.
        const historicalResponse = await page.evaluate(async () => {
          const response = await fetch('./v4-program-intelligence.json', { cache: 'no-store' });
          const contentType = response.headers.get('content-type') || '';
          if (!response.ok || !contentType.includes('json')) return 'unavailable';
          const payload = await response.json();
          return payload.schema_version === 1 && payload.status === 'descriptive_only'
            && payload.source_review_attested === true && payload.predictive_validation === false
            && Array.isArray(payload.programs) ? 'published' : 'invalid';
        });
        if (historicalResponse === 'invalid') throw new Error('Historical research asset failed provenance schema gate');
        if (historicalResponse === 'unavailable') {
          await page.getByText('No rankings are estimated from missing data.', { exact: false }).waitFor();
        }
        if (historicalResponse === 'published') {
          await page.getByText('Descriptive research only', { exact: false }).first().waitFor();
          const link = page.getByRole('button', { name: firstTeam, exact: true }).first();
          if (await link.count()) {
            await link.click();
            await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
            await page.getByLabel('Choose dashboard section').selectOption(section);
          }
        }

      }
      if (section === 'cfp') {
        await page.getByRole('heading', { name: 'Projected 12-Team CFP Field' }).waitFor();
        await page.getByRole('heading', { name: 'Our Top 25 vs. Official CFP Top 25' }).waitFor();
        await page.getByRole('heading', { name: 'Playoff Bubble' }).waitFor();
        const poll = await page.evaluate(async () => { try { const response = await fetch('./poll-snapshot.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; } catch { return null; } });
        if (!poll?.cfp_published_at || !poll?.cfp_top25?.length) {
          await page.getByText('A verified, publication-dated official CFP Top 25 is not available', { exact: false }).waitFor();
        }
      }
      if (section === 'schedule') {
        await page.getByRole('heading', { name: 'School Season Schedule' }).waitFor();
        await page.getByLabel('School Schedule').waitFor();
      }
      if (section === 'matchup') {
        await page.getByRole('heading', { name: 'Hypothetical Matchup' }).waitFor();
        await page.getByLabel('First school').waitFor();
        await page.getByLabel('Second school').waitFor();
      }
      if (await page.getByLabel('Choose dashboard section').inputValue() !== section) {
        throw new Error(`Navigation failed for ${section} at ${width}px`);
      }
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
      if (horizontalOverflow) throw new Error(`Page-wide horizontal overflow in ${section} at ${width}px`);
      if (['rankings', 'predictions', 'cfp', 'profile', 'stock', 'contenders', 'programs', 'hype', 'trajectory'].includes(section)) {
        await page.screenshot({ path: `web/mobile-evidence/${section}-${width}.png`, fullPage: true });
      }
      if (errors.length) throw new Error(`Browser error in ${section}: ${errors.join('; ')}`);
    }
    console.log(`Browser navigation smoke passed at ${width}px`);
    await page.close();
    const failedPage = await browser.newPage({ viewport: { width, height: 844 } });
    await failedPage.route('**/season-report.json', route => route.fulfill({ status: 503, body: 'Unavailable' }));
    await failedPage.goto('http://127.0.0.1:4178/');
    await failedPage.getByText('Waiting for live data').waitFor();
    await failedPage.close();
  }
} finally {
  await browser?.close();
  // npm launches Vite as a child; terminate the entire process group so
  // inherited handles cannot keep the GitHub Actions job alive.
  if (server.pid) {
    try { process.kill(-server.pid, 'SIGTERM'); } catch (error) {
      if (error.code !== 'ESRCH') throw error;
    }
  }
}
