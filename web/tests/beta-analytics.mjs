import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {setTimeout as delay} from 'node:timers/promises'
import {chromium} from 'playwright'
import {chooseSection} from './section-navigation.mjs'
const url='http://127.0.0.1:4189/',out='web/analytics-evidence'
await mkdir(out,{recursive:true})
const server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port','4189','--strictPort'],{cwd:'web',stdio:'ignore',detached:true})
let browser;const results=[]
const nav=(p,name)=>p.getByRole('navigation',{name:'Main navigation',exact:true}).getByRole('button',{name,exact:true}).click()
async function settings(p){const menu=p.locator('.editorial-menu');if(await menu.getAttribute('open')===null)await menu.locator(':scope > summary').click();const privacy=p.getByRole('group',{name:'Optional usage analytics',exact:true});if(await privacy.getAttribute('open')===null)await privacy.locator('summary').click()}
async function fits(p){assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Page overflow')}
const endpoint='https://us.i.posthog.com/batch/'
try{
 for(let i=0;i<40;i++){try{if((await fetch(url)).ok)break}catch{}await delay(250)}
 browser=await chromium.launch({headless:true})
 for(const width of [375,390,430,768,1536]){
  const c=await browser.newContext({viewport:{width,height:844},serviceWorkers:'block'}),packets=[],unexpected=[]
  await c.route('**/*',r=>{const u=r.request().url();if(u===endpoint){packets.push(JSON.parse(r.request().postData()));return r.fulfill({status:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:'{"status":1}'})}if(u.startsWith(url))return r.continue();unexpected.push(u);return r.abort()})
  const p=await c.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));p.setDefaultTimeout(15000)
  await p.goto(url,{waitUntil:'networkidle'});await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor();await nav(p,'Rankings');await nav(p,'Home');await delay(500);assert.equal(packets.length,0,'Events before consent')
  await settings(p);await fits(p);await p.screenshot({path:`${out}/privacy-${width}.png`,fullPage:true});await p.getByRole('button',{name:'Allow this visit only',exact:true}).click();await delay(600);await p.locator('.editorial-menu > summary').click()
  const es=()=>packets.flatMap(p=>p.batch)
  assert.equal(es().filter(e=>e.event==='cfa_visit_started').length,1);assert.equal(es().filter(e=>e.event==='cfa_page_view').length,1)
  await nav(p,'Rankings');await nav(p,'Rankings');await p.getByLabel('Search teams',{exact:true}).fill('private@example.com');await delay(600);assert.equal(es().filter(e=>e.event==='cfa_rankings_viewed').length,1)
  await nav(p,'Teams');await p.getByLabel('Choose school').selectOption('Texas Tech');await chooseSection(p,'Team Profile sections','Schedule & Predictions');await chooseSection(p,'Team Profile sections','Historical Intelligence');await p.getByRole('region',{name:'Program context for Texas Tech',exact:true}).getByText('FBS win-rate change',{exact:true}).waitFor();await fits(p)
  await chooseSection(p,'Teams sections','Compare & What If');await p.getByLabel('First school',{exact:true}).selectOption('Texas Tech');await p.getByLabel('Second school',{exact:true}).selectOption('Georgia');await p.getByLabel('Game location',{exact:true}).selectOption('neutral');await delay(600)
  assert.ok(es().some(e=>e.event==='cfa_comparison_viewed'&&e.properties.team==='Texas Tech'&&e.properties.opponent==='Georgia'))
  await nav(p,'Home');await p.getByRole('button',{name:/All games/}).click();await p.locator('.prediction-card').first().waitFor();await nav(p,'Playoffs');await p.getByRole('button',{name:'Explore scenarios',exact:true}).click();await p.waitForFunction(()=>document.querySelector('[aria-label="Scenario matchup"]')?.disabled===false)
  await delay(600);const starts=es().filter(e=>e.event==='cfa_scenario_started'),completed=es().filter(e=>e.event==='cfa_scenario_completed');assert.equal(starts.length,1);assert.equal(completed.length,1);assert.equal(starts[0].properties.run_id,completed[0].properties.run_id)
  await p.evaluate(()=>window.dispatchEvent(new ErrorEvent('error',{message:'private@example.com secret query',filename:'https://example.com/?token=SECRET'})));await delay(600)
  assert.ok(es().some(e=>e.event==='cfa_application_error'&&e.properties.error_kind==='uncaught_error'))
  const serialized=JSON.stringify(packets);for(const privateText of ['private@example.com','SECRET','favorite','query','filename','stack'])assert.ok(!serialized.includes(privateText),privateText)
  const allowedKeys=new Set(['view','section','profile_section','team','opponent','venue','previous_view','run_id','picks_count','error_kind','schema_version','traffic_type','device_type','display_mode','identity_scope','return_visit','$session_id','sequence','$process_person_profile','$geoip_disable','$ip','$insert_id'])
  const ids=new Set();for(const e of es()){assert.ok(!ids.has(e.properties.$insert_id),'Duplicate insert ID');ids.add(e.properties.$insert_id);assert.equal(e.properties.traffic_type,'test');assert.equal(e.properties.$process_person_profile,false);assert.equal(e.properties.$ip,null);for(const k of Object.keys(e.properties))assert.ok(allowedKeys.has(k),k)}
  await settings(p);await p.getByRole('button',{name:'Turn analytics off',exact:true}).click();const count=packets.length;await p.locator('.editorial-menu > summary').click();await nav(p,'Teams');await nav(p,'Home');await delay(700);assert.equal(packets.length,count,'Events after opt-out');assert.equal(await p.evaluate(()=>sessionStorage.getItem('cfba-analytics-visit-v1')),null)
  assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);await fits(p);await p.screenshot({path:`${out}/home-${width}.png`,fullPage:true});results.push({width,status:'PASS',events:es().length,started:starts.length,completed:completed.length,duplicates:0,unintendedRequests:0});await c.close()
 }
 // Browser-level DNT/GPC and offline interruption; no live PostHog request can escape.
 for(const preference of ['gpc','dnt']){const c=await browser.newContext({serviceWorkers:'block'}),packets=[];await c.addInitScript(pref=>Object.defineProperty(navigator,pref==='gpc'?'globalPrivacyControl':'doNotTrack',{value:pref==='gpc'?true:'1',configurable:true}),preference);await c.route(endpoint,r=>{packets.push(r.request().postData());return r.abort()});const p=await c.newPage();await p.goto(url,{waitUntil:'networkidle'});await settings(p);assert.ok(await p.getByRole('button',{name:'Allow this visit only',exact:true}).isDisabled());assert.ok(await p.getByText('Your browser privacy preference blocks analytics',{exact:false}).isVisible());await nav(p,'Rankings');await delay(600);assert.equal(packets.length,0);results.push({privacy:preference,status:'PASS',events:0});await c.close()}
 const c=await browser.newContext({serviceWorkers:'block'}),p=await c.newPage(),requests=[]
 await c.route(endpoint,async r=>{requests.push(r.request().postData());await delay(4000);await r.abort().catch(()=>{})})
 await p.goto(url,{waitUntil:'networkidle'});await settings(p);const stalled=p.waitForRequest(endpoint);await p.getByRole('button',{name:'Allow this visit only',exact:true}).click();await stalled;await p.locator('.editorial-menu > summary').click();const begin=performance.now();await nav(p,'Rankings');await p.getByRole('heading',{name:'Model Rankings',exact:true}).waitFor();const latency=performance.now()-begin;assert.ok(latency<2000,'UI waited for analytics');await c.setOffline(true);await nav(p,'Teams');await delay(500);await c.setOffline(false);await nav(p,'Home');await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor();await fits(p);results.push({failureIsolation:'stalled transport and offline navigation',status:'PASS',navigationMs:latency});await c.close()
 console.log(JSON.stringify(results,null,2));await writeFile(out+'/results.json',JSON.stringify({status:'PASS',traffic:'test, intercepted; no live ingestion claimed',results},null,2)+'\n')
}finally{await browser?.close();process.kill(-server.pid,'SIGTERM')}
