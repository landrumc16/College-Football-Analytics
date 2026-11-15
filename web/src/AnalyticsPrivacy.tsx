import { useEffect, useState } from 'react'
import { analyticsStatus, setAnalyticsConsent, type Consent } from './analytics'
export default function AnalyticsPrivacy(){
  const [status,setStatus]=useState(analyticsStatus)
  useEffect(()=>{const sync=()=>setStatus(analyticsStatus());const events=['cfba-analytics-consent','pageshow','focus'];for(const event of events)window.addEventListener(event,sync);return()=>{for(const event of events)window.removeEventListener(event,sync)}},[])
  const choose=(mode:Consent)=>{setAnalyticsConsent(mode);setStatus(analyticsStatus())}
  return <details className="install-guide" aria-label="Optional usage analytics"><summary>Usage analytics: {status.mode==='off'?'off':'on'}</summary><div className="install-guide-content">
    <p>Help improve the fan beta by sharing which sections and schools you open, comparisons, simulator use and broad error categories with PostHog. This is optional and starts only with your permission.</p>
    <p>No names, email, search text, favorite lists, full URLs, exception messages, recordings or automatic click capture are sent. School names come only from published football data. PostHog receives normal network connection information. Counts cover consenting browsers, not every fan.</p>
    <p>This visit uses a random browser-tab identifier, expiring after 30 minutes of inactivity. Repeat-visit measurement separately allows a random identifier in this browser for up to 30 days. It is never linked to an account. Turning analytics off deletes these identifiers; it does not erase events already received by PostHog. Your saved teams are unaffected.</p>
    {!status.configured&&<p role="status">Analytics is not configured. No analytics events are being sent.</p>}
    {status.privacyRequested&&<p role="status">Your browser privacy preference blocks analytics (Global Privacy Control or Do Not Track).</p>}
    <button type="button" disabled={!status.configured||status.privacyRequested||status.mode==='session'} onClick={()=>choose('session')}>Allow this visit only</button>{' '}
    <button type="button" disabled={!status.configured||status.privacyRequested||status.mode==='returning'} onClick={()=>choose('returning')}>Allow repeat-visit measurement</button>{' '}
    <button type="button" disabled={status.mode==='off'} onClick={()=>choose('off')}>Turn analytics off</button>
    <p><a href="https://posthog.com/privacy" target="_blank" rel="noopener noreferrer">PostHog privacy policy</a></p>
  </div></details>
}
