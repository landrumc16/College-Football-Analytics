import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { createServer } from 'node:http';
import { connect } from 'node:net';

// The same journeys validate the local build and the actual published app.
const liveUrl = process.env.DASHBOARD_URL;
const baseUrl = liveUrl ? new URL('./', liveUrl).href : 'http://127.0.0.1:4178/';
let denyNetwork = false;
const connections = new Set();
const networkGate = liveUrl ? createServer() : null;
if (networkGate) {
  // Closing these browser-only tunnels makes the live origin truly unreachable
  // to service-worker fetches without affecting the public site or other users.
  networkGate.on('connect', (request, socket, head) => {
    if (denyNetwork) { socket.destroy(); return; }
    const destination = new URL(`https://${request.url}`);
    const upstream = connect(Number(destination.port) || 443, destination.hostname);
    for (const connection of [socket, upstream]) {
      connections.add(connection);
      connection.on('close', () => connections.delete(connection));
      connection.on('error', () => { socket.destroy(); upstream.destroy(); });
    }
    upstream.once('connect', () => {
      socket.write('HTTP/1.1 200 Connection Established\r\n\r\n');
      if (head.length) upstream.write(head);
      socket.pipe(upstream); upstream.pipe(socket);
    });
  });
  await new Promise(resolve => networkGate.listen(0, '127.0.0.1', resolve));
}
const startServer = () => spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4178', '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true });
let server = liveUrl ? null : startServer();
let browser;
async function waitForPreview() {
  if (liveUrl) return;
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch('http://127.0.0.1:4178/');
      if (response.ok) { ready = true; break; }
    } catch {}
    await delay(500);
  }
  if (!ready) throw new Error('Dashboard development server did not start');
}

const sections = {
  home: ['Home', 'This Week'], predictions: ['Home', 'Game Predictions'],
  rankings: ['Rankings', 'Model Rankings'], ap: ['Rankings', 'AP Poll'], coaches: ['Rankings', 'Coaches Poll'], stock: ['Rankings', 'Team Stock Watch'],
  profile: ['Teams', 'Team Profiles'], compare: ['Teams', 'Compare & What If'], programs: ['Teams', 'Program Directory'], hype: ['Teams', 'Hype Index'], trajectory: ['Teams', 'Program Trajectory'],
  cfp: ['Playoffs', 'CFP Projections'], conferences: ['Playoffs', 'Conference Races'], contenders: ['Playoffs', 'Contenders & Pretenders'],
  research: ['Research', 'Prediction Accuracy'], history: ['Research', 'Historical Research'], methods: ['Research', 'Methodology'], sources: ['Research', 'Data Sources'], validation: ['Research', 'Model Validation'],
};
async function navigate(page, view) {
  const [destination, label] = sections[view];
  await page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: destination, exact: true }).click();
  await page.getByRole('tablist', { name: `${destination} sections`, exact: true }).getByRole('tab', { name: label, exact: true }).click();
}
async function profileTab(page, label) {
  await page.getByRole('tablist', { name: 'Team Profile sections', exact: true }).getByRole('tab', { name: label, exact: true }).click();
}

async function assertReportCard(page, team) {
  const published = await page.evaluate(async () => (await fetch('./v5-program-report-cards.json')).json());
  const record = published.programs.find(p => p.team === team);
  if (!record) throw new Error('Missing eligible report card: ' + team);
  const card = page.getByRole('region', { name: `CFA Program Report Card for ${team}`, exact: true }).first();
  await card.getByRole('heading', { name: `${team} · CFA Program Report Card` }).waitFor();
  for (const key of ['hype', 'trajectory', 'strength']) {
    const c = record.categories[key];
    const label = key === 'hype' ? 'Hype Index' : key === 'trajectory' ? 'Program Trajectory' : 'Program Strength';
    const tile = card.locator('.team-profile-tile').filter({ has: page.getByText(label, { exact: true }) });
    await tile.getByText(c.score === null ? 'N/A' : `${c.grade} (${c.score.toFixed(1)})`, { exact: true }).waitFor();
  }
  if (record.overall_score !== null) await card.getByText(`${record.overall_grade} (${record.overall_score.toFixed(1)}/100)`, { exact: true }).waitFor();
}

try {
  await waitForPreview();
  browser = await chromium.launch({ headless: true,
    ...(networkGate ? { proxy: { server: `http://127.0.0.1:${networkGate.address().port}` } } : {}) });
  await mkdir('web/mobile-evidence', { recursive: true });
  for (const width of [375, 390, 768, 1536]) {
    const page = await browser.newPage({ viewport: { width, height: width === 1536 ? 900 : 844 }, deviceScaleFactor: 1 });
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /College Football Analytics/i }).waitFor();
    await page.getByRole('navigation', { name: 'Main navigation', exact: true }).waitFor();
    const mainLabels = await page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button').allTextContents();
    if (JSON.stringify(mainLabels) !== JSON.stringify(['Home', 'Rankings', 'Teams', 'Playoffs', 'Research'])) throw new Error('Primary navigation must contain exactly five ordered destinations');
    if (await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: 'Home', exact: true }).getAttribute('aria-current') !== 'page') throw new Error('This Week is not the default homepage');
    await page.getByRole('heading', { name: 'Playoff Snapshot', exact: true }).waitFor();
    // Tabs must be operable by keyboard as well as touch.
    await navigate(page, 'rankings');
    const modelTab = page.getByRole('tab', { name: 'Model Rankings', exact: true });
    await modelTab.press('ArrowRight');
    if (await page.getByRole('tab', { name: 'AP Poll', exact: true }).getAttribute('aria-selected') !== 'true') throw new Error('Arrow-key navigation failed');
    await page.getByRole('tab', { name: 'AP Poll', exact: true }).press('End');
    if (await page.getByRole('tab', { name: 'Team Stock Watch', exact: true }).getAttribute('aria-selected') !== 'true') throw new Error('End-key navigation failed');
    await page.getByRole('tab', { name: 'Team Stock Watch', exact: true }).press('Home');
    if (await modelTab.getAttribute('aria-selected') !== 'true') throw new Error('Home-key navigation failed');
    await page.getByLabel('Search teams').fill('Georgia');
    const rankingNames = await page.locator('table tbody tr td:first-child').allTextContents();
    if (!rankingNames.length || rankingNames.some(name => !name.includes('Georgia'))) throw new Error('Model ranking search failed');
    await navigate(page, 'home');
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
      await isolatedPage.goto(baseUrl, { waitUntil: 'networkidle' });
      await isolatedPage.getByRole('heading', { name: 'My Teams' }).waitFor();
      if (await isolatedPage.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).count()) {
        throw new Error('Favorite leaked into a separate browser profile');
      }
      const isolatedFavorites = await isolatedPage.evaluate(() => JSON.parse(localStorage.getItem('cfba-favorites-v1') || '[]'));
      if (isolatedFavorites.some(Boolean)) throw new Error('New browser profile inherited favorites');
    } finally {
      await isolatedContext.close();
    }
    await page.getByRole('button', { name: 'View schedule', exact: true }).first().click();
    await page.getByRole('heading', { name: 'Full Season Schedule and Model Outlook', exact: true }).waitFor();
    if (await page.getByLabel('Choose school').inputValue() !== firstTeam) throw new Error('Favorite schedule shortcut lost its school');
    if (await page.getByRole('tab', { name: 'Schedule & Predictions', exact: true }).getAttribute('aria-selected') !== 'true') throw new Error('Favorite schedule did not open the Profile schedule tab');
    await profileTab(page, 'Historical Intelligence');
    await page.getByRole('region', { name: 'Historical FBS results', exact: true }).waitFor();
    await navigate(page, 'home');
    // A saved school must open its complete Team Profile, not just its schedule.
    await page.getByRole('button', { name: 'Team profile' }).first().click();
    await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
    if (await page.getByLabel('Choose school').inputValue() !== firstTeam) throw new Error('Favorite-to-profile navigation lost the selected team');
    await navigate(page, 'home');
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).waitFor();
    await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).click();
    await page.reload({ waitUntil: 'networkidle' });
    if (await page.getByRole('button', { name: `Remove ${firstTeam} from favorites` }).count()) throw new Error('Favorite removal did not persist');

    const report = await page.evaluate(async () => { const response = await fetch('./season-report.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; });
    if (!report?.rankings?.length || !report?.predictions?.length) throw new Error('Published report missing usable rankings or predictions');
    // Opening Team Profile directly from navigation must select a real school.
    await navigate(page, 'profile');
    if (await page.getByLabel('Choose school').inputValue() !== report.rankings[0].team) {
      throw new Error('Direct Team Profile navigation did not select the first available school');
    }
    await navigate(page, 'home');
    for (const section of ['rankings', 'ap', 'coaches', 'predictions', 'conferences', 'cfp', 'compare', 'programs', 'hype', 'trajectory', 'stock', 'contenders', 'profile', 'history', 'methods', 'sources', 'validation']) {
      await navigate(page, section);
      if (section === 'ap' || section === 'coaches') {
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
        await page.getByLabel('Search teams').fill('Georg');
        await page.getByRole('listbox', { name: 'Suggested schools' }).getByRole('option', { name: 'Georgia', exact: true }).click();
        if (!(await page.locator('.prediction-card').count()) || (await page.locator('.prediction-matchup').allTextContents()).some(name => !name.includes('Georgia'))) throw new Error('Prediction autocomplete failed');
        await page.getByLabel('Search teams').fill('');
        const firstCard = page.locator('.prediction-card').first();
        const matchup = (await firstCard.locator('.prediction-matchup').innerText()).split('@').map(part => part.trim());
        if (matchup.length !== 2 || !matchup.every(Boolean)) throw new Error('Prediction card lacks a valid matchup');
        await firstCard.getByRole('button', { name: 'Compare teams' }).click();
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        if (await page.getByLabel('First school').inputValue() !== matchup[1] || await page.getByLabel('Second school').inputValue() !== matchup[0]) {
          throw new Error('Prediction-to-Compare did not preserve the visible card matchup');
        }
        await page.getByRole('region', { name: 'Side-by-side team comparison' }).waitFor();
        await navigate(page, 'predictions');
      }
      if (section === 'hype') await page.getByRole('heading', { name: 'Historical Hype Index', exact: true }).waitFor();
      if (section === 'hype') {
        await page.getByText('Current-season poll disagreement', { exact: true }).click();
        await page.getByRole('region', { name: 'Current-season poll perception', exact: true }).waitFor();
        await page.getByLabel('Choose AP or Coaches Poll').selectOption('Coaches');
        await page.getByLabel('Sort current poll perception').selectOption('disagreement');
        await page.getByLabel('Filter current poll perception by conference').selectOption('all');
        await page.getByText('Current-season poll disagreement', { exact: true }).click();
      }
      if (section === 'hype' || section === 'trajectory') {
        await page.getByRole('region', { name: 'Verified national historical intelligence' }).waitFor();
        await page.getByLabel('Choose historical program').selectOption(firstTeam);
        await assertReportCard(page, firstTeam);
        await page.getByLabel('Search historical programs').fill(firstTeam);
        const historical = page.getByRole('region', { name: 'Verified national historical intelligence' });
        const expectedNames = await page.evaluate(async ({ query, category }) => {
          const published = await (await fetch('./v5-program-report-cards.json')).json();
          return published.programs.filter(p => p.team.toLowerCase().includes(query.toLowerCase()))
            .sort((a, b) => (b.categories[category].score ?? -1) - (a.categories[category].score ?? -1) || a.team.localeCompare(b.team)).slice(0, 25).map(p => p.team);
        }, { query: firstTeam, category: section === 'hype' ? 'hype' : 'trajectory' });
        await page.waitForFunction(count => document.querySelector('[aria-label="Verified national historical intelligence"] tbody')?.children.length === count, expectedNames.length);
        const actualNames = await historical.locator('tbody tr td:first-child button').allTextContents();
        if (JSON.stringify(actualNames) !== JSON.stringify(expectedNames)) throw new Error('Verified historical search differs from source-backed results');
      }
      if (section === 'trajectory') await page.getByRole('heading', { name: 'Program Trajectory & Momentum', exact: true }).waitFor();
      if (['programs', 'stock', 'contenders'].includes(section)) {
        await page.getByRole('heading', { name: section === 'stock' ? 'Team Stock Watch' : section === 'contenders' ? 'Contenders & Pretenders' : 'Program Intelligence', exact: true }).waitFor();
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
        await assertReportCard(page, firstTeam);
        const row = page.getByRole('row').filter({ hasText: firstTeam }).first();
        const overviewTrend = (await row.locator('td').nth(7).textContent() || '').trim();
        await row.getByRole('button', { name: `Compare ${firstTeam} with another school` }).click();
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        if (await page.getByLabel('First school').inputValue() !== firstTeam) throw new Error('Program-to-comparison navigation lost the selected team');
        await navigate(page, 'programs');
        await page.getByLabel('Find a program').fill(firstTeam);
        await page.getByRole('row').filter({ hasText: firstTeam }).first().getByRole('button', { name: 'View team' }).click();
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        await page.getByText('Form, conference and postseason details', { exact: true }).click();
        const profileTrend = page.locator('.team-profile-tile').filter({ hasText: 'Current-Season Form Trend' });
        await profileTrend.waitFor();
        const profileTrendValue = (await profileTrend.locator('strong').textContent() || '').trim();
        if (profileTrendValue !== (overviewTrend === '—' ? 'Requires 8 scored games' : overviewTrend)) {
          throw new Error(`Team Profile and Program Intelligence disagree on current-season form trend for ${firstTeam}: overview=${JSON.stringify(overviewTrend)}, profile=${JSON.stringify(profileTrendValue)}`);
        }
        if (await page.getByLabel('Choose school').inputValue() !== firstTeam) {
          throw new Error(`Program Intelligence did not preserve selected team for ${section}`);
        }
        await navigate(page, section);
      }
      if (section === 'profile') {
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        await page.getByLabel('Choose school').selectOption(firstTeam);
        await profileTab(page, 'Program Report Card');
        await assertReportCard(page, firstTeam);
        await profileTab(page, 'Historical Intelligence');
        const verifiedProfile = await page.evaluate(async team => (await (await fetch('./v5-program-report-cards.json')).json()).programs.find(p => p.team === team), firstTeam);
        if (verifiedProfile.trajectory) await page.getByText(`Long-term trajectory: ${verifiedProfile.trajectory.direction}`, { exact: false }).waitFor();
        if (await page.getByText('Not published with verified multi-season coverage', { exact: false }).count() || await page.getByText('Historical research has not passed the publication gate', { exact: false }).count()) throw new Error('Legacy missing-history message contradicts verified publication');
        await profileTab(page, 'Schedule & Predictions');
        await page.getByText('Full Season Schedule and Model Outlook').waitFor();
        const explanations = page.locator('details').filter({ has: page.locator('summary').getByText('Upcoming prediction explanations', { exact: true }) });
        if (!(await explanations.evaluate(element => element.open))) await explanations.locator('summary').click();
        try {
          await explanations.getByRole('columnheader').filter({ hasText: 'Team win probability' }).waitFor();
        } catch (error) {
          console.log('Schedule disclosure diagnostic:', await explanations.evaluate(element => ({ open: element.open, headers: [...element.querySelectorAll('th')].map(th => ({ text: th.textContent, display: getComputedStyle(th).display, visibility: getComputedStyle(th).visibility })) })));
          console.log('Exposed header roles:', await explanations.getByRole('columnheader').allTextContents());
          await page.screenshot({ path: `web/mobile-evidence/schedule-failure-${width}.png`, fullPage: true });
          throw error;
        }
        await page.getByRole('button', { name: 'Compare this school' }).click();
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        if (await page.getByLabel('First school').inputValue() !== firstTeam) throw new Error('Profile-to-Compare lost selected school');
        await navigate(page, 'profile');
      }
      if (section === 'cfp') {
        await page.getByRole('heading', { name: 'Projected 12-Team CFP Field' }).waitFor();
        await page.getByRole('heading', { name: 'Our Top 25 vs. Official CFP Top 25' }).waitFor();
        await page.getByRole('heading', { name: 'Playoff Bubble' }).waitFor();
        const poll = await page.evaluate(async () => { try { const response = await fetch('./poll-snapshot.json'); return response.ok && response.headers.get('content-type')?.includes('json') ? response.json() : null; } catch { return null; } });
        if (!poll?.cfp_published_at || !poll?.cfp_top25?.length) {
          await page.getByText('A verified, publication-dated official CFP Top 25 is not available', { exact: false }).waitFor();
        } else if (poll.cfp_week != null) {
          await page.getByText(`CFP poll week ${poll.cfp_week}`, { exact: false }).waitFor();
        }
      }
      if (section === 'compare') {
        await page.getByRole('heading', { name: 'Compare Teams', exact: true }).waitFor();
        const secondTeam = report.rankings.find(team => team.team !== firstTeam)?.team;
        if (!secondTeam) throw new Error('Need two distinct teams for comparison');
        await page.getByLabel('First school').selectOption(firstTeam);
        await page.getByLabel('Second school').selectOption(secondTeam);
        await assertReportCard(page, firstTeam);
        await assertReportCard(page, secondTeam);
        const comparison = page.getByRole('region', { name: 'Side-by-side team comparison' });
        await comparison.getByRole('heading', { name: 'Side-by-side team comparison' }).waitFor();
        const historicalComparison = comparison.getByRole('region', { name: 'Historical FBS results' });
        await historicalComparison.getByRole('heading', { name: 'Historical FBS results comparison' }).waitFor();
        await historicalComparison.getByLabel('Historical results window').selectOption('3');
        const historicalResponse = await page.evaluate(async () => {
          const r = await fetch('./v5-historical-results.json');
          return r.ok ? r.json() : null;
        });
        if (!historicalResponse || historicalResponse.status !== 'independently_corroborated_results' || historicalResponse.source_review_attested !== true) {
          throw new Error('Historical comparison is missing its reviewed source provenance');
        }
        if (historicalResponse.programs.length < 120) throw new Error('Historical source is not national in coverage');
        const historicalAliases = { 'Miami (FL)': 'Miami', 'Appalachian State': 'App State', ULM: 'UL Monroe', 'Sam Houston State': 'Sam Houston' };
        const historicalName = name => historicalAliases[name] || name;
        for (const name of [firstTeam, secondTeam]) {
          const record = historicalResponse.programs.find(p => historicalName(p.team) === historicalName(name));
          if (!record) {
            await historicalComparison.getByText('No independently documented historical results for ' + name, { exact: false }).waitFor();
          } else if (!record.windows['3']) {
            await historicalComparison.getByText(name + ' has insufficient verified season coverage', { exact: false }).waitFor();
          }
        }
        const historicalRows = historicalComparison.locator('tbody tr');
        if (await historicalRows.count() !== [firstTeam, secondTeam].filter(name => historicalResponse.programs.some(p => historicalName(p.team) === historicalName(name))).length) throw new Error('Historical Compare rows do not match documented source coverage');
        for (const teamName of [firstTeam, secondTeam]) {
          if (historicalResponse.programs.some(p => p.team === historicalName(teamName)) && !await historicalRows.filter({ hasText: historicalName(teamName) }).count()) throw new Error('Historical Compare missing ' + teamName);
        }
        if (!await historicalComparison.getByText('unadjusted win percentages', { exact: false }).count()) {
          throw new Error('Historical comparison is missing its metric limitations');
        }
        await page.getByLabel('Game location').selectOption('neutral');
        await page.locator('.matchup-result').waitFor();
        await page.getByRole('button', { name: 'Swap schools', exact: true }).click();
        if (await page.getByLabel('First school').inputValue() !== secondTeam) throw new Error('What If swap failed');
        await page.getByRole('button', { name: 'Swap schools', exact: true }).click();
        await comparison.getByRole('columnheader', { name: firstTeam }).waitFor();
        await comparison.getByRole('columnheader', { name: secondTeam }).waitFor();
        await comparison.getByRole('button', { name: `View ${firstTeam} profile` }).click();
        await page.getByRole('heading', { name: 'Team Profile', exact: true }).waitFor();
        if (await page.getByLabel('Choose school').inputValue() !== firstTeam) throw new Error('Compare-to-profile navigation lost team selection');
        await navigate(page, 'compare');
      }
      if (await page.locator(`#dashboard-panel-${section}`).getAttribute('aria-selected') !== 'true') {
        throw new Error(`Navigation failed for ${section} at ${width}px`);
      }
      if (section === 'history') {
        await page.getByText('Multi-season Historical Research', { exact: true }).click();
        await page.getByRole('region', { name: 'V2 Multi-season Research', exact: true }).waitFor();
      }
      if (section === 'methods') await page.getByRole('heading', { name: 'Model and historical methods', exact: true }).waitFor();
      if (section === 'sources') await page.getByRole('heading', { name: 'Published data and provenance', exact: true }).waitFor();
      if (section === 'validation') await page.getByRole('region', { name: 'Retrospective Weekly Backtest', exact: true }).waitFor();
      // Only the CFP page may display the CFP projection's full statistical table.
      if (section !== 'cfp' && await page.getByRole('columnheader', { name: 'Avg Seed If Selected' }).count()) {
        throw new Error(`Unrelated CFP projection table leaked into ${section}`);
      }
      const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
      if (horizontalOverflow) throw new Error(`Page-wide horizontal overflow in ${section} at ${width}px`);
      if (['rankings', 'predictions', 'compare', 'cfp', 'profile', 'stock', 'contenders', 'programs', 'hype', 'trajectory'].includes(section)) {
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
        await pollPage.goto(baseUrl, { waitUntil: 'networkidle' });
        await navigate(pollPage, 'cfp');
        await pollPage.getByText('Official CFP snapshot:', { exact: false }).waitFor();
        const official = pollPage.locator('section.predictions-intro').filter({ hasText: 'Official CFP snapshot:' });
        await official.getByRole('row').filter({ hasText: topTeam }).locator('td').nth(2).getByText('#1').waitFor();
      } finally { await pollPage.close(); }
    }
    await navigate(page, 'research');
    const archive = page.getByRole('region', { name: 'Independent pregame forecast verification' });
    await archive.getByRole('heading', { name: 'Independently verified forecast archive' }).waitFor();
    await archive.getByText('65 predictions', { exact: false }).waitFor();
    await page.screenshot({ path: `web/mobile-evidence/forecast-evidence-${width}.png`, fullPage: true });
    console.log(`Browser navigation smoke passed at ${width}px`);
    await page.close();
    const failedPage = await browser.newPage({ viewport: { width, height: 844 } });
    await failedPage.route('**/season-report.json', route => route.fulfill({ status: 503, body: 'Unavailable' }));
    await failedPage.goto(baseUrl);
    await failedPage.getByText('Waiting for live data').waitFor();
    // A transient refresh failure must recover without requiring an app reinstall.
    await failedPage.unroute('**/season-report.json');
    await failedPage.getByRole('button', { name: 'Retry loading data' }).click();
    await failedPage.getByRole('heading', { name: 'My Teams' }).waitFor();
    if (await failedPage.getByText('Waiting for live data').count()) throw new Error('Refresh retry did not clear the failure');
    await failedPage.close();
  }
  const android = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36' });
  const app = await android.newPage();
  await app.goto(baseUrl, { waitUntil: 'networkidle' });
  await app.evaluate(() => navigator.serviceWorker.ready);
  await app.reload({ waitUntil: 'networkidle' });
  await app.waitForFunction(() => navigator.serviceWorker.controller !== null);
  const cdp = await android.newCDPSession(app);
  const installability = await cdp.send('Page.getInstallabilityErrors');
  if (installability.installabilityErrors.length) throw new Error('Android PWA installability: ' + JSON.stringify(installability.installabilityErrors));
  await app.getByRole('heading', { name: 'My Teams' }).waitFor();
  await app.screenshot({ path: 'web/mobile-evidence/android-pwa-online.png', fullPage: true });
  await app.evaluate(async () => {
    await navigator.serviceWorker.register('./sw.js?acceptance-update', { scope: './' });
  });
  await app.getByText('App update available', { exact: true }).waitFor();
  await app.getByRole('button', { name: 'Reload app', exact: true }).click();
  await app.getByRole('heading', { name: 'My Teams' }).waitFor();
  await app.waitForFunction(async () => {
    const registration = await navigator.serviceWorker.getRegistration();
    return registration?.active?.state === 'activated' && !registration.installing && !registration.waiting && registration.active.scriptURL.endsWith('/sw.js') && navigator.serviceWorker.controller?.scriptURL === registration.active.scriptURL;
  });
  await android.setOffline(true);
  // A real unavailable server also covers Chromium builds whose emulated
  // offline flag does not consistently reach service-worker fetches.
  if (networkGate) {
    denyNetwork = true;
    for (const connection of connections) connection.destroy();
  } else {
    const stopped = new Promise(resolve => server.once('exit', resolve));
    process.kill(-server.pid, 'SIGTERM');
    await stopped;
  }
  await app.reload({ waitUntil: 'load' });
  await app.getByRole('heading', { name: 'You are offline' }).waitFor();
  await app.screenshot({ path: 'web/mobile-evidence/android-pwa-offline.png', fullPage: true });
  const cached = await app.evaluate(async () => {
    const keys = await caches.keys();
    return (await Promise.all(keys.map(async key => (await (await caches.open(key)).keys()).map(r => r.url)))).flat();
  });
  if (cached.some(url => /\.json(?:$|\?)/.test(url))) throw new Error('PWA cached live JSON as current data');
  if (networkGate) denyNetwork = false;
  else server = startServer();
  await waitForPreview();
  await android.setOffline(false);
  await app.getByRole('link', { name: 'Try again' }).click();
  await app.getByRole('heading', { name: 'My Teams' }).waitFor();
  await android.close();
  console.log('Android Chrome emulation: installability, update, offline and recovery passed');
} finally {
  await browser?.close();
  if (networkGate) {
    for (const connection of connections) connection.destroy();
    await new Promise(resolve => networkGate.close(resolve));
  }
  // npm launches Vite as a child; terminate the entire process group so
  // inherited handles cannot keep the GitHub Actions job alive.
  if (server?.pid) {
    try { process.kill(-server.pid, 'SIGTERM'); } catch (error) {
      if (error.code !== 'ESRCH') throw error;
    }
  }
}
