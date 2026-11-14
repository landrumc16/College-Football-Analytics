// Isolated adversarial verification. This server never binds a public interface.
import assert from 'node:assert/strict'
import {createServer,get} from 'node:http'
import {readFile,mkdir,writeFile} from 'node:fs/promises'
import {resolve,extname} from 'node:path'
import {performance} from 'node:perf_hooks'
import {setTimeout as delay} from 'node:timers/promises'
import {chromium} from 'playwright'
import {chooseSection} from './section-navigation.mjs'
const root=resolve('web/dist'),out='web/adversarial-evidence',url='http://127.0.0.1:4190/'
assert.equal(new URL(url).hostname,'127.0.0.1')
await mkdir(out,{recursive:true})
const realReport=JSON.parse(await readFile(root+'/season-report.json','utf8'))
const realPacket=JSON.parse(await readFile(root+'/v6-scenario-input.json','utf8'))
const realContext=JSON.parse(await readFile(root+'/v6-program-context.json','utf8'))
const records=[],requests=[],mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.webmanifest':'application/manifest+json','.png':'image/png'}
let failJson=false,disconnect=false
const server=createServer(async(req,res)=>{const start=performance.now();try{
 if(disconnect){req.socket.destroy();return}
 const pathname=decodeURIComponent(new URL(req.url,url).pathname),file=resolve(root,'.'+(pathname==='/'?'/index.html':pathname))
 if(!file.startsWith(root+'/')){res.writeHead(403);res.end();return}
 if(failJson&&pathname.endsWith('.json')){res.writeHead(503);res.end('Isolated network fault');return}
 const bytes=await readFile(file);res.writeHead(200,{'Content-Type':mime[extname(file)]||'application/octet-stream','Cache-Control':pathname.endsWith('.json')?'no-store':'no-cache'});res.end(bytes)
 requests.push({path:pathname,ms:performance.now()-start,bytes:bytes.length,status:200})
 }catch{res.writeHead(404);res.end('Not found')}})
await new Promise(r=>server.listen(4190,'127.0.0.1',r))
const browser=await chromium.launch({headless:true})
let activePage,caseName
async function run(name,fn){caseName=name;const start=performance.now();try{const details=await fn();records.push({name,status:'PASS',ms:performance.now()-start,details})}catch(e){records.push({name,status:'FAIL',ms:performance.now()-start,error:e.message,cause:String(e.cause||''),browserErrors:activePage?.errors,stack:e.stack});if(activePage&&!activePage.isClosed())await activePage.screenshot({path:`${out}/${name}.png`,fullPage:true}).catch(()=>{})}finally{console.log(name+': '+records.at(-1).status);activePage=null;await writeFile(out+'/results.json',JSON.stringify(records,null,2))}}
async function context(options={}){const c=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block',...options});await c.route('**/*',route=>{const u=new URL(route.request().url());return ['127.0.0.1','localhost'].includes(u.hostname)?route.continue():route.abort()});return c}
async function pageIn(c){const p=await c.newPage();activePage=p;p.setDefaultTimeout(7000);p.errors=[];p.on('pageerror',e=>p.errors.push(e.message));return p}
async function home(p){await p.goto(url,{waitUntil:'networkidle'});await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor()}
async function nav(p,name){await p.getByRole('navigation',{name:'Main navigation',exact:true}).getByRole('button',{name,exact:true}).click()}
async function healthy(p){assert.deepEqual(p.errors,[],'Uncaught browser errors');assert.ok(await p.getByRole('navigation',{name:'Main navigation',exact:true}).isVisible(),'Navigation vanished');const d=await p.evaluate(()=>({w:innerWidth,scroll:document.documentElement.scrollWidth}));assert.ok(d.scroll<=d.w+1,'Page overflow '+JSON.stringify(d))}
async function withPage(fn,options){const c=await context(options),p=await pageIn(c);try{return await fn(p,c)}catch(e){await p.screenshot({path:`${out}/${caseName}.png`,fullPage:true}).catch(()=>{});throw e}finally{await c.close()}}
try{
 await run('rapid-navigation-search-and-profile',()=>withPage(async p=>{
  await home(p)
  const names=['Home','Rankings','Teams','Playoffs','Research']
  for(let i=0;i<100;i++)await nav(p,names[i%5])
  await nav(p,'Rankings')
  for(const text of ['','Texas Tech','<script>alert(1)</script>','\u0000','🦅'.repeat(500),'x'.repeat(10000),' texas  tech ','Texas A&M','\u202Eabc']){await p.getByLabel('Search teams',{exact:true}).fill(text);await healthy(p)}
  await p.getByLabel('Search teams',{exact:true}).fill('')
  await nav(p,'Teams');await chooseSection(p,'Teams sections','Team Profiles')
  for(let i=0;i<30;i++)await p.getByLabel('Choose school').selectOption(['Texas Tech','Georgia','Texas A&M',''][i%4])
  await p.getByLabel('Choose school').selectOption('Texas Tech')
  for(let i=0;i<16;i++)await chooseSection(p,'Team Profile sections',['Overview','Schedule & Predictions','Historical Intelligence','Program Report Card'][i%4])
  await healthy(p);return {destinationChanges:100,schoolChanges:31,profileChanges:16,searchInputs:9}
 }))
 for(const [label,stored] of [['invalid-json','{'],['wrong-type','42'],['hostile-strings',JSON.stringify(['<img src=x onerror=alert(1)>','🦅'.repeat(500),'Unknown school'])],['mixed-types',JSON.stringify(['Texas Tech',{},null,'Georgia'])]])await run('storage-'+label,()=>withPage(async(p,c)=>{
  await c.addInitScript(s=>localStorage.setItem('cfba-favorites-v1',s),stored);await home(p);await healthy(p);await p.reload({waitUntil:'networkidle'});await healthy(p);return {storedType:label,reload:'recovered'}
 }))
 await run('storage-blocked',()=>withPage(async(p,c)=>{await c.addInitScript(()=>{Storage.prototype.getItem=()=>{throw new DOMException('Blocked','SecurityError')};Storage.prototype.setItem=()=>{throw new DOMException('Quota exceeded','QuotaExceededError')}});await home(p);await healthy(p);await nav(p,'Teams');await healthy(p)}))
 await run('favorite-invalid-save-and-repetition',()=>withPage(async p=>{
  await home(p);await p.locator('.editorial-favorite-editor > summary').click();await p.locator('.favorite-add > summary').click()
  await p.getByLabel('Add favorite team').fill('Not a real school');assert.ok(await p.getByRole('button',{name:'Save Team',exact:true}).isDisabled())
  for(let i=0;i<20;i++){
   const input=p.getByLabel('Add favorite team');await input.fill('Texas Tech');await p.getByRole('button',{name:'Save Team',exact:true}).click();await p.getByRole('button',{name:'Remove Texas Tech from favorites',exact:true}).click()
  }
  await p.getByLabel('Add favorite team').fill('Texas Tech');await p.getByRole('button',{name:'Save Team',exact:true}).click();await p.reload({waitUntil:'networkidle'});assert.equal(await p.locator('.editorial-team-row').count(),1);await healthy(p)
 }))
 await run('favorites-independent-profiles',async()=>{
  const sessions=[]
  try{for(const team of ['Texas Tech','Georgia']){const c=await context();sessions.push(c);const p=await pageIn(c);await home(p);await p.locator('.editorial-favorite-editor > summary').click();await p.locator('.favorite-add > summary').click();await p.getByLabel('Add favorite team').fill(team);await p.getByRole('button',{name:'Save Team',exact:true}).click()}
   for(let i=0;i<sessions.length;i++){const p=sessions[i].pages()[0];await p.reload({waitUntil:'networkidle'});const saved=await p.evaluate(()=>JSON.parse(localStorage.getItem('cfba-favorites-v1')).filter(Boolean));assert.deepEqual(saved,[['Texas Tech','Georgia'][i]]);await healthy(p)}
   return {profiles:2,distinctFavorites:['Texas Tech','Georgia'],reload:'independent'}
  }finally{await Promise.all(sessions.map(c=>c.close()))}
 })
 await run('comparison-empty-same-and-repeated',()=>withPage(async p=>{
  await home(p);await nav(p,'Teams');await chooseSection(p,'Teams sections','Compare & What If')
  for(let i=0;i<30;i++){await p.getByLabel('First school',{exact:true}).selectOption(['','Texas Tech','Georgia'][i%3]);await p.getByLabel('Second school',{exact:true}).selectOption(['Texas Tech','Texas Tech',''][i%3]);await p.getByLabel('Game location',{exact:true}).selectOption(['home','neutral','away'][i%3]);await healthy(p)}
  await p.getByLabel('First school',{exact:true}).selectOption('Texas Tech');await p.getByLabel('Second school',{exact:true}).selectOption('Texas A&M');await p.locator('.matchup-result').waitFor();await healthy(p)
 }))
 await run('predictions-unusual-search-reload',()=>withPage(async p=>{await home(p);await p.getByRole('button',{name:/All games/}).click();for(const s of ['Texas Tech','unknown',"' OR 1=1 --",'🦅'.repeat(300),'']){await p.getByLabel('Search teams',{exact:true}).fill(s);await healthy(p)}await p.reload({waitUntil:'networkidle'});await healthy(p)}))
 await run('scenario-races-unmount-reset',()=>withPage(async p=>{
  await home(p);let workers=0,peak=0;p.on('worker',w=>{workers++;peak=Math.max(peak,workers);w.on('close',()=>workers--)})
  const section=()=>p.getByRole('region',{name:'Playoff what-if scenarios',exact:true})
  for(let i=0;i<8;i++){await nav(p,'Playoffs');await section().getByRole('button',{name:'Explore scenarios',exact:true}).click();await nav(p,'Home')}
  await nav(p,'Playoffs');await section().getByRole('button',{name:'Explore scenarios',exact:true}).click();await p.waitForFunction(()=>document.querySelector('[aria-label="Scenario matchup"]')?.disabled===false)
  const base=await section().locator('tbody').textContent(),g=realPacket.games.find(g=>g.home==='Army'&&g.start_date&&Date.parse(g.start_date)>Date.now())
  assert.ok(g);await p.getByLabel('Scenario matchup',{exact:true}).selectOption(String(g.game_id))
  await p.getByLabel('Scenario winner',{exact:true}).selectOption(g.away);await section().getByRole('button',{name:'Reset to baseline',exact:true}).click();await section().getByRole('button',{name:'Reset to baseline',exact:true}).click()
  await p.waitForFunction(base=>{const r=document.querySelector('[aria-label="Playoff what-if scenarios"]');return r.querySelector('[aria-busy="false"]')&&r.querySelector('tbody').textContent===base},base)
  await nav(p,'Home');await delay(150);assert.equal(workers,0,'Orphaned scenario workers');await healthy(p);return {workerPeak:peak,workersAfterUnmount:workers,reset:'exact'}
 }))
 // Data faults are intercepted only in fresh, isolated browser contexts.
 const faults=[
  {name:'core-404',path:'season-report.json',status:404,body:'',core:true},
  {name:'core-bad-json',path:'season-report.json',body:'{',core:true},
  {name:'core-wrong-shape',path:'season-report.json',body:JSON.stringify({...realReport,rankings:[null]}),core:true},
  {name:'core-empty-rows',path:'season-report.json',body:JSON.stringify({...realReport,rankings:[]}),core:true},
  {name:'core-stale',path:'season-report.json',body:JSON.stringify({...realReport,retrieved_at:'2020-01-01T00:00:00Z'}),stale:true},
  {name:'core-future',path:'season-report.json',body:JSON.stringify({...realReport,retrieved_at:'2030-01-01T00:00:00Z'}),stale:true},
  {name:'program-404',path:'v6-program-context.json',status:404,body:'',program:true},
  {name:'program-wrong-shape',path:'v6-program-context.json',body:JSON.stringify({...realContext,programs:[{team:'Texas Tech',season:2026}]}),program:true},
  {name:'research-wrong-shape',path:'v6-prediction-research.json',body:JSON.stringify({model_status:'experimental_not_promoted',promotion:{incumbent_retained:true},chronological_research:{retrospective:{games:3059}}}),research:true},
  {name:'archive-wrong-shape',path:'v5-forecast-evaluation.json',body:JSON.stringify({status:'independently_verified_published_pregame_subset',models:{workbook_2026_baseline:{games:65}}}),research:true},
  {name:'poll-wrong-shape',path:'poll-snapshot.json',body:JSON.stringify({season:2026,week:11,source:'Isolated test',ap_top25:[null],coaches_top25:[null]}),poll:true},
  {name:'scenario-wrong-hash',path:'v6-scenario-input.json',body:JSON.stringify({...realPacket,report_sha256:'bad'}),scenario:true},
  {name:'scenario-malformed-scale',path:'v6-scenario-input.json',body:JSON.stringify({...realPacket,scale:'bad'}),scenario:true},
  {name:'scenario-malformed-edge',path:'v6-scenario-input.json',body:JSON.stringify({...realPacket,home_edge:null}),scenario:true},
  {name:'scenario-malformed-seed',path:'v6-scenario-input.json',body:JSON.stringify({...realPacket,seed:-1}),scenario:true},
  {name:'scenario-malformed-teams',path:'v6-scenario-input.json',body:JSON.stringify({...realPacket,teams:null}),scenario:true},
 ]
 for(const f of faults)await run('fixture-'+f.name,()=>withPage(async p=>{
  const response=p.waitForResponse(r=>r.url().endsWith('/'+f.path),{timeout:10000})
  let intercept=true;await p.route('**/'+f.path,route=>intercept?route.fulfill({status:f.status||200,contentType:'application/json',body:f.body}):route.continue())
  await p.goto(url,{waitUntil:'networkidle'});await delay(100)
  if(f.program){await nav(p,'Teams');await chooseSection(p,'Teams sections','Team Profiles');await p.getByLabel('Choose school').selectOption('Texas Tech');await chooseSection(p,'Team Profile sections','Historical Intelligence')}
  if(f.research){await nav(p,'Research');await p.waitForLoadState('networkidle')}
  if(f.poll){await nav(p,'Rankings');await p.waitForLoadState('networkidle')}
  await response;await delay(150)
  if(f.scenario){await nav(p,'Playoffs');await p.getByRole('button',{name:'Explore scenarios',exact:true}).click();await delay(900);const r=p.getByRole('region',{name:'Playoff what-if scenarios',exact:true});await r.getByRole('alert').waitFor({timeout:2500});assert.equal(await r.locator('tbody').count(),0,'Invalid packet displayed plausible probabilities')}
  if(f.core&&!f.stale){await p.getByRole('button',{name:'Retry loading data',exact:true}).waitFor({timeout:2500})}
  else{await healthy(p);if(f.stale)assert.ok(/stale|old|out.of.date|refresh|outdated/i.test(await p.locator('body').innerText()),'Missing freshness warning')}
  const errors=[...p.errors];assert.deepEqual(errors,[],'Malformed input crashed the page')
  if(f.name.includes('wrong-shape')||f.name.includes('malformed-scale'))await p.screenshot({path:`${out}/fixture-${f.name}-contained.png`,fullPage:true})
  intercept=false;const retry=p.getByRole('button',{name:'Retry loading data',exact:true});if(await retry.count()){await retry.first().click();await p.waitForLoadState('networkidle');await delay(150);assert.equal(await p.getByText('This section is unavailable',{exact:true}).count(),0,'Section retry did not recover')}await p.reload({waitUntil:'networkidle'});p.errors=[];await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor();await healthy(p)
  return {injectedPath:f.path,payload:f.body.length<400?f.body:'See named mutation in test source',recovery:'healthy after restoring original bytes'}
 }))
 await run('pwa-disconnect-poisoned-cache-recovery',()=>withPage(async(p,c)=>{
  await home(p);await p.evaluate(()=>navigator.serviceWorker.ready);await p.reload({waitUntil:'networkidle'});await p.waitForFunction(()=>!!navigator.serviceWorker.controller)
  await p.evaluate(async()=>{const cache=await caches.open('cfb-shell-v341');await cache.put('./season-report.json',new Response(JSON.stringify({season:1999,rankings:[],predictions:[]})));await cache.put('./index.html',new Response('<h1>STALE CACHE SENTINEL</h1>'))})
  await p.reload({waitUntil:'networkidle'});await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor();assert.ok(!(await p.locator('body').innerText()).includes('STALE CACHE SENTINEL'))
  failJson=true;await p.reload({waitUntil:'networkidle'});await p.getByRole('button',{name:'Retry loading data',exact:true}).waitFor();failJson=false;await p.getByRole('button',{name:'Retry loading data',exact:true}).click();await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor()
  disconnect=true;await p.reload({waitUntil:'load'});await p.getByRole('heading',{name:'You are offline',exact:true}).waitFor();disconnect=false;await p.getByRole('link',{name:'Try again',exact:true}).click();await p.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor();await healthy(p)
 },{serviceWorkers:'allow'}));failJson=false;disconnect=false
 await run('memory-navigation-worker-soak',()=>withPage(async(p,c)=>{
  await home(p);const cdp=await c.newCDPSession(p);await cdp.send('Performance.enable');const readings=[]
  for(let batch=0;batch<4;batch++){
   for(let i=0;i<20;i++){await nav(p,['Rankings','Teams','Research','Playoffs','Home'][i%5])}
   await cdp.send('HeapProfiler.collectGarbage');await delay(100);const metrics=await cdp.send('Performance.getMetrics');readings.push(Object.fromEntries(metrics.metrics.filter(x=>['JSHeapUsedSize','Nodes','Documents'].includes(x.name)).map(x=>[x.name,x.value])))
  }
  const growth=readings.at(-1).JSHeapUsedSize-readings[0].JSHeapUsedSize;assert.ok(growth<32*1024*1024,'Retained heap grew more than 32 MiB after GC');assert.ok(readings.at(-1).JSHeapUsedSize-readings.at(-2).JSHeapUsedSize<12*1024*1024,'Late retained heap growth exceeds 12 MiB');await healthy(p);return {cycles:80,gcReadings:readings,retainedGrowthBytes:growth,conditions:'single page, forced GC checkpoints; not device-wide memory'}
 }))
 // Visitors and request bursts target only the isolated loopback server.
 for(const count of [1,10,25,50])await run('concurrent-visitors-'+count,async()=>{
  const start=performance.now(),begin=requests.length;const sessions=[]
  try{await Promise.all(Array.from({length:count},async(_,i)=>{
   const c=await context({viewport:{width:[375,390,430,768,1536][i%5],height:844}});sessions.push(c);const p=await c.newPage();p.setDefaultTimeout(60000);p.errors=[];p.on('pageerror',e=>p.errors.push(e.message));await home(p);await nav(p,'Rankings');await p.getByLabel('Search teams',{exact:true}).fill(i%2?'Texas Tech':'Georgia');await nav(p,'Teams');await chooseSection(p,'Teams sections','Team Profiles');await p.getByLabel('Choose school').selectOption('Texas Tech');await healthy(p)
   if(i%10===0){await nav(p,'Playoffs');await p.getByRole('button',{name:'Explore scenarios',exact:true}).click();await p.waitForFunction(()=>document.querySelector('[aria-label="Scenario matchup"]')?.disabled===false,{},{timeout:60000});await healthy(p)}
  }));return {visitors:count,elapsedMs:performance.now()-start,servedRequests:requests.length-begin,conditions:'one Chromium process, independent browser contexts, 10% run 2000-draw scenarios; isolated static server, no public traffic'}}finally{await Promise.all(sessions.map(c=>c.close()))}
 })
 await run('repeated-local-requests',async()=>{
  const timings=[],errors=[],start=performance.now();let issued=0
  await Promise.all(Array.from({length:25},async()=>{while(issued<1000){const i=issued++,t=performance.now();const status=await new Promise((resolve,reject)=>{const req=get(url+['','season-report.json','poll-snapshot.json','v6-scenario-input.json'][i%4],{agent:false},res=>{res.resume();res.on('end',()=>resolve(res.statusCode));res.on('error',reject)});req.setTimeout(10000,()=>req.destroy(Error('Local request timed out')));req.on('error',reject)});if(status!==200)errors.push(status);timings.push(performance.now()-t)}}));timings.sort((a,b)=>a-b);assert.deepEqual(errors,[]);return {requests:1000,concurrency:25,elapsedMs:performance.now()-start,p50Ms:timings[Math.floor(timings.length*.5)],p95Ms:timings[Math.floor(timings.length*.95)],p99Ms:timings[Math.floor(timings.length*.99)],errors,publicRequests:0}
 })
}finally{await browser.close();await new Promise(r=>server.close(r));await writeFile(out+'/results.json',JSON.stringify({productionCommit:'2c47bec5935fd32844ef20c307e3aab4c201d052',candidateCommit:process.env.CANDIDATE_SHA||null,artifactRun:43649840894,conditions:{origin:url,network:'loopback only; external browser requests aborted',fixtures:'isolated interception, never live data',heapGrowthLimitMiB:32,lateHeapLimitMiB:12},records,summary:{pass:records.filter(r=>r.status==='PASS').length,fail:records.filter(r=>r.status==='FAIL').length}},null,2)+'\n')}
console.log(JSON.stringify(records.map(r=>({name:r.name,status:r.status,error:r.error})),null,2));if(records.some(r=>r.status==='FAIL'))process.exitCode=1
