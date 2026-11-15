/** Explicit PostHog capture only: no SDK, autocapture, replay, cookies or person profiles. */
export type Consent = 'off' | 'session' | 'returning'
type Page = { view: string; section: string; profile_section?: string; team?: string; opponent?: string; venue?: string }
type EventName = 'cfa_visit_started' | 'cfa_page_view' | 'cfa_team_profile_opened' | 'cfa_rankings_viewed' | 'cfa_predictions_viewed' | 'cfa_comparison_viewed' | 'cfa_scenario_started' | 'cfa_scenario_completed' | 'cfa_application_error'
const CHOICE='cfba-analytics-choice-v1', VISIT='cfba-analytics-visit-v1', RETURN='cfba-analytics-return-v1'
const DAY=86400000, IDLE=30*60*1000
const views=new Set(['home','predictions','rankings','ap','coaches','stock','profile','compare','programs','hype','trajectory','cfp','conferences','contenders','research','history','methods','sources','validation'])
const sections=new Set(['home','rankings','teams','playoffs','research'])
const profiles=new Set(['overview','schedule','history','card'])
const errors=new Set(['report_unavailable','scenario_unavailable','uncaught_error','unhandled_rejection'])
const key=import.meta.env.VITE_POSTHOG_PUBLIC_KEY || ''
const host=import.meta.env.VITE_POSTHOG_HOST || ''
const configured=/^phc_[a-zA-Z0-9]{10,}$/.test(key) && ['https://us.i.posthog.com','https://eu.i.posthog.com'].includes(host)
const uuid=()=>crypto.randomUUID()
const read=(storage:Storage,name:string)=>{try{return JSON.parse(storage.getItem(name)||'null')}catch{return null}}
const write=(storage:Storage,name:string,value:unknown)=>{try{storage.setItem(name,JSON.stringify(value))}catch{/* Analytics storage is optional. */}}
const remove=(storage:Storage,name:string)=>{try{storage.removeItem(name)}catch{/* App storage must keep working independently. */}}
// Accessing a Storage object itself can throw in restricted browsers.
const storage=(kind:'localStorage'|'sessionStorage')=>{try{return window[kind]}catch{return null}}
const get=(kind:'localStorage'|'sessionStorage',name:string)=>{const s=storage(kind);return s?read(s,name):null}
const put=(kind:'localStorage'|'sessionStorage',name:string,value:unknown)=>{const s=storage(kind);if(s)write(s,name,value)}
const del=(kind:'localStorage'|'sessionStorage',name:string)=>{const s=storage(kind);if(s)remove(s,name)}
const validId=(x:unknown):x is string=>typeof x==='string' && /^[a-f0-9-]{36}$/.test(x)
export function privacyRequested(){return (navigator as Navigator & {globalPrivacyControl?:boolean}).globalPrivacyControl===true || navigator.doNotTrack==='1' || (window as Window & {doNotTrack?:string}).doNotTrack==='1'}
let memoryConsent:Consent|null=null, schools=new Set<string>(), latest:Page={view:'home',section:'home'}
let pageKey='', profileKey='', comparisonKey='', sequence=0, emitted=0
let visit:{id:string;visitor:string;last:number;started:boolean;returning:boolean;scope:Consent}|null=null
let pending:Record<string,unknown>[]=[], timer:ReturnType<typeof setTimeout>|undefined
const activeRuns=new Set<string>()
const inflight=new Set<AbortController>(), errorTimes=new Map<string,number>()
export function analyticsStatus(){
  let mode:Consent='off'
  const saved=get('localStorage',RETURN)
  if(saved && (!validId(saved.id)||!Number.isFinite(saved.expires)||saved.expires<=Date.now()))del('localStorage',RETURN)
  if(privacyRequested()){stop();del('localStorage',RETURN);del('sessionStorage',VISIT);del('sessionStorage',CHOICE);memoryConsent=null}
  else if(get('localStorage',CHOICE)==='off')mode='off'
  else if(memoryConsent)mode=memoryConsent
  else if(saved && validId(saved.id) && saved.expires>Date.now())mode='returning'
  else if(get('sessionStorage',CHOICE)==='session')mode='session'
  return {mode,configured,privacyRequested:privacyRequested()}
}
function stop(){pending=[];clearTimeout(timer);timer=undefined;for(const c of inflight)c.abort();inflight.clear();activeRuns.clear();visit=null;pageKey='';profileKey='';comparisonKey=''}
function allowed(){return configured && !privacyRequested() && analyticsStatus().mode!=='off' && navigator.onLine}
export function setAnalyticsConsent(mode:Consent){
  try{
  if(!['off','session','returning'].includes(mode)||privacyRequested())mode='off'
  stop();memoryConsent=mode;sequence=0;emitted=0
  del('localStorage',RETURN);del('sessionStorage',VISIT);del('sessionStorage',CHOICE)
  put('localStorage',CHOICE,mode)
  if(mode==='session')put('sessionStorage',CHOICE,'session')
  if(mode==='returning'){put('localStorage',RETURN,{id:uuid(),expires:Date.now()+30*DAY,seen:false});memoryConsent=get('localStorage',RETURN)?null:'session'}
  window.dispatchEvent(new Event('cfba-analytics-consent'))
  if(mode!=='off')observePage(latest)
  }catch{stop();memoryConsent='off';del('localStorage',RETURN);del('sessionStorage',VISIT);del('sessionStorage',CHOICE)}
}
function identity(){
  const now=Date.now(),mode=analyticsStatus().mode
  if(visit && now-visit.last<IDLE && visit.scope===mode){visit.last=now;put('sessionStorage',VISIT,visit);return visit}
  const saved=get('sessionStorage',VISIT)
  if(saved && validId(saved.id)&&validId(saved.visitor)&&Number.isFinite(saved.last)&&now-saved.last>=0&&now-saved.last<IDLE&&saved.scope===mode){visit=saved;visit!.last=now;return visit!}
  const returning=get('localStorage',RETURN), persistent=mode==='returning'&&returning&&validId(returning.id)&&returning.expires>now
  const visitId=uuid()
  visit={id:visitId,visitor:persistent?returning.id:visitId,last:now,started:false,returning:Boolean(persistent&&returning.seen),scope:mode}
  if(persistent)put('localStorage',RETURN,{...returning,seen:true})
  put('sessionStorage',VISIT,visit);return visit
}
function common(){
  const v=identity()
  const test=import.meta.env.VITE_POSTHOG_TRAFFIC==='test' || location.hostname!=='landrumc16.github.io' || !location.pathname.startsWith('/College-Football-Analytics/') || new URLSearchParams(location.search).get('analytics_test')==='1'
  return {schema_version:1,traffic_type:test?'test':'beta',device_type:innerWidth<768?'mobile':innerWidth<1024?'tablet':'desktop',display_mode:matchMedia('(display-mode: standalone)').matches?'pwa':'browser',identity_scope:v.scope,return_visit:v.returning,$session_id:v.id,sequence:++sequence,$process_person_profile:false,$geoip_disable:true,$ip:null}
}
function enqueue(event:EventName,properties:Record<string,unknown>){
  if(!allowed() || emitted>=1000 || pending.length>=20)return
  const v=identity();emitted++
  pending.push({event,distinct_id:v.visitor,properties:{...properties,...common(),$insert_id:uuid()},timestamp:new Date().toISOString()})
  if(!timer)timer=setTimeout(flush,400)
}
function capture(event:EventName,properties:Record<string,unknown>={}){
  try{
    if(!allowed())return
    const v=identity()
    if(!v.started){v.started=true;put('sessionStorage',VISIT,v);enqueue('cfa_visit_started',{})}
    enqueue(event,properties)
  }catch{/* No analytics failure may propagate into football functionality. */}
}
function flush(){
  timer=undefined
  try{
    if(!allowed()){pending=[];return}
    const batch=pending;pending=[];if(!batch.length)return
    const controller=new AbortController();inflight.add(controller)
    const timeout=setTimeout(()=>controller.abort(),2500)
    void Promise.resolve().then(()=>fetch(host+'/batch/',{method:'POST',redirect:'error',credentials:'omit',referrerPolicy:'no-referrer',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:key,batch}),signal:controller.signal}))
      .catch(()=>{/* Drop failures; never retry or persist an offline queue. */}).finally(()=>{clearTimeout(timeout);inflight.delete(controller)})
  }catch{/* Includes unavailable fetch and storage APIs. */}
}
export function setAnalyticsSchools(names:string[]){schools=new Set(names.filter(n=>typeof n==='string'))}
export function observePage(page:Page){
  try{
    if(!views.has(page.view)||!sections.has(page.section))return
    latest={view:page.view,section:page.section}
    if(page.profile_section&&profiles.has(page.profile_section))latest.profile_section=page.profile_section
    if(page.team&&schools.has(page.team))latest.team=page.team
    if(page.opponent&&schools.has(page.opponent))latest.opponent=page.opponent
    if(page.venue&&['home','away','neutral'].includes(page.venue))latest.venue=page.venue
    if(!allowed())return
    const next=[latest.view,latest.view==='profile'?latest.team:'',latest.profile_section].join(':')
    if(pageKey!==next){const previous=pageKey.split(':')[0];pageKey=next;capture('cfa_page_view',{...latest,...(views.has(previous)?{previous_view:previous}:{})})
      if(['rankings','ap','coaches','stock'].includes(latest.view))capture('cfa_rankings_viewed',latest)
      if(latest.view==='predictions'||(latest.view==='profile'&&latest.profile_section==='schedule'))capture('cfa_predictions_viewed',latest)
    }
    const p=latest.view==='profile'&&latest.team?latest.team:''
    if(p&&p!==profileKey)capture('cfa_team_profile_opened',{team:p,section:'teams',view:'profile'})
    profileKey=p
    const c=latest.view==='compare'&&latest.team&&latest.opponent&&latest.team!==latest.opponent?[latest.team,latest.opponent,latest.venue].join(':'):''
    if(c&&c!==comparisonKey)capture('cfa_comparison_viewed',latest)
    comparisonKey=c
  }catch{/* Invalid publication data must not make analytics an app dependency. */}
}
export function analyticsError(kind:string){try{if(!errors.has(kind))return;const k=kind+':'+latest.view,now=Date.now();if(now-(errorTimes.get(k)||0)<60000)return;errorTimes.set(k,now);capture('cfa_application_error',{error_kind:kind,view:latest.view,section:latest.section})}catch{/* Never collect exception text or stacks. */}}
export function scenarioStarted(picks:number){try{if(!allowed())return;const id=uuid();activeRuns.add(id);capture('cfa_scenario_started',{run_id:id,picks_count:Math.max(0,Math.min(500,Math.trunc(picks)))});return id}catch{return}}
export function scenarioCompleted(id:string|undefined){if(id&&activeRuns.delete(id))capture('cfa_scenario_completed',{run_id:id})}
window.addEventListener('error',()=>analyticsError('uncaught_error'))
window.addEventListener('unhandledrejection',()=>analyticsError('unhandled_rejection'))
window.addEventListener('offline',()=>{pending=[];clearTimeout(timer);timer=undefined})
window.addEventListener('storage',event=>{if(event.key===RETURN||event.key===CHOICE||event.key===null){memoryConsent=null;stop();if(get('localStorage',CHOICE)==='off'){del('sessionStorage',CHOICE);del('sessionStorage',VISIT)};window.dispatchEvent(new Event('cfba-analytics-consent'))}})
window.addEventListener('pageshow',()=>{if(privacyRequested())analyticsStatus()})
