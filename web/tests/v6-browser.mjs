import assert from 'node:assert/strict'
import {readFile,mkdir,writeFile} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {setTimeout as delay} from 'node:timers/promises'
import {chromium} from 'playwright'
import ts from 'typescript'
import {chooseSection,assertNavigationFits} from './section-navigation.mjs'
const server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port','4180','--strictPort'],{cwd:'web',stdio:'ignore',detached:true})
const url='http://127.0.0.1:4180/'
let browser,page
await mkdir('web/v6-evidence',{recursive:true})
const results=[]
try {
 for(let i=0;i<40;i++){try{if((await fetch(url)).ok)break}catch{}await delay(500)}
 browser=await chromium.launch({headless:true})
 const source=await readFile('web/src/scenarios.ts','utf8')
 const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText
 const fixture=JSON.parse(await readFile('research/v6/scenario-python-fixtures.json','utf8'))
 for(const width of [375,390,430,768,1536]) {
  const context=await browser.newContext({viewport:{width,height:width===1536?900:844},deviceScaleFactor:1})
  page=await context.newPage();page.setDefaultTimeout(20000)
  const errors=[];page.on('pageerror',e=>errors.push(e.message))
  await page.goto(url,{waitUntil:'networkidle'})
  const nav=page.getByRole('navigation',{name:'Main navigation',exact:true})
  await nav.getByRole('button',{name:'Teams',exact:true}).click()
  await chooseSection(page,'Teams sections','Team Profiles')
  await page.getByLabel('Choose school').selectOption('Texas Tech')
  await chooseSection(page,'Team Profile sections','Historical Intelligence')
  const program=()=>page.getByRole('region',{name:'Program context for Texas Tech',exact:true})
  await program().getByText('FBS win-rate change',{exact:true}).waitFor()
  const metrics=await program().locator('.team-profile-tile strong').allTextContents()
  assert.equal(metrics.length,4);assert.ok(!metrics.includes('Unavailable'))
  await assertNavigationFits(page,'Team Profile sections',width)
  await program().scrollIntoViewIfNeeded()
  await page.screenshot({path:`web/v6-evidence/profile-context-${width}.png`})
  await chooseSection(page,'Teams sections','Program Directory')
  await page.getByLabel('Find a program',{exact:true}).fill('Texas Tech')
  await program().getByText('FBS win-rate change',{exact:true}).waitFor()
  assert.deepEqual(await program().locator('.team-profile-tile strong').allTextContents(),metrics)
  await chooseSection(page,'Teams sections','Compare & What If')
  await page.getByLabel('First school',{exact:true}).selectOption('Texas Tech')
  await page.getByLabel('Second school',{exact:true}).selectOption('Texas A&M')
  await program().getByText('FBS win-rate change',{exact:true}).waitFor()
  assert.deepEqual(await program().locator('.team-profile-tile strong').allTextContents(),metrics)
  await nav.getByRole('button',{name:'Research',exact:true}).click()
  const research=page.getByRole('region',{name:'Experimental prediction research',exact:true})
  await research.getByRole('heading',{name:'Challenger research · incumbent retained'}).waitFor()
  assert.ok((await research.innerText()).includes('3,059'))
  await page.screenshot({path:`web/v6-evidence/research-${width}.png`})
  await nav.getByRole('button',{name:'Playoffs',exact:true}).click()
  const scenario=page.getByRole('region',{name:'Playoff what-if scenarios',exact:true})
  await scenario.getByRole('button',{name:'Explore scenarios',exact:true}).click()
  await page.getByRole('combobox',{name:'Scenario matchup',exact:true}).waitFor()
  await page.waitForFunction(()=>{const s=document.querySelector('select[aria-label="Scenario matchup"]');return s&&!s.disabled})
  const baseline=await scenario.locator('tbody').innerText()
  const input=JSON.parse(await readFile('web/public/v6-scenario-input.json','utf8'))
  const g=input.games.find(g=>g.start_date&&Date.parse(g.start_date)>Date.now()&&g.home==='Army')||input.games.find(g=>g.start_date&&Date.parse(g.start_date)>Date.now())
  assert.ok(g,'Need an actually future scheduled game for scenario acceptance')
  await page.getByRole('combobox',{name:'Scenario matchup',exact:true}).selectOption(String(g.game_id))
  await page.getByRole('combobox',{name:'Scenario winner',exact:true}).selectOption(g.away)
  await page.waitForFunction(()=>{const s=document.querySelector('select[aria-label="Scenario winner"]');return s&&!s.disabled})
  assert.ok((await scenario.getByRole('status').innerText()).includes('1 selected outcomes'))
  await scenario.scrollIntoViewIfNeeded();await page.screenshot({path:`web/v6-evidence/scenario-${width}.png`})
  await scenario.getByRole('button',{name:'Reset to baseline',exact:true}).click()
  await page.waitForFunction(()=>{const s=document.querySelector('select[aria-label="Scenario matchup"]');return s&&!s.disabled})
  assert.equal(await scenario.locator('tbody').innerText(),baseline,'Reset must exactly restore seeded baseline')
  let benchmark=null
  if(width===390){
   const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4})
   benchmark=await page.evaluate(async({js,fixture})=>{const{simulate}=await import('data:text/javascript,'+encodeURIComponent(js));return simulate(fixture.input,{},fixture.now)},{js,fixture})
   await cdp.send('Emulation.setCPUThrottlingRate',{rate:1})
   assert.ok(benchmark.milliseconds<=3000,`Predeclared 4x CPU budget exceeded: ${benchmark.milliseconds} ms`)
   assert.deepEqual(benchmark.teams,fixture.cases[0].teams)
  }
  const scroll=await page.evaluate(()=>({page:document.documentElement.scrollWidth,viewport:innerWidth}))
  assert.ok(scroll.page<=scroll.viewport+1,JSON.stringify(scroll));assert.deepEqual(errors,[])
  results.push({width,crossPageContext:'exact',scenarioReset:'exact',benchmarkMs4x:benchmark?.milliseconds??null,overflow:false,pageErrors:errors})
  await context.close()
 }
 await writeFile('web/v6-evidence/results.json',JSON.stringify(results,null,2)+'\n')
 console.log(JSON.stringify(results))
} catch(error){if(page)await page.screenshot({path:'web/v6-evidence/failure.png',fullPage:true}).catch(()=>{});throw error}
finally {if(browser)await browser.close();try{process.kill(-server.pid,'SIGTERM')}catch{server.kill()}}
