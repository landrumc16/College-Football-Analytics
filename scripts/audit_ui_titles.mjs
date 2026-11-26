/** Source-only UI label audit. --write changes labels, never prose or calculations. */
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'
const require = createRequire(path.resolve('web/package.json'))
const ts = require('typescript')
const module = {exports:{}}
vm.runInNewContext(ts.transpileModule(fs.readFileSync('web/src/titleCase.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:module.exports,Set})
const {titleCase}=module.exports
const tags=new Set(['h1','h2','h3','h4','h5','h6','summary','button','option','label','th','dt','legend','caption'])
const changes=[];let inspected=0
for(const file of fs.readdirSync('web/src').filter(f=>/\.(tsx|ts)$/.test(f))) {
  const filename='web/src/'+file, source=fs.readFileSync(filename,'utf8')
  const root=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true,file.endsWith('tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS)
  const edits=[]
  const add=(start,end,before,after)=>{inspected++;if(before!==after){edits.push({start,end,after});changes.push({file:filename,line:root.getLineAndCharacterOfPosition(start).line+1,before,after})}}
  function visit(n) {
    if(ts.isJsxText(n)&&ts.isJsxElement(n.parent)) {
      const tag=n.parent.openingElement.tagName.getText(root)
      const attr=n.parent.openingElement.attributes.getText(root)
      // Small labels in metric tiles; narrative/sourcing <small> text stays sentence case.
      const metricSmall=tag==='small' && /profile-tile|prediction-metrics|projection-metric|od-summary/.test(n.parent.parent?.getText(root).slice(0,200)??'')
      if((tags.has(tag)||metricSmall)&&n.getText(root).trim()) {
        const siblings=n.parent.children.filter(c=>!ts.isJsxText(c)||c.getText(root).trim())
        const text=n.getText(root)
        add(n.getStart(root),n.end,text,titleCase(text,siblings[0]===n,siblings.at(-1)===n))
      }
    }
    if(ts.isStringLiteral(n)||ts.isNoSubstitutionTemplateLiteral(n)) {
      const p=n.parent
      const property=ts.isPropertyAssignment(p)&&['label','title','heading'].includes(p.name.getText(root))
      const attribute=ts.isJsxAttribute(p)&&['label'].includes(p.name.getText(root))
      const tile=ts.isCallExpression(p)&&p.arguments[0]===n&&/^(tile|stat|metric)$/.test(p.expression.getText(root))
      const expression=ts.isJsxExpression(p)&&ts.isJsxElement(p.parent)&&tags.has(p.parent.openingElement.tagName.getText(root))
      if(property||attribute||tile||expression) {
        const start=n.getStart(root), quote=source[start], before=source.slice(start+1,n.end-1)
        const titled=titleCase(n.text)
        const after=attribute?titleCase(before):titled.replace(/\\/g,'\\\\').replace(quote==='\"'?/\"/g:quote==="'"?/'/g:/`/g, '\\'+quote).replace(/\n/g,'\\n')
        add(start+1,n.end-1,before,after)
      }
    }
    ts.forEachChild(n,visit)
  }
  visit(root)
  if(process.argv.includes('--write')) {let updated=source;for(const e of edits.sort((a,b)=>b.start-a.start))updated=updated.slice(0,e.start)+e.after+updated.slice(e.end);if(updated!==source)fs.writeFileSync(filename,updated)}
}
const report={files_scanned:fs.readdirSync('web/src').filter(f=>/\.(tsx|ts)$/.test(f)).length,labels_inspected:inspected,changes}
if(process.argv.includes('--json')) console.log(JSON.stringify(report,null,2))
else {console.log(`Audited ${report.files_scanned} source files, ${inspected} static labels; ${changes.length} inconsistent labels.`);for(const c of changes)console.log(`${c.file}:${c.line}: ${c.before.trim()} → ${c.after.trim()}`)}
if(process.argv.includes('--check')&&changes.length)process.exitCode=1
