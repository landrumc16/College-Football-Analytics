// One controlled test-tagged journey against an isolated build or the deployed Pages app.
// No raw request/response bodies, token values, browser traces or cookies are logged.
import {mkdir,writeFile} from 'node:fs/promises'
import {spawn} from 'node:child_process'
import {setTimeout as delay} from 'node:timers/promises'
import {chromium} from 'playwright'
import {chooseSection} from './section-navigation.mjs'
import {captureAcknowledgment} from './posthog-capture-response.mjs'
import {answerConsentPrompt} from './consent-prompt.mjs'
const liveUrl=process.env.DASHBOARD_URL
if(liveUrl && liveUrl!=='https://landrumc16.github.io/College-Football-Analytics/')throw Error('Unexpected production verification target')
const origin=liveUrl||'http://127.0.0.1:4193/',endpoint='https://us.i.posthog.com/batch/',out='web/posthog-live-evidence'
const required=['cfa_visit_started','cfa_page_view','cfa_rankings_viewed','cfa_team_profile_opened','cfa_predictions_viewed','cfa_comparison_viewed','cfa_scenario_started','cfa_scenario_completed','cfa_application_error']
const keys=new Set(['view','section','profile_section','team','opponent','venue','previous_view','run_id','picks_count','error_kind','schema_version','traffic_type','device_type','display_mode','identity_scope','return_visit','$session_id','sequence','$process_person_profile','$geoip_disable','$ip','$insert_id'])
const codes=new Set(['missing_secret','invalid_token_shape','unexpected_network_target','invalid_payload','unsafe_properties','credential_header','capture_before_consent','capture_not_accepted','missing_events','duplicate_events','capture_after_opt_out','browser_error'])
const receipt={projectExpected:737110,sourceCommit:process.env.GITHUB_SHA||'local',host:'https://us.i.posthog.com',trafficType:'test',productionDeployed:Boolean(liveUrl),secretValueRecorded:false,personalApiKeyUsed:false,connectionRequired:false,requests:[],status:'FAIL',privateProjectVerification:'Read back the retained session IDs in project 737110; capture acceptance alone does not prove indexing.'}
await mkdir(out,{recursive:true})
const fail=code=>{throw Error(code)}
let browser,server,observed=0;const pending=[],wireFailures=[]
try{
 const token=process.env.VITE_POSTHOG_PUBLIC_KEY||''
 if(!token)fail('missing_secret')
 if(!/^phc_[a-zA-Z0-9]{10,}$/.test(token)||token.trim()!==token)fail('invalid_token_shape')
 receipt.deploymentSecretAccessible=true
 if(!liveUrl)server=spawn('npm',['run','preview','--','--host','127.0.0.1','--port','4193','--strictPort'],{cwd:'web',stdio:'ignore',detached:true})
 for(let i=0;i<40;i++){try{if((await fetch(origin)).ok)break}catch{}await delay(250)}
 browser=await chromium.launch({headless:true})
 const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'})
 await context.route('**/*',async route=>{
  const request=route.request(),url=request.url()
  if(url.startsWith(origin))return route.continue()
  if(url!==endpoint){wireFailures.push('unexpected_network_target');return route.abort()}
  try{
   const body=JSON.parse(request.postData()||'{}'),h=await request.allHeaders()
   if(request.method()!=='POST'||body.api_key!==token||!Array.isArray(body.batch)||!body.batch.length)fail('invalid_payload')
   if(h.cookie||h.authorization||h.referer)fail('credential_header')
   for(const e of body.batch){const p=e.properties||{};if(!required.includes(e.event)||p.traffic_type!=='test'||p.$process_person_profile!==false||p.$geoip_disable!==true||p.$ip!==null||Object.keys(p).some(k=>!keys.has(k)))fail('unsafe_properties')}
   observed++;return route.continue()
  }catch(e){wireFailures.push(codes.has(e.message)?e.message:'invalid_payload');return route.abort()}
 })
 const page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',()=>wireFailures.push('browser_error'))
 page.on('response',r=>{if(r.url()!==endpoint)return;pending.push((async()=>{
  let acknowledgment=captureAcknowledgment(r.status(),null);try{acknowledgment=captureAcknowledgment(r.status(),await r.json())}catch{}
  let events=[];try{events=JSON.parse(r.request().postData()||'{}').batch||[]}catch{}
  receipt.requests.push({httpStatus:r.status(),...acknowledgment,eventCount:events.length,eventNames:events.map(e=>e.event),insertIds:events.map(e=>e.properties?.$insert_id),sessionIds:[...new Set(events.map(e=>e.properties?.$session_id))]})
 })())})
 const nav=name=>page.getByRole('navigation',{name:'Main navigation',exact:true}).getByRole('button',{name,exact:true}).click()
 await page.goto(origin+'?analytics_test=1',{waitUntil:'networkidle'});await page.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor();await delay(500)
 if(observed)fail('capture_before_consent')
 await answerConsentPrompt(page,true);await delay(600)
 await nav('Rankings');await delay(600)
 await nav('Teams');await page.getByLabel('Choose school').selectOption('Texas Tech');await chooseSection(page,'Team Profile sections','Schedule & Predictions');await delay(600)
 await chooseSection(page,'Teams sections','Compare & What If');await page.getByLabel('First school',{exact:true}).selectOption('Texas Tech');await page.getByLabel('Second school',{exact:true}).selectOption('Georgia');await delay(600)
 await nav('Home');await page.getByRole('button',{name:/All games/}).click();await delay(600)
 await nav('Playoffs');await page.getByRole('button',{name:'Explore scenarios',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[aria-label="Scenario matchup"]')?.disabled===false)
 await page.evaluate(()=>window.dispatchEvent(new Event('error')))
 for(let i=0;i<40;i++){await delay(500);await Promise.all([...pending]);const names=new Set(receipt.requests.filter(r=>r.acceptedByCaptureApi).flatMap(r=>r.eventNames));if(required.every(n=>names.has(n)))break}
 await Promise.all([...pending])
 if(wireFailures.length)fail(wireFailures[0])
 if(!receipt.requests.length||receipt.requests.some(r=>!r.acceptedByCaptureApi))fail('capture_not_accepted')
 const names=new Set(receipt.requests.flatMap(r=>r.eventNames));if(!required.every(n=>names.has(n)))fail('missing_events')
 const ids=receipt.requests.flatMap(r=>r.insertIds);if(ids.length!==new Set(ids).size)fail('duplicate_events')
 receipt.sessionIds=[...new Set(receipt.requests.flatMap(r=>r.sessionIds))];receipt.acceptedEventCount=ids.length;receipt.verifiedEventNames=[...names];receipt.duplicateInsertIds=0
 await page.locator('.editorial-menu > summary').click();const privacy=page.locator('.analytics-privacy');if(await privacy.getAttribute('open')===null)await privacy.locator(':scope > summary').click();await page.getByRole('button',{name:'Turn analytics off',exact:true}).click();const before=observed
 await page.locator('.editorial-menu > summary').click();await nav('Home');await nav('Rankings');await delay(900)
 if(observed!==before)fail('capture_after_opt_out')
 if(liveUrl){
  // Verify the genuine fan path without inserting artificial beta traffic.
  const fanContext=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'}),fanTypes=[]
  await fanContext.route('**/*',async route=>{
   const request=route.request()
   if(request.url().startsWith(origin))return route.continue()
   if(request.url()!==endpoint)return route.abort()
   const batch=JSON.parse(request.postData()||'{}').batch||[]
   fanTypes.push(...batch.map(e=>e.properties?.traffic_type))
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({status:'Ok'})})
  })
  const fanPage=await fanContext.newPage()
  await fanPage.goto(origin,{waitUntil:'networkidle'})
  await fanPage.getByRole('heading',{name:'Featured Matchups',exact:true}).waitFor()
  await answerConsentPrompt(fanPage,true)
  await delay(900)
  if(!fanTypes.length||fanTypes.some(type=>type!=='beta'))fail('invalid_payload')
  receipt.betaClassificationVerified=true
  receipt.syntheticBetaEventsDelivered=0
  await fanContext.close()
 }
 receipt.status='PASS';receipt.delivery=liveUrl?'PostHog capture API accepted controlled test events from the deployed Pages application.':'PostHog capture API accepted controlled events from the actual isolated PR build.'
}catch(e){receipt.failure=codes.has(e.message)?e.message:'browser_or_network_verification_failed';process.exitCode=1}
finally{await browser?.close();if(server?.pid)process.kill(-server.pid,'SIGTERM');await writeFile(out+'/delivery.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt,null,2))}
