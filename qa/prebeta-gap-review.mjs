import assert from 'node:assert/strict'
import {readFile,mkdir,writeFile} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {chromium,firefox,webkit} from '../web/node_modules/playwright/index.mjs'
import {chooseSection} from '../web/tests/section-navigation.mjs'
const origin='http://127.0.0.1:4196/',out='qa/evidence',results=[]
await mkdir(out,{recursive:true})
const server=spawn('python',['-m','http.server','4196','--bind','127.0.0.1','--directory','web/dist'],{stdio:'ignore'})
const axe=await readFile('web/node_modules/axe-core/axe.min.js','utf8')
const packet=JSON.parse(await readFile('web/dist/v6-scenario-input.json','utf8'))
const future=packet.games.find(g=>g.start_date&&Date.parse(g.start_date)>Date.now())
const pause=ms=>new Promise(r=>setTimeout(r,ms))
async function scan(p,name,row){
 await p.addScriptTag({content:axe})
 const a=await p.evaluate(async()=>await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}}))
 row.accessibility.push({view:name,violations:a.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,helpUrl:v.helpUrl,nodes:v.nodes.map(n=>({target:n.target,html:n.html,summary:n.failureSummary}))})),incomplete:a.incomplete.map(v=>({id:v.id,nodes:v.nodes.length}))})
}
try{
 for(let i=0;i<40;i++){try{if((await fetch(origin)).ok)break}catch{}await pause(250)}
 for(const [name,type] of Object.entries({chromium,firefox,webkit})){
  let b
  try{
   b=await type.launch({headless:true})
   for(const width of [390,1536]){
    const row={browser:name,version:b.version(),width,status:'FAIL',accessibility:[],errors:[],externalRequests:[],scope:'Exact released artifact; loopback only; no live analytics'}
    results.push(row)
    let c,p
    try{
     c=await b.newContext({viewport:{width,height:width===1536?900:844},deviceScaleFactor:1,serviceWorkers:'block'})
     await c.route('**/*',r=>{if(r.request().url().startsWith(origin))return r.continue();row.externalRequests.push(new URL(r.request().url()).origin);return r.abort()})
     p=await c.newPage();p.setDefaultTimeout(20000);p.on('pageerror',e=>row.errors.push(e.message))
     await p.goto(origin,{waitUntil:'networkidle'})
     await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor()
     await scan(p,'Home',row)
     const nav=p.getByRole('navigation',{name:'Main navigation',exact:true})
     const rankingButton=nav.getByRole('button',{name:'Rankings',exact:true})
     await rankingButton.focus();await p.keyboard.press('Enter')
     await p.getByRole('heading',{name:'Model Rankings',exact:true}).waitFor()
     row.keyboardActivation='PASS'
     await scan(p,'Rankings',row)
     await nav.getByRole('button',{name:'Teams',exact:true}).click()
     await p.getByLabel('Choose school').selectOption('Texas Tech')
     await p.getByRole('heading',{name:'Team Profile',exact:true}).waitFor()
     await scan(p,'Team Profile',row)
     await chooseSection(p,'Team Profile sections','Schedule & Predictions')
     await p.getByRole('heading',{name:'Full Season Schedule and Model Outlook',exact:true}).waitFor()
     await nav.getByRole('button',{name:'Playoffs',exact:true}).click()
     await p.getByRole('button',{name:'Explore scenarios',exact:true}).click()
     await p.waitForFunction(()=>document.querySelector('[aria-label="Scenario matchup"]')?.disabled===false)
     const region=p.getByRole('region',{name:'Playoff what-if scenarios',exact:true}),baseline=await region.locator('tbody').innerText()
     assert.ok(future,'Need a genuinely future matchup')
     await p.getByLabel('Scenario matchup',{exact:true}).selectOption(String(future.game_id))
     await p.getByLabel('Scenario winner',{exact:true}).selectOption(future.away)
     await p.waitForFunction(()=>document.querySelector('[aria-label="Scenario winner"]')?.disabled===false)
     await region.getByRole('button',{name:'Reset to baseline',exact:true}).click()
     await p.waitForFunction(text=>{const s=document.querySelector('[aria-label="Playoff what-if scenarios"]');return s?.querySelector('.table-wrap[aria-busy="false"]')&&s.querySelector('tbody').innerText===text},baseline)
     row.workerAndReset='PASS'
     await scan(p,'Playoff scenario',row)
     await nav.getByRole('button',{name:'Home',exact:true}).click()
     await p.locator('.editorial-menu > summary').click()
     await p.locator('.analytics-privacy > summary').click()
     assert.ok(await p.getByRole('button',{name:'Allow this visit only',exact:true}).isEnabled())
     await scan(p,'Privacy controls open',row)
     await p.locator('.editorial-menu > summary').click()
     row.smallTargets=await p.evaluate(()=>[...document.querySelectorAll('button,a,input,select,summary')].filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width&&r.height&&s.visibility!=='hidden'&&s.display!=='none'}).map(e=>{const r=e.getBoundingClientRect();return {label:(e.getAttribute('aria-label')||e.textContent||e.tagName).trim().slice(0,100),width:r.width,height:r.height}}).filter(e=>e.width<24||e.height<24))
     const focus=[]
     for(let i=0;i<18;i++){
      await p.keyboard.press('Tab')
      focus.push(await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();return {label:(e.getAttribute('aria-label')||e.textContent||e.tagName).trim().slice(0,90),tag:e.tagName,outline:s.outlineStyle,outlineWidth:s.outlineWidth,shadow:s.boxShadow,width:r.width,height:r.height}}))
     }
     row.focusProbe=focus
     await p.evaluate(()=>{const data=[...document.querySelectorAll('body *')].filter(e=>e instanceof HTMLElement&&!['SCRIPT','STYLE'].includes(e.tagName)).map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);for(const [e,size] of data)if(Number.isFinite(size)&&size>0)e.style.fontSize=(size*2)+'px'})
     row.textEnlargement=await p.evaluate(()=>({method:'synthetic computed-font doubling, not native zoom',viewport:innerWidth,pageWidth:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth>innerWidth+1,navButtons:[...document.querySelectorAll('[aria-label="Main navigation"] button')].map(e=>({name:e.textContent,visible:!!e.getBoundingClientRect().width}))}))
     await p.screenshot({path:out+'/'+name+'-'+width+'-text200.png',fullPage:true})
     assert.deepEqual(row.errors,[])
     assert.deepEqual(row.externalRequests,[])
     row.status='PASS'
    }catch(e){row.failure=e.message;if(p)await p.screenshot({path:out+'/'+name+'-'+width+'-failure.png',fullPage:true}).catch(()=>{})}
    finally{await c?.close();await writeFile(out+'/browser-results.json',JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify({browser:name,width,status:row.status,failure:row.failure,axeViolations:row.accessibility.reduce((n,v)=>n+v.violations.length,0),textOverflow:row.textEnlargement?.overflow}))}
   }
  }catch(e){results.push({browser:name,status:'ENVIRONMENT_BLOCKED',failure:e.message})}
  finally{await b?.close()}
 }
}finally{server.kill('SIGTERM');await writeFile(out+'/browser-results.json',JSON.stringify(results,null,2)+'\n')}
console.log('QA_BROWSER_SUMMARY '+JSON.stringify(results.map(r=>({browser:r.browser,width:r.width,status:r.status,failure:r.failure,violations:[...new Set((r.accessibility||[]).flatMap(v=>v.violations.map(a=>a.id)))],smallTargets:r.smallTargets?.length,textOverflow:r.textEnlargement?.overflow}))))
