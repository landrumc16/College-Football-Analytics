import { useEffect, useState } from 'react'
import { analyticsStatus, setAnalyticsConsent, type Consent } from './analytics'
import './analytics-privacy.css'
export default function AnalyticsPrivacy(){
  const [status,setStatus]=useState(analyticsStatus)
  useEffect(()=>{const sync=()=>setStatus(analyticsStatus());const events=['cfba-analytics-consent','pageshow','focus'];for(const event of events)window.addEventListener(event,sync);return()=>{for(const event of events)window.removeEventListener(event,sync)}},[])
  const choose=(mode:Consent)=>{setAnalyticsConsent(mode);setStatus(analyticsStatus())}
  return <details className="install-guide analytics-privacy" aria-label="Optional usage analytics"><summary>Usage analytics: {status.mode==='off'?'off':'on'}</summary><div className="install-guide-content">
    <p>Help improve the fan beta. Share sections and schools opened, comparisons, simulator use and broad error categories with PostHog. This starts only if you allow it.</p>
    <p>No names, email, search text, favorite lists, full URLs, error messages, recordings or automatic click tracking.</p>
    {!status.configured&&<p role="status">Analytics is not configured. No analytics events are being sent.</p>}
    {status.privacyRequested&&<p role="status">Your browser privacy preference blocks analytics (Global Privacy Control or Do Not Track).</p>}
    <div className="analytics-choices">
      <button type="button" disabled={!status.configured||status.privacyRequested||status.mode==='session'} onClick={()=>choose('session')}>Allow this visit only</button>
      <button type="button" disabled={!status.configured||status.privacyRequested||status.mode==='returning'} onClick={()=>choose('returning')}>Allow repeat-visit measurement</button>
      <button type="button" disabled={status.mode==='off'} onClick={()=>choose('off')}>Turn analytics off</button>
    </div>
    <p>Visit-only uses a temporary tab ID. Repeat measurement separately allows a random browser ID for up to 30 days. Neither is linked to an account.</p>
    <details><summary>Privacy details</summary>
      <p>Visit IDs change after 30 minutes of inactivity. Turning analytics off deletes these IDs and stops future collection, but does not erase events already received by PostHog. Your saved teams are unaffected.</p>
      <p>School names come only from published football data. PostHog receives normal network connection information. Counts cover consenting browsers, not every fan.</p>
      <p><a href="https://posthog.com/privacy" target="_blank" rel="noopener noreferrer">PostHog privacy policy</a></p>
    </details>
  </div></details>
}
