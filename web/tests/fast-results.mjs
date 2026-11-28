// Controlled fixtures only; never contact or impersonate a production data source.
import assert from 'node:assert/strict'
import {spawn} from 'node:child_process'
import {readFile} from 'node:fs/promises'
import {setTimeout as delay} from 'node:timers/promises'
import {chromium} from 'playwright'
const server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port','4198','--strictPort'],{cwd:'web',stdio:'ignore',detached:true})
let browser
try {
 for(let i=0;i<40;i++){try{if((await fetch('http://127.0.0.1:4198/')).ok)break}catch{}await delay(250)}
 browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})})
 for(const width of [390,1536]) {
  const context=await browser.newContext({viewport:{width,height:900}})
  await context.route('**/*',r=>['127.0.0.1','localhost'].includes(new URL(r.request().url()).hostname)?r.continue():r.abort())
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message))
  const report=JSON.parse(await readFile('web/dist/season-report.json','utf8'))
  const retained=report.schedule.find(g=>g.home==='Texas Tech' && g.away==='TCU')
  assert.ok(retained)
  const event={game_id:retained.game_id,home:'Texas Tech',away:'TCU',home_score:48,away_score:27,status:'provisional',observed_at:'2026-11-26T20:00:00Z',verified_at:null,statistics_pending:true,source:'https://authorized.example/game/999',model_ingestion_allowed:false,basic_stats:{home:{total_yards:400}}}
  const feed={schema_version:1,revision:1,generated_at:'2026-11-26T20:01:00Z',events:[event],records:{'Texas Tech':{wins:11,losses:1,provisional_games:1}}}
  await page.route('**/fast-results.json',r=>r.fulfill({json:feed}))
  await page.goto('http://127.0.0.1:4198/',{waitUntil:'networkidle'})
  const panel=page.locator('section[aria-label="Rapid game results"]')
  await panel.getByText('Provisional Final').waitFor()
  assert.match(await panel.innerText(),/11–1 \(provisional\)/)
  assert.match(await panel.innerText(),/Statistics pending/)
  assert.match(await panel.innerText(),/400/)
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
  event.status='corrected';event.verified_at='2026-11-26T21:00:00Z';event.model_ingestion_allowed=true;event.home_score=49;feed.revision=2
  await page.reload({waitUntil:'networkidle'});await panel.getByText('Corrected — CFBD Verified').waitFor()
  assert.match(await panel.innerText(),/Texas Tech 49/)
  await page.unroute('**/fast-results.json');await page.route('**/fast-results.json',r=>r.fulfill({status:404,body:''}))
  await page.reload({waitUntil:'networkidle'});assert.equal(await panel.count(),0)
  assert.deepEqual(errors,[])
  await context.close()
 }
 console.log('Rapid results browser: mobile/desktop provisional, stats, corrected and absent-feed cases passed')
}finally{await browser?.close();try{process.kill(-server.pid,'SIGTERM')}catch{}}
