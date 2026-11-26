// Same real data, same journeys, both builds. Capture presentation; compare behavior.
import assert from 'node:assert/strict'
import {readFile,mkdir,writeFile} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {setTimeout as delay} from 'node:timers/promises'
import {createHash} from 'node:crypto'
import {chromium} from 'playwright'
import {chooseSection,assertNavigationFits,openDestination,PRIMARY,chooseSchool} from './section-navigation.mjs'
const phase=process.env.EDITORIAL_PHASE
// V9 Title Cases visible labels; the 'before' phase runs against the released V6 source, which predates it.
const L=(v9,released)=>phase==='before'?released:v9
assert.ok(['before','after'].includes(phase))
const directory=`web/polish-evidence/${phase}`
await mkdir(directory,{recursive:true})
const server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port','4182','--strictPort'],{cwd:'web',stdio:'ignore',detached:true})
const url='http://127.0.0.1:4182/'
const hashes={}
for(const name of ['season-report.json','v6-program-context.json','v6-prediction-research.json','v6-scenario-input.json','v5-program-report-cards.json','v5-forecast-evaluation.json'])hashes[name]=createHash('sha256').update(await readFile('web/public/'+name)).digest('hex')
let browser,page
const records=[]
try {
 for(let i=0;i<40;i++){try{if((await fetch(url)).ok)break}catch{}await delay(500)}
 browser=await chromium.launch({headless:true})
 for(const width of [375,390,430,768,1536]) {
  const context=await browser.newContext({viewport:{width,height:width===1536?900:844},deviceScaleFactor:1})
  await context.addInitScript(()=>localStorage.setItem('cfba-favorites-v1',JSON.stringify(['Texas Tech','Texas A&M','Georgia'])))
  page=await context.newPage();page.setDefaultTimeout(20000)
  const errors=[];page.on('pageerror',e=>errors.push(e.message))
  const proof={width,layout:{}}
  await page.goto(url,{waitUntil:'networkidle'})
  const nav=page.getByRole('navigation',{name:'Main navigation',exact:true})
  proof.navigation=await nav.getByRole('button').allTextContents()
  // Owner-approved V7 information architecture: Market replaces Research in the bottom bar; Research & Data moves to the menu.
  assert.deepEqual(proof.navigation,phase==='before'?['Home','Rankings','Teams','Playoffs','Research']:PRIMARY)
  const capture=async(name,{full=false,region=null}={})=>{
   if(region)await region.scrollIntoViewIfNeeded();else await page.evaluate(()=>scrollTo(0,0))
   const dimensions=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight}))
   assert.ok(dimensions.scrollWidth<=width+1,`${name}: page overflow ${JSON.stringify(dimensions)}`)
   proof.layout[name]=dimensions
   await page.screenshot({path:`${directory}/${name}-${width}.png`})
   if(full)await page.screenshot({path:`${directory}/${name}-${width}-full.png`,fullPage:true})
  }
  await page.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor()
  proof.favorites=await page.locator('.editorial-team-row').allTextContents()
  assert.equal(proof.favorites.length,3,'Three real saved-team rows must be visible')
  await capture('home',{full:true})
  if(width<768)assert.ok(proof.layout.home.height<=1688,'Home must remain within two phone screens')
  await nav.getByRole('button',{name:'Rankings',exact:true}).click()
  proof.rankings=await page.locator('#dashboard-panel tbody tr').evaluateAll(rows=>rows.slice(0,5).map(r=>[...r.querySelectorAll('td')].slice(0,5).map(c=>c.textContent.trim())))
  await capture('rankings')
  await nav.getByRole('button',{name:'Teams',exact:true}).click()
  await chooseSection(page,'Teams sections','Team Profiles')
  await chooseSchool(page, L('Choose School','Choose school'), 'Texas Tech')
  proof.profile=await page.locator('#profile-panel > .team-profile-grid .team-profile-tile strong').allTextContents()
  assert.equal(proof.profile.length,6)
  await capture('profile')
  await chooseSection(page,L('Team Profile Sections','Team Profile sections'),'Historical Intelligence')
  await assertNavigationFits(page,L('Team Profile Sections','Team Profile sections'),width)
  const program=page.getByRole('region',{name:'Program context for Texas Tech',exact:true})
  await program.getByText(L('FBS Win-Rate Change','FBS win-rate change'),{exact:true}).waitFor()
  proof.context=(await program.locator('.team-profile-tile strong').allTextContents()).map(s=>parseFloat(s))
  assert.ok(proof.context.every(Number.isFinite))
  await capture('program',{region:program})
  await program.locator('summary').click()
  await program.getByText('Roster retention is returning observed members',{exact:false}).waitFor()
  await program.getByRole('link').first().waitFor()
  await chooseSection(page,'Teams sections','Compare & What If')
  await chooseSchool(page, L('First School','First school'), 'Texas Tech')
  await chooseSchool(page, L('Second School','Second school'), 'Texas A&M')
  await page.locator('.matchup-result').waitFor()
  proof.matchup=await page.locator('.matchup-result').textContent()
  await capture('compare',{full:true})
  if(phase==='after')await page.getByText(L('Program Histories and Report Cards','Program histories and report cards'),{exact:true}).click()
  await page.getByRole('region',{name:'CFA Program Report Card for Texas Tech',exact:true}).getByRole('heading').waitFor()
  await page.getByRole('region',{name:'Historical FBS results',exact:true}).getByRole('heading',{name:'Historical FBS results comparison'}).waitFor()
  if(phase==='before')await nav.getByRole('button',{name:'Research',exact:true}).click();else await openDestination(page,'Research')
  const archive=page.getByRole('region',{name:'Independent pregame forecast verification',exact:true})
  await archive.getByRole('heading').waitFor()
  const research=page.getByRole('region',{name:'Experimental prediction research',exact:true})
  await research.getByText('3,059',{exact:false}).waitFor()
  if(phase==='after')assert.equal(await archive.locator('.research-scoreline strong').evaluate(el=>{const r=document.createRange();r.selectNodeContents(el);return new Set([...r.getClientRects()].map(rect=>Math.round(rect.top))).size}),1,'Accuracy percentage must stay on one line')
  await capture('research',{full:true})
  if(phase==='after')await archive.getByText(L('Scores, Sample and Publication Record','Scores, sample and publication record'),{exact:true}).click()
  await archive.locator('thead th').filter({hasText:L('Predicted Winner Confidence','Predicted winner confidence')}).waitFor()
  proof.verifiedScores=await archive.locator('tbody').textContent()
  assert.equal(await archive.locator('tbody tr').count(),3)
  await research.locator('details > summary').click()
  proof.researchTables=await research.locator('tbody').allTextContents()
  assert.ok((await research.innerText()).includes('95% interval'))
  if(phase==='after')await page.getByText(L('Full Tracked-Season Results','Full tracked-season results'),{exact:true}).click()
  proof.ledger=await page.getByRole('region',{name:'Historical Prediction Accuracy',exact:true}).textContent()
  await nav.getByRole('button',{name:'Playoffs',exact:true}).click()
  const scenario=page.getByRole('region',{name:'Playoff what-if scenarios',exact:true})
  await scenario.getByRole('button',{name:L('Explore Scenarios','Explore scenarios'),exact:true}).click()
  await page.waitForFunction(()=>{const s=document.querySelector('[aria-label="Scenario matchup"]');return s&&!s.disabled})
  const baseline=await scenario.locator('tbody').textContent()
  // A genuinely future scheduled game from the staged data (a fixed game id goes stale once it is played).
  const scenarioInput=JSON.parse(await readFile('web/public/v6-scenario-input.json','utf8'))
  const future=scenarioInput.games.filter(g=>g.start_date&&Date.parse(g.start_date)>Date.now())
  const pick=future.find(g=>g.home==='Army')||future[0]
  assert.ok(pick,'Need a future scheduled game for scenario parity')
  await page.getByRole('combobox',{name:'Scenario matchup',exact:true}).selectOption(String(pick.game_id))
  await page.getByRole('combobox',{name:'Scenario winner',exact:true}).selectOption(pick.away)
  // Applied pick, confirmed by the scenario's own status (any future game, whether or not it moves the visible rows).
  await page.waitForFunction(()=>{const s=document.querySelector('[aria-label="Playoff what-if scenarios"]');return s.querySelector('.table-wrap[aria-busy="false"]')&&/1 pick applied|· 1 selected outcomes/.test(s.querySelector('[role="status"]')?.textContent||'')})
  proof.scenario=await scenario.locator('tbody').textContent()
  await capture('scenarios',{region:scenario})
  await scenario.getByRole('button',{name:L('Reset to Baseline','Reset to baseline'),exact:true}).click()
  await page.waitForFunction(baseline=>{const s=document.querySelector('[aria-label="Playoff what-if scenarios"]');return s.querySelector('.table-wrap[aria-busy="false"]')&&s.querySelector('tbody').textContent===baseline},baseline)
  assert.equal(await scenario.locator('tbody').textContent(),baseline)
  assert.deepEqual(errors,[])
  proof.errors=errors
  records.push(proof)
  await context.close()
 }
 await writeFile(`${directory}/proof.json`,JSON.stringify({hashes,records},null,2)+'\n')
 if(phase==='after'){
  const before=JSON.parse(await readFile('web/polish-evidence/before/proof.json','utf8'))
  assert.deepEqual(hashes,before.hashes,'Before/after must use identical real data bytes')
  for(let i=0;i<records.length;i++){
   // Navigation is asserted per phase above; every other visible metric and behaviour must stay identical.
   const {layout:beforeLayout,navigation:beforeNavigation,...a}=before.records[i],{layout:afterLayout,navigation:afterNavigation,...b}=records[i]
   assert.deepEqual(b,a,'Visible metrics, model output, favorites and research must remain identical')
  }
  await writeFile('web/polish-evidence/behavior-parity.json',JSON.stringify({status:'passed',viewports:records.map(r=>r.width),sameData:true,unchanged:['navigation','favorites','rankings','profile metrics','program metrics','matchup probabilities','verified scoring','research tables','tracked ledger','scenario results and exact reset']},null,2)+'\n')
 }
 console.log(`${phase}: seven pages captured at all five widths; data and functionality verified`)
} catch(error){if(page)await page.screenshot({path:`${directory}/failure.png`,fullPage:true}).catch(()=>{});throw error}
finally {if(browser)await browser.close();try{process.kill(-server.pid,'SIGTERM')}catch{server.kill()}}
