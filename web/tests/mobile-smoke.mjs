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
    // V5 public onboarding and privacy disclosure must be available at every viewport.
    const about = page.getByLabel('About, privacy and getting started');
    await about.locator('summary').click();
    await about.getByText('Favorites are stored only in this browser', { exact: false }).waitFor();
    await about.getByText('No account or cross-device synchronization', { exact: false }).waitFor();
    const feedback = about.getByRole('link', { name: 'the project issue form' });
    if (!(await feedback.getAttribute('href'))?.endsWith('/issues/new')) throw new Error('Public feedback destination missing');
    await about.locator('summary').click();

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
    // A separate browser profile must not inherit another user's local favorites.
    const isolatedContext = await browser.newContext({ viewport: { width, height: 844 } });
    try {
      const isolatedPage = await isolatedContext.newPage();
      await isolatedPage.goto('http://127.0.0.1:4178/', { waitUntil: 'networkidle' });
      await isolatedPage.getByRole('heading', { name: 'My Teams' }).waitFor();
      if (await isolatedPage.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).count()) {
        throw new Error('Favorite leaked into a separate browser profile');
      }
      const isolatedFavorites = await isolatedPage.evaluate(() => JSON.parse(localStorage.getItem('cfba-favorites-v1') || '[]'));
      if (isolatedFavorites.some(Boolean)) throw new Error('New browser profile inherited favorites');
    } finally {
      await isolatedContext.close();
    }
    // A saved school must open its complete Team Profile, not just its schedule.
    await page.getByRole('button', { name: 'Team profile' }).first().click();
    await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
    if (await page.getByLabel('Choose school').inputValue() !== firstTeam) throw new Error('Favorite-to-profile navigation lost the selected team');
    await page.getByLabel('Choose dashboard section').selectOption('home');
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).waitFor();
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).click();
    await page.reload({ waitUntil: 'networkidle' });
    if (await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).count()) throw new Error('Favorite removal did not persist');

    const report = await page.evaluate(async () => { const response = await fetch('./season-report.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; });
    if (!report?.rankings?.length || !report?.predictions?.length) throw new Error('Published report missing usable rankings or predictions');
    for (const section of ['rankings', 'polls', 'predictions', 'conferences', 'cfp', 'schedule', 'matchup', 'compare', 'programs', 'profile']) {
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
            const ranked = values.filter(value => /^\d+$/.test(value)).map(Number);
            if (ranked.some((rank, i) => i > 0 && rank < ranked[i - 1])) throw new Error(`${label} poll is not sorted numerically`);
            if (values.length > 30) throw new Error('Poll comparison exceeded 30 rows');
          }
        }
      }
      if (section === 'predictions') {
        await page.getByRole('heading', { name: 'Game Predictions' }).waitFor();
        const firstPrediction = report.predictions[0];
        await page.getByRole('button', { name: 'Compare teams' }).first().click();
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        if (await page.getByLabel('First school').inputValue() !== firstPrediction.home || await page.getByLabel('Second school').inputValue() !== firstPrediction.away) {
          throw new Error('Prediction-to-Compare did not preserve both schools');
        }
        await page.getByRole('region', { name: 'Side-by-side team comparison' }).waitFor();
        await page.getByLabel('Choose dashboard section').selectOption('predictions');
      }
      if (['programs', 'hype', 'trajectory', 'stock', 'contenders'].includes(section)) {
        await page.getByRole('heading', { name: 'Program Intelligence', exact: true }).waitFor();
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Last 5' }).waitFor({ state: 'attached' });
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Vs forecast' }).waitFor({ state: 'attached' });
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Top 25 wins' }).waitFor({ state: 'attached' });
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Rating' }).waitFor({ state: 'attached' });
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Conf. record' }).waitFor({ state: 'attached' });
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Season trend' }).waitFor({ state: 'attached' });
        await page.locator('.program-intelligence-table th').filter({ hasText: 'Coaches Poll' }).waitFor({ state: 'attached' });
        if (await page.locator('.program-intelligence-table tbody tr:first-child td').count() !== await page.locator('.program-intelligence-table thead th').count()) {
          throw new Error('Program Intelligence comparison columns are out of sync with mobile cards');
        }
        if (await page.getByText('Verified historical program development').count()) {
          await page.getByText('Verified historical program development').click();
          await page.getByLabel('Choose historical program').waitFor();
        }
        const rows = page.locator('.program-intelligence-table tbody tr');
        if (await rows.count() === 0) throw new Error('Program Intelligence has no current-season comparisons');
        if (await rows.count() > 10) throw new Error('Initial Program Intelligence view exceeds ten teams');
        const firstRow = await rows.first().innerText();
        if (/Too Early to Tell|Insufficient verified snapshots/.test(firstRow)) throw new Error('Legacy placeholders returned');
        if (width <= 390) {
          const fits = await page.locator('.program-intelligence-table').evaluate(el => {
            const rect = el.getBoundingClientRect();
            return rect.left >= -1 && rect.right <= document.documentElement.clientWidth + 1;
          });
          if (!fits) throw new Error('Program Intelligence table exceeds mobile viewport');
        }
        await page.getByLabel('Sort program intelligence').selectOption('recent');
        await page.getByLabel('Sort program intelligence').selectOption('rank');
        await page.getByLabel('Filter programs by conference').selectOption('all');
        await page.getByLabel('Find a program').fill(firstTeam);
        const row = page.getByRole('row').filter({ hasText: firstTeam }).first();
        const overviewTrend = (await row.locator('td').nth(7).textContent() || '').trim();
        await row.getByRole('button', { name: `Compare ${firstTeam} with another school` }).click();
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        if (await page.getByLabel('First school').inputValue() !== firstTeam) throw new Error('Program-to-comparison navigation lost the selected team');
        await page.getByLabel('Choose dashboard section').selectOption('programs');
        await page.getByLabel('Find a program').fill(firstTeam);
        await page.getByRole('row').filter({ hasText: firstTeam }).first().getByRole('button', { name: 'View team' }).click();
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        const profileTrend = page.locator('.team-profile-tile').filter({ hasText: 'Current-Season Form Trend' });
        await profileTrend.waitFor();
        const profileTrendValue = (await profileTrend.locator('strong').textContent() || '').trim();
        if (profileTrendValue !== (overviewTrend === '—' ? 'Requires 8 scored games' : overviewTrend)) {
          throw new Error(`Team Profile and Program Intelligence disagree on current-season form trend for ${firstTeam}: overview=${JSON.stringify(overviewTrend)}, profile=${JSON.stringify(profileTrendValue)}`);
        }
        if (await page.getByLabel('Choose school').inputValue() !== firstTeam) {
          throw new Error(`Program Intelligence did not preserve selected team for ${section}`);
        }
        await page.getByLabel('Choose dashboard section').selectOption(section);
      }
      if (section === 'profile') {
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        await page.getByLabel('Choose school').selectOption(firstTeam);
        await page.getByText('Full Season Schedule and Model Outlook').waitFor();
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
      if (section === 'compare') {
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        const secondTeam = report.rankings.find(team => team.team !== firstTeam)?.team;
        if (!secondTeam) throw new Error('Need two distinct teams for comparison');
        await page.getByLabel('First school').selectOption(firstTeam);
        await page.getByLabel('Second school').selectOption(secondTeam);
        const comparison = page.getByRole('region', { name: 'Side-by-side team comparison' });
        await comparison.getByRole('heading', { name: 'Side-by-side team comparison' }).waitFor();
        await comparison.getByRole('columnheader', { name: firstTeam }).waitFor();
        await comparison.getByRole('columnheader', { name: secondTeam }).waitFor();
        await comparison.getByRole('button', { name: `View ${firstTeam} profile` }).click();
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        if (await page.getByLabel('Choose school').inputValue() !== firstTeam) throw new Error('Compare-to-profile navigation lost team selection');
        await page.getByLabel('Choose dashboard section').selectOption('compare');
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
    // A correctly dated official CFP snapshot must render, rather than being
    // discarded by the poll-date format gate. This fixture is browser-test-only.
    if (width === 390) {
      const pollPage = await browser.newPage({ viewport: { width, height: 844 } });
      const topTeam = report.rankings[0].team;
      await pollPage.route('**/poll-snapshot.json', route => route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ season: report.season, week: 10,
          source: 'Browser test fixture — not published research',
          ap_top25: [{ team: topTeam, rank: 1 }],
          coaches_top25: [{ team: topTeam, rank: 1 }],
          cfp_top25: [{ team: topTeam, rank: 1 }],
          cfp_published_at: `${report.season}-11-01` }),
      }));
      try {
        await pollPage.goto('http://127.0.0.1:4178/', { waitUntil: 'networkidle' });
        await pollPage.getByLabel('Choose dashboard section').selectOption('cfp');
        await pollPage.getByText('Official CFP snapshot:', { exact: false }).waitFor();
        const official = pollPage.locator('section.predictions-intro').filter({ hasText: 'Official CFP snapshot:' });
        await official.getByRole('row').filter({ hasText: topTeam }).locator('td').nth(2).getByText('#1').waitFor();
      } finally { await pollPage.close(); }
    }
    console.log(`Browser navigation smoke passed at ${width}px`);
    await page.close();
    const failedPage = await browser.newPage({ viewport: { width, height: 844 } });
    await failedPage.route('**/season-report.json', route => route.fulfill({ status: 503, body: 'Unavailable' }));
    await failedPage.goto('http://127.0.0.1:4178/');
    await failedPage.getByText('Waiting for live data').waitFor();
    // A transient refresh failure must recover without requiring an app reinstall.
    await failedPage.unroute('**/season-report.json');
    await failedPage.getByRole('button', { name: 'Retry loading data' }).click();
    await failedPage.getByRole('heading', { name: 'My Teams' }).waitFor();
    if (await failedPage.getByText('Waiting for live data').count()) throw new Error('Refresh retry did not clear the failure');
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
