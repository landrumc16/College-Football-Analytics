// Consolidated Poll Rankings: deterministic tie / NR / alias / sorting / keyboard / mobile-fit checks.
// The poll snapshot response is replaced with a controlled fixture; all other app data is real.
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { mkdir } from 'node:fs/promises'
import { setTimeout as delay } from 'node:timers/promises'
import { chromium } from 'playwright'
import { chooseSection } from './section-navigation.mjs'

const url = 'http://127.0.0.1:4196/', out = 'web/mobile-evidence'
await mkdir(out, { recursive: true })
const server = spawn('npm', ['run', 'preview', '--', '--host', '127.0.0.1', '--port', '4196', '--strictPort'], { cwd: 'web', stdio: 'ignore', detached: true })
const report = await import('node:fs').then(fs => JSON.parse(fs.readFileSync('web/public/season-report.json', 'utf8')))
const ap = [['Georgia', 1], ['Utah', 2], ['Notre Dame', 3], ['Texas Tech', 3], ['Miami', 5], ['Oregon', 6]]
const coaches = [['Utah', 1], ['Georgia', 2], ['Texas Tech', 3], ['Notre Dame', 4], ['Miami', 5], ['Alabama', 6]]
const fixture = { season: report.season, week: 11, source: 'Test fixture', ap_top25: ap.map(([team, rank]) => ({ team, rank })),
  coaches_top25: coaches.map(([team, rank]) => ({ team, rank })) }
let browser
try {
  for (let i = 0; i < 40; i++) { try { if ((await fetch(url)).ok) break } catch {} await delay(250) }
  browser = await chromium.launch({ headless: true })
  for (const width of [375, 390, 430, 768, 1536]) {
    const context = await browser.newContext({ viewport: { width, height: width === 1536 ? 900 : 844 }, serviceWorkers: 'block' })
    await context.route('**/poll-snapshot.json', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(fixture) }))
    const page = await context.newPage(); page.setDefaultTimeout(15000)
    const errors = []; page.on('pageerror', e => errors.push(e.message))
    await page.goto(url, { waitUntil: 'networkidle' })
    await page.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: 'Rankings', exact: true }).click()
    await chooseSection(page, 'Rankings sections', 'Poll Rankings')
    await page.getByRole('heading', { name: 'Poll Rankings', exact: true }).waitFor()
    const rows = async () => page.locator('.poll-rankings-table tbody tr').evaluateAll(trs => trs.map(tr => [...tr.children].map(c => c.textContent.trim())))
    // Default AP sort: tie shown as T-3 for both teams, tie broken by Coaches rank; Coaches-only team NR in AP, last.
    assert.deepEqual(await rows(), [['Georgia', '1', '2'], ['Utah', '2', '1'], ['Texas Tech', 'T-3', '3'], ['Notre Dame', 'T-3', '4'],
      ['Miami (FL)', '5', '5'], ['Oregon', '6', 'NR'], ['Alabama', 'NR', '6']])
    assert.equal(await page.locator('.poll-rankings-table th[aria-sort="ascending"]').textContent(), 'AP ▲')
    // Keyboard: Tab to the Coaches heading button and activate it with Space.
    const coachesButton = page.getByRole('button', { name: 'Sort by Coaches Poll ranking', exact: true })
    await coachesButton.focus(); await page.keyboard.press('Space')
    assert.equal(await coachesButton.locator('xpath=..').getAttribute('aria-sort'), 'ascending')
    assert.equal(await page.getByRole('button', { name: 'Sort by AP Poll ranking', exact: true }).locator('xpath=..').getAttribute('aria-sort'), 'none')
    assert.deepEqual((await rows()).map(r => r[0]), ['Utah', 'Georgia', 'Texas Tech', 'Notre Dame', 'Miami (FL)', 'Alabama', 'Oregon'])
    assert.equal(await page.locator('[role="status"]').filter({ hasText: 'Sorted by Coaches Poll ranking' }).count(), 1)
    // Screen-reader labels for ranks.
    assert.equal(await page.locator('.poll-rankings-table tbody tr').nth(2).locator('td').first().getAttribute('aria-label'), 'AP tied 3')
    assert.equal(await page.locator('.poll-rankings-table tbody tr').last().locator('td').nth(1).getAttribute('aria-label'), 'Coaches not ranked')
    // Conference filter uses canonical names (poll "Miami" is Miami (FL) in the ACC) and search persists across views.
    await page.getByLabel('Filter polls by conference').selectOption('ACC')
    assert.deepEqual((await rows()).map(r => r[0]), ['Miami (FL)'])
    await page.getByLabel('Filter polls by conference').selectOption('all')
    // Search text and conference selection persist while the user re-sorts within the view.
    await page.getByLabel('Filter polls by conference').selectOption('Big 12')
    await page.getByLabel('Search poll teams').fill('tech')
    assert.deepEqual((await rows()).map(r => r[0]), ['Texas Tech'])
    await page.getByRole('button', { name: 'Sort by AP Poll ranking', exact: true }).click()
    assert.equal(await page.getByLabel('Search poll teams').inputValue(), 'tech')
    assert.equal(await page.getByLabel('Filter polls by conference').inputValue(), 'Big 12')
    assert.deepEqual((await rows()).map(r => r[0]), ['Texas Tech'])
    await page.getByLabel('Search poll teams').fill('')
    await page.getByLabel('Filter polls by conference').selectOption('all')
    // Mobile fit: no horizontal page or table overflow.
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'page overflow')
    assert.ok(await page.locator('.poll-rankings-table').evaluate(el => el.scrollWidth <= el.clientWidth + 1), 'poll table overflow')
    await page.locator('.poll-rankings').screenshot({ path: `${out}/poll-rankings-${width}.png` })
    assert.deepEqual(errors, [])
    console.log(`Poll Rankings passed at ${width}px`)
    await context.close()
  }
} finally { await browser?.close(); try { process.kill(-server.pid, 'SIGTERM') } catch (error) { if (error.code !== 'ESRCH') throw error } }
