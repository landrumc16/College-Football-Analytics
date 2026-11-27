import assert from 'node:assert/strict'
import {readFile,writeFile,mkdir} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {chromium} from 'playwright'
import {openDestination,chooseSection,chooseSchool} from './section-navigation.mjs'
import {startAsDeclinedVisitor} from './consent-prompt.mjs'
const port=4396,base=`http://127.0.0.1:${port}/`,out='web/favorite-defaults-evidence'
const report=JSON.parse(await readFile('web/dist/season-report.json','utf8'))
const server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port',String(port),'--strictPort'],{cwd:'web',stdio:'ignore',detached:true})
let browser
const results=[]
async function context(favorites, width=390,standalone=false){
 const ctx=await browser.newContext({viewport:{width,height:900},hasTouch:width<768})
 await ctx.addInitScript(({favorites,standalone})=>{
  if(localStorage.getItem('cfba-favorites-v1')===null)localStorage.setItem('cfba-favorites-v1',JSON.stringify(favorites))
  if(standalone){const original=window.matchMedia.bind(window);window.matchMedia=q=>q==='(display-mode: standalone)'?{...original(q),matches:true,addEventListener(){},removeEventListener(){}}:original(q)}
 },{favorites,standalone})
 return ctx
}
const field=(p,label)=>p.getByLabel(label,{exact:true}).locator('visible=true').first()
async function value(p,label,expected){const f=field(p,label);await f.waitFor();assert.equal(await f.inputValue(),expected,label)}
async function section(p,d,l){await openDestination(p,d);if(l)await chooseSection(p,`${d} sections`,l)}
async function detail(p,text){const summary=p.locator('summary').filter({hasText:text}).first();await summary.waitFor();if(!await summary.evaluate(e=>e.parentElement.open))await summary.click()}
try{
 browser=startAsDeclinedVisitor(await chromium.launch())
 await mkdir(out,{recursive:true})
 for(let i=0;i<50;i++){try{if((await fetch(base)).ok)break}catch{}await new Promise(r=>setTimeout(r,200))}
 // Explicit fallback populations, including a primary that cannot be selected.
 for(const [name,favorites,expected] of [['none',[],report.rankings[0].team],['one',['Texas Tech'],'Texas Tech'],['multiple',['Texas Tech','Baylor'],'Texas Tech'],['empty-first',[null,'Baylor'],'Baylor'],['alias-primary',['Miami (FL)'],'Miami (FL)'],['ineligible',['Not an FBS School','Baylor'],report.rankings[0].team]]){
  const ctx=await context(favorites);const p=await ctx.newPage();await p.clock.setFixedTime(report.retrieved_at);await p.goto(base+'#/profile',{waitUntil:'networkidle'});await value(p,'Choose School',expected)
  await section(p,'Teams','Compare & What If');await value(p,'First School',favorites.includes(expected)?expected:'');await value(p,'Second School','')
  if(name==='alias-primary'){await section(p,'Teams','Offense & Defense');await value(p,'Choose Team','Miami')}
  results.push({case:name,passed:true});await ctx.close()
 }
 for(const width of [375,390,430,768,1536]){
  const ctx=await context(['Texas Tech','Baylor'],width);const p=await ctx.newPage();await p.clock.setFixedTime(report.retrieved_at);const errors=[];p.on('pageerror',e=>errors.push(e.message))
  await p.goto(base,{waitUntil:'networkidle'})
  await section(p,'Teams','Team Profiles');await value(p,'Choose School','Texas Tech')
  await section(p,'Home');await p.getByRole('button',{name:'Open Baylor Team Profile',exact:true}).click();await value(p,'Choose School','Baylor')
  await chooseSchool(p,'Choose School','Baylor');await section(p,'Research','Methodology');await section(p,'Teams','Team Profiles');await value(p,'Choose School','Baylor')
  assert.deepEqual(await p.evaluate(()=>JSON.parse(localStorage.getItem('cfba-favorites-v1'))),['Texas Tech','Baylor',null])
  // A separate tool starts at the favorite, not the unrelated browsed profile.
  await section(p,'Teams','Compare & What If');await value(p,'First School','Texas Tech');await value(p,'Second School','')
  await chooseSchool(p,'Second School','Baylor');await chooseSchool(p,'First School','Baylor');await value(p,'Second School','Texas Tech')
  await p.getByRole('button',{name:'Reset Matchup',exact:true}).click();await value(p,'First School','');await value(p,'Second School','')
  await section(p,'Teams','Offense & Defense');await value(p,'Choose Team','Texas Tech');await value(p,'Choose Opponent','')
  await chooseSchool(p,'Choose Team','Baylor');await value(p,'Choose Opponent','Texas Tech')
  await section(p,'Teams','Model Projections');await value(p,'Find a Team','Texas Tech');await chooseSchool(p,'Find a Team','Baylor')
  await section(p,'Home');await section(p,'Teams','Model Projections');await value(p,'Find a Team','Baylor')
  await section(p,'Rankings','Model Rankings');await value(p,'Find School in Intelligence','Texas Tech');await value(p,'Search teams','')
  assert.equal(await p.locator('.rankings-table tbody tr').count(),report.rankings.length)
  await p.getByRole('button',{name:'All Schools',exact:true}).click();await value(p,'Find School in Intelligence','')
  await section(p,'Teams','Program Directory');await value(p,'Find a program','Texas Tech')
  await section(p,'Teams','Hype Index');await value(p,'Choose Historical Program','Texas Tech')
  await section(p,'Teams','Program Trajectory');await value(p,'Choose Historical Program','Texas Tech')
  const historical=p.locator('details').filter({has:p.locator('summary',{hasText:'Verified Historical Program Development'})}).first()
  if(await historical.count()){await historical.locator(':scope > summary').click();assert.equal(await historical.getByLabel('Choose Historical Program',{exact:true}).inputValue(),'Texas Tech')}
  await section(p,'Research','Market Intelligence');assert.match(await p.locator('.market-selected-game').innerText(),/Texas Tech/)
  assert.equal(await p.getByRole('radio',{name:'Texas Tech',exact:true}).isChecked(),true)
  await p.getByLabel('Find a Game by Team Name',{exact:true}).fill('Georgia');await p.locator('.market-game-results button').first().click()
  const chosen=await p.locator('.market-selected-game').innerText();assert.match(chosen,/Georgia/)
  await section(p,'Home');await section(p,'Research','Market Intelligence');assert.equal(await p.locator('.market-selected-game').innerText(),chosen)
  await section(p,'Playoffs');await p.getByRole('button',{name:'Explore Scenarios',exact:true}).click()
  const match=field(p,'Scenario matchup');await match.waitFor();await p.waitForFunction(()=>document.querySelector('[aria-label="Scenario matchup"]')?.value)
  assert.match(await match.locator('option:checked').innerText(),/Texas Tech/);await value(p,'Scenario winner','') // selecting a game never forces its outcome
  for(const destination of ['Home','Rankings','Teams','Playoffs','Research']){await section(p,destination);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth)<=1)}
  await section(p,'Home');await p.locator('.editorial-favorite-editor > summary').click();await p.getByRole('button',{name:'Remove Texas Tech from favorites',exact:true}).click()
  await section(p,'Teams','Team Profiles');await value(p,'Choose School','Baylor')
  await p.reload({waitUntil:'networkidle'});await value(p,'Choose School','Baylor')
  assert.deepEqual(await p.evaluate(()=>JSON.parse(localStorage.getItem('cfba-favorites-v1'))),[null,'Baylor',null])
  await p.screenshot({path:`${out}/profile-${width}.png`,fullPage:true});assert.deepEqual(errors,[])
  results.push({width,passed:true,errors});await ctx.close()
 }
 // Real cross-tab favorites synchronization: do not disrupt an active explicit choice.
 const ctx=await context(['Texas Tech','Baylor'],390,true);const p=await ctx.newPage();await p.clock.setFixedTime(report.retrieved_at);await p.goto(base+'#/profile',{waitUntil:'networkidle'});await value(p,'Choose School','Texas Tech');await chooseSchool(p,'Choose School','Georgia')
 const other=await ctx.newPage();await other.clock.setFixedTime(report.retrieved_at);await other.goto(base,{waitUntil:'networkidle'});await other.evaluate(()=>localStorage.setItem('cfba-favorites-v1',JSON.stringify(['Baylor','Texas Tech',null])))
 await p.waitForTimeout(200);await value(p,'Choose School','Georgia');await section(p,'Home');await section(p,'Teams','Team Profiles');await value(p,'Choose School','Baylor')
 await p.reload({waitUntil:'networkidle'});await value(p,'Choose School','Baylor');results.push({case:'cross-tab-and-standalone-persistence',passed:true});await ctx.close()
 console.log(JSON.stringify({status:'PASS',results},null,2))
}finally{
 await writeFile(`${out}/results.json`,JSON.stringify({results},null,2));await browser?.close();try{process.kill(-server.pid,'SIGTERM')}catch{}
}
