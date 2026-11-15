// Read-only production QA (2026-11-15): PWA assets, forced-colors / reduced-motion rendering,
// cold-load timing at phone width with 4x CPU throttle, and outbound link inventory. No analytics opt-in.
import { chromium } from 'playwright'
import { writeFile, mkdir } from 'node:fs/promises'
const U = process.env.QA_URL || 'https://landrumc16.github.io/College-Football-Analytics/', OUT = process.env.QA_OUT || 'web/qa-evidence/'
await mkdir(OUT, { recursive: true })
const res = {}
// PWA: manifest + icons + offline page + worker reachable with correct types
const man = await (await fetch(U + 'manifest.webmanifest')).json()
res.manifest = { display: man.display, start_url: man.start_url, scope: man.scope, icons: [] }
for (const i of man.icons) { const r = await fetch(U + i.src); const b = Buffer.from(await r.arrayBuffer()); res.manifest.icons.push({ src: i.src, sizes: i.sizes, status: r.status, png: b.subarray(1, 4).toString() === 'PNG', actual: `${b.readUInt32BE(16)}x${b.readUInt32BE(20)}` }) }
for (const f of ['offline.html', 'sw.js']) { const r = await fetch(U + f); res[f] = { status: r.status, type: r.headers.get('content-type'), cache: r.headers.get('cache-control') } }
const b = await chromium.launch()
const nav = (p, n) => p.getByRole('navigation', { name: 'Main navigation', exact: true }).getByRole('button', { name: n, exact: true }).click()
async function page(opts) { const c = await b.newContext({ serviceWorkers: 'block', ...opts }); await c.route('**/*', r => r.request().url().startsWith(U) ? r.continue() : r.abort()); const p = await c.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message)); return { c, p, errs } }
// Forced colors (Windows High Contrast) and reduced motion
for (const [label, opts] of [['forced-colors', { forcedColors: 'active' }], ['reduced-motion', { reducedMotion: 'reduce' }], ['light-scheme', { colorScheme: 'light' }]]) {
  const { c, p, errs } = await page({ viewport: { width: 390, height: 844 }, ...opts })
  await p.goto(U, { waitUntil: 'networkidle' })
  for (const d of ['Home', 'Rankings', 'Teams', 'Playoffs', 'Research']) { await nav(p, d); await p.waitForTimeout(500) }
  await p.screenshot({ path: `${OUT}${label}-research.png` })
  res[label] = { errors: errs, overflow: await p.evaluate(() => document.documentElement.scrollWidth - innerWidth),
    longAnimations: await p.evaluate(() => [...document.querySelectorAll('*')].filter(e => { const s = getComputedStyle(e); return parseFloat(s.animationDuration) > 0.01 || parseFloat(s.transitionDuration) > 0.3 }).length) }
  await c.close()
}
// Cold load timing, 390px, 4x CPU throttle (single sample set; public-network latency included)
res.coldLoad = []
for (let i = 0; i < 3; i++) {
  const { c, p } = await page({ viewport: { width: 390, height: 844 } })
  const cdp = await c.newCDPSession(p); await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 })
  const t0 = Date.now(); await p.goto(U); await p.getByRole('heading', { name: 'Featured Matchups', exact: true }).waitFor({ timeout: 30000 })
  const featured = Date.now() - t0
  const m = await p.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; const fcp = performance.getEntriesByName('first-contentful-paint')[0]; return { ttfb: Math.round(n.responseStart), domContentLoaded: Math.round(n.domContentLoadedEventEnd), fcp: fcp && Math.round(fcp.startTime), transferKB: Math.round(performance.getEntriesByType('resource').reduce((s, r) => s + (r.transferSize || 0), n.transferSize) / 1024) } })
  res.coldLoad.push({ featuredMatchupsVisibleMs: featured, ...m }); await c.close()
}
// Outbound links in the app (Menu → About & privacy etc.)
{ const { c, p } = await page({ viewport: { width: 1280, height: 900 } }); await p.goto(U, { waitUntil: 'networkidle' })
  await p.locator('summary[aria-label="App menu"]').click().catch(() => {})
  for (const s of await p.locator('details:not([open]) > summary').all()) await s.click().catch(() => {})
  res.links = [...new Set(await p.$$eval('a[href]', as => as.map(a => a.href)))]
  res.linksNewTabWithoutNoopener = await p.$$eval('a[target=_blank]', as => as.filter(a => !/noopener|noreferrer/.test(a.rel)).map(a => a.href)); await c.close() }
await b.close()
await writeFile(`${OUT}pwa-render-perf.json`, JSON.stringify(res, null, 1)); console.log(JSON.stringify(res, null, 1))
