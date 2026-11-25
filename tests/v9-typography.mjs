import assert from 'node:assert/strict'
import fs from 'node:fs'
import { createHash } from 'node:crypto'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'
import { execFileSync } from 'node:child_process'
const require=createRequire(path.resolve('web/package.json')),ts=require('typescript')
const module={exports:{}}
vm.runInNewContext(ts.transpileModule(fs.readFileSync('web/src/titleCase.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:module.exports,Set})
const {titleCase}=module.exports
const examples=[
 ['How good is this team?','How Good Is This Team?'],
 ['offense and defense','Offense and Defense'],
 ['a guide to the CFP','A Guide to the CFP'],
 ['what this means for AP, FBS and PWA','What This Means for AP, FBS and PWA'],
 ['opponent-adjusted performance','Opponent-Adjusted Performance'],
 ['playoff what-if','Playoff What-If'],
 ['EPA/play','EPA/play'],
 ['McNeese and UConn','McNeese and UConn'],
 ['Miami (FL)','Miami (FL)'],
 ['Offense &amp; Defense','Offense &amp; Defense'],
 ['SCENARIO SNAPSHOT','Scenario Snapshot'],
 ['THE CFP AND THE AP POLL','The CFP and the AP Poll'],
 ['SP+ and FPI','SP+ and FPI'],
 ['what’s changing at Texas Tech','What’s Changing at Texas Tech'],
 ['standings: the next game','Standings: The Next Game'],
 ['the team we root for','The Team We Root For'],
]
for(const [input,expected] of examples){assert.equal(titleCase(input),expected);assert.equal(titleCase(expected),expected)}
for (const {team} of JSON.parse(fs.readFileSync('data/season-2026-report.json','utf8')).rankings) assert.equal(titleCase(team),team)
assert.equal(titleCase(' and ',false,false),' and ')
assert.equal(titleCase(' vs ',false,false),' vs ')
// Descriptive paragraphs must remain byte-for-byte sentence case through the audit.
const paragraphs=source=>{const r=ts.createSourceFile('view.tsx',source,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX),out=[];function walk(n){if(ts.isJsxText(n)&&ts.isJsxElement(n.parent)&&n.parent.openingElement.tagName.getText(r)==='p')out.push(n.getText(r));ts.forEachChild(n,walk)}walk(r);return out}
const proseBaseline=JSON.parse(fs.readFileSync('docs/evidence/v9/sentence-case-prose.json','utf8'))
for(const [file,expected] of Object.entries(proseBaseline)) {
  const actual=paragraphs(fs.readFileSync('web/src/'+file,'utf8')).filter(text=>text.trim()).map(text=>createHash('sha256').update(text).digest('hex'))
  let cursor=0
  for(const hash of expected){const position=actual.indexOf(hash,cursor);assert.ok(position>=0,file+' existing paragraph text changed');cursor=position+1}
}
const dir=fs.mkdtempSync(path.resolve('web/node_modules/.v9-typography-'))
try {
  execFileSync('web/node_modules/.bin/esbuild',['web/src/StatExplain.tsx','--bundle','--platform=node','--format=cjs','--external:react','--loader:.css=empty',`--outfile=${dir}/explain.cjs`],{stdio:'pipe'})
  const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),{StatExplain}=require(dir+'/explain.cjs')
  const paragraph='Texas Tech is playing better lately, but three games do not establish why.'
  const html=renderToStaticMarkup(React.createElement(StatExplain,{label:'what do these numbers mean?'},React.createElement('p',null,paragraph)))
  assert.ok(html.includes('<summary>What Do These Numbers Mean?</summary>'))
  assert.ok(html.includes(`<p>${paragraph}</p>`));assert.ok(!html.includes(' open'))
} finally {fs.rmSync(dir,{recursive:true,force:true})}
execFileSync('node',['scripts/audit_ui_titles.mjs','--check'],{stdio:'inherit'})
console.log('Title Case conventions, acronym/identity preservation, collapsed explanations and untouched prose passed.')
