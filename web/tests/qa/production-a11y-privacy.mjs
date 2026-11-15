// Read-only production QA (final pre-beta review, 2026-11-15). Requires: npm i --no-save playwright axe-core@4.10.3 (in web/).
// Navigates the public site only; blocks all third-party requests; never opts in to analytics. Run: node web/tests/qa/production-a11y-privacy.mjs
import { chromium } from 'playwright'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { createRequire } from 'node:module'
const URL_ = process.env.QA_URL || 'https://landrumc16.github.io/College-Football-Analytics/'
const OUT = process.env.QA_OUT || 'web/qa-evidence/'
await mkdir(OUT, { recursive: true })
const axeSrc = await readFile(createRequire(import.meta.url).resolve('axe-core/axe.min.js'), 'utf8')
const DEST = ['Home', 'Rankings', 'Teams', 'Playoffs', 'Research']
const results = { url: URL_, at: new Date().toISOString(), axe: {}, keyboard: {}, targets: {}, reflow: {}, privacy: {}, errors: [] }
const browser = await chromium.launch()

async function ctx(opts = {}) {
  const c = await browser.newContext({ serviceWorkers: 'block', ...opts })
  const external = []
  await c.route('**/*', r => { const u = r.request().url(); if (u.startsWith(URL_)) return r.continue(); external.push(u); return r.abort() })
  const p = await c.newPage(); p.setDefaultTimeout(20000)
  p.on('pageerror', e => results.errors.push(`${opts.viewport?.width}: ${e.message}`))
  p.on('console', m => { if (m.type() === 'error') results.errors.push(`console ${opts.viewport?.width}: ${m.text()}`) })
  return { c, p, external }
}
const nav = (p, name) => p.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name, exact: true }).click()
const ready = p => p.getByRole('heading', { name: 'Featured Matchups', exact: true }).waitFor()

// 1. axe-core WCAG 2.2 A/AA on each primary destination at phone and desktop widths
for (const width of [390, 1280]) {
  const { c, p } = await ctx({ viewport: { width, height: 900 } })
  await p.goto(URL_, { waitUntil: 'networkidle' }); await ready(p)
  for (const d of DEST) {
    await nav(p, d); await p.waitForTimeout(1200)
    if (d === 'Teams') { await p.getByLabel('Choose school').selectOption('Texas Tech').catch(() => {}); await p.waitForTimeout(800) }
    await p.addScriptTag({ content: axeSrc })
    const r = await p.evaluate(async () => await window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] } }))
    results.axe[`${width}-${d}`] = r.violations.map(v => ({ id: v.id, impact: v.impact, count: v.nodes.length, sample: v.nodes.slice(0, 3).map(n => n.target.join(' ') + ' :: ' + (n.failureSummary || '').split('\n').slice(1, 2).join('').trim()) }))
    await p.screenshot({ path: `${OUT}axe-${width}-${d}.png` })
  }
  await c.close()
}

// 2. Keyboard: tab through Home, record focus order and whether a visible indicator exists
{
  const { c, p } = await ctx({ viewport: { width: 1280, height: 900 } })
  await p.goto(URL_, { waitUntil: 'networkidle' }); await ready(p)
  await p.locator('body').click({ position: { x: 1, y: 1 } })
  const stops = []
  for (let i = 0; i < 60; i++) {
    await p.keyboard.press('Tab')
    stops.push(await p.evaluate(() => {
      const el = document.activeElement; if (!el || el === document.body) return null
      const s = getComputedStyle(el), r = el.getBoundingClientRect()
      const visible = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || (s.boxShadow && s.boxShadow !== 'none')
      return { tag: el.tagName, name: (el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 40), indicator: visible, onscreen: r.width > 0 && r.height > 0 }
    }))
  }
  const real = stops.filter(Boolean)
  results.keyboard = { stops: real.length, firstStops: real.slice(0, 8).map(s => `${s.tag}:${s.name}`), withoutIndicator: real.filter(s => !s.indicator).map(s => `${s.tag}:${s.name}`), offscreen: real.filter(s => !s.onscreen).length,
    skipLink: /skip/i.test(real[0]?.name || '') }
  // Keyboard-only navigation to Teams via Enter
  await p.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: 'Teams', exact: true }).focus()
  await p.keyboard.press('Enter'); await p.waitForTimeout(800)
  results.keyboard.enterActivatesNav = await p.getByLabel('Choose school').isVisible().catch(() => false)
  await c.close()
}

// 3. Touch targets at 390px: interactive elements smaller than 24px (WCAG 2.5.8) and 44px (Apple/WCAG AAA)
{
  const { c, p } = await ctx({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 })
  await p.goto(URL_, { waitUntil: 'networkidle' }); await ready(p)
  for (const d of DEST) {
    await nav(p, d); await p.waitForTimeout(1000)
    results.targets[d] = await p.evaluate(() => {
      const els = [...document.querySelectorAll('button, a[href], select, input, summary, [role=tab], [role=option]')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden' })
      const small = (n) => els.filter(e => { const r = e.getBoundingClientRect(); return r.height < n || r.width < n })
      const lab = e => `${e.tagName}:${(e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 30)}(${Math.round(e.getBoundingClientRect().width)}x${Math.round(e.getBoundingClientRect().height)})`
      return { total: els.length, under24: small(24).map(lab), under44: small(44).length }
    })
  }
  await c.close()
}

// 4. Reflow / 200% enlargement: 640px = 1280 desktop at 200% zoom; 320px = WCAG 1.4.10; plus 200% root text scaling
for (const [label, width, textScale] of [['zoom200-640', 640, false], ['reflow-320', 320, false], ['text200-390', 390, true]]) {
  const { c, p } = await ctx({ viewport: { width, height: 800 } })
  await p.goto(URL_, { waitUntil: 'networkidle' }); await ready(p)
  if (textScale) await p.addStyleTag({ content: 'html{font-size:200% !important}' })
  const per = {}
  for (const d of DEST) {
    await nav(p, d); await p.waitForTimeout(1000)
    per[d] = await p.evaluate(() => {
      const over = document.documentElement.scrollWidth - innerWidth
      const clipped = [...document.querySelectorAll('h1,h2,h3,p,button,label,summary')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 2 || r.left < -2) && !e.closest('.table-wrap') }).slice(0, 5).map(e => e.tagName + ':' + e.textContent.trim().slice(0, 30))
      return { horizontalOverflowPx: over, clippedOutsideViewport: clipped }
    })
    await p.screenshot({ path: `${OUT}${label}-${d}.png` })
  }
  // Does the root text scale actually enlarge body text? (px-only CSS would ignore it)
  if (textScale) per.bodyFontPx = await p.evaluate(() => parseFloat(getComputedStyle(document.querySelector('main') || document.body).fontSize))
  results.reflow[label] = per
  await c.close()
}

// 5. Privacy: first visit with no consent; storage, cookies, external requests; GPC context
for (const [label, extra] of [['default', {}], ['gpc', { extraHTTPHeaders: { 'Sec-GPC': '1' } }]]) {
  const { c, p, external } = await ctx({ viewport: { width: 390, height: 844 }, ...extra })
  if (label === 'gpc') await c.addInitScript(() => Object.defineProperty(navigator, 'globalPrivacyControl', { get: () => true }))
  await p.goto(URL_, { waitUntil: 'networkidle' }); await ready(p)
  for (const d of DEST) { await nav(p, d); await p.waitForTimeout(500) }
  await p.getByLabel('Choose school').selectOption('Texas Tech').catch(() => {})
  const storage = await p.evaluate(() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage), cookie: document.cookie }))
  results.privacy[label] = { storage, cookies: (await c.cookies()).map(k => k.name), externalRequestsAttempted: external }
  await c.close()
}
// Favorite persistence content check: what is stored when a fan saves a school
{
  const { c, p } = await ctx({ viewport: { width: 390, height: 844 } })
  await p.goto(URL_, { waitUntil: 'networkidle' }); await ready(p)
  const fav = p.getByRole('button', { name: /favorite|save/i }).first()
  if (await fav.count()) { await fav.click().catch(() => {}); await p.waitForTimeout(400) }
  results.privacy.afterFavoriteAttempt = await p.evaluate(() => Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k).slice(0, 200)])))
  await c.close()
}
await browser.close()
await writeFile(`${OUT}results.json`, JSON.stringify(results, null, 1))
console.log(JSON.stringify(results, null, 1))
