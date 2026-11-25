/** Build the real React app with offline V9 evidence; never fetches CFBD or deploys. */
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'v9-preview-'))
try {
  execFileSync('node', ['scripts/v9_intelligence.mjs', temporary], {stdio:'inherit'})
  execFileSync('python', ['-m','scripts.v9_scenario_packet','--report','data/season-2026-report.json','--games','data/cfbd-2026-games.json','--output',`${temporary}/v6-scenario-input.json`], {stdio:'inherit'})
  execFileSync('python', ['-m','scripts.v9_accountability','--output',`${temporary}/v9-accountability.json`], {stdio:'inherit'})
  execFileSync('npm', ['run','build','--prefix','web'], {stdio:'inherit', env:{...process.env,VITE_POSTHOG_PUBLIC_KEY:'',VITE_POSTHOG_HOST:''}})
  for (const [source,target] of [['data/season-2026-report.json','season-report.json'],['data/poll-2026-snapshot.json','poll-snapshot.json'],['data/v2-research-summary.json','v2-research-summary.json']]) fs.copyFileSync(source, `web/dist/${target}`)
  fs.copyFileSync(`${temporary}/v9-accountability.json`, 'web/dist/v9-accountability.json')
  fs.copyFileSync(`${temporary}/team-intelligence.json`, 'web/dist/team-intelligence.json')
  fs.copyFileSync(`${temporary}/v6-scenario-input.json`, 'web/dist/v6-scenario-input.json')
  console.log('Offline V9 review build ready in web/dist. Analytics disabled; no deployment performed.')
} finally {fs.rmSync(temporary,{recursive:true,force:true})}
