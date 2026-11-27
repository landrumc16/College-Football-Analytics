import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'
const mod={exports:{}}
vm.runInNewContext(ts.transpileModule(readFileSync('web/src/favoriteDefaults.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:mod.exports})
const {primaryFavorite,defaultSchool,favoriteGame,eligibleSchool,withSchoolAliases,resolveFavoriteSelection:r}=mod.exports
const eligible=['Texas Tech','Baylor','Georgia'], auto={value:null,primary:'Texas Tech'}
assert.equal(primaryFavorite([]),null)
assert.equal(primaryFavorite([null,'Baylor','Texas Tech']),'Baylor')
assert.equal(defaultSchool('Texas Tech',eligible,'Georgia'),'Texas Tech')
assert.equal(defaultSchool('Unknown',eligible,'Georgia'),'Georgia')
assert.equal(defaultSchool(null,eligible,'Georgia'),'Georgia')
assert.equal(r(auto,'Texas Tech',0,0,eligible,'Georgia'),'Texas Tech')
assert.equal(r({value:'Baylor',primary:'Texas Tech'},'Texas Tech',10,0,eligible,'Georgia'),'Baylor')
assert.equal(r({value:'',primary:'Texas Tech'},'Texas Tech',10,0,eligible,'Georgia'),'')
assert.equal(r(auto,'Baylor',3,3,eligible,'Georgia'),'Texas Tech') // active view is stable
assert.equal(r(auto,'Baylor',4,3,eligible,'Georgia'),'Baylor') // subsequent navigation
assert.equal(r({value:'Georgia',primary:'Texas Tech'},'Baylor',3,3,eligible,''),'Georgia')
assert.equal(r({value:'Georgia',primary:'Texas Tech'},'Baylor',4,3,eligible,''),'Baylor')
assert.equal(r(auto,'Texas Tech',0,0,['Baylor'],''),'') // no duplicate comparison opponent
assert.equal(r({value:'Baylor',primary:'Texas Tech'},'Texas Tech',0,0,['Georgia'],''),'')
assert.equal(r({value:'Bay',primary:'Texas Tech'},'Texas Tech',0,0,eligible,'',undefined,true),'Bay')
assert.equal(r(auto,'Texas Tech',0,0,[],''),'') // async eligibility
assert.equal(r(auto,'Texas Tech',0,0,eligible,''),'Texas Tech')
const games=[{game_id:3,home:'Baylor',away:'Georgia',week:14},{game_id:2,home:'Georgia',away:'Texas Tech',week:14},{game_id:1,home:'Texas Tech',away:'Baylor',week:13}]
assert.equal(favoriteGame('Texas Tech',games),'1')
assert.equal(favoriteGame('Unknown',games),'')
assert.equal(favoriteGame(null,games),'')
assert.equal(r(auto,'Texas Tech',0,0,['1','2'],'',favoriteGame('Texas Tech',games)),'1')
assert.equal(r({value:'3',primary:'Texas Tech'},'Texas Tech',5,0,['1','2','3'],'',favoriteGame('Texas Tech',games)),'3')
for(const [canonical,display] of [['Miami (FL)','Miami'],['Appalachian State','App State'],['Sam Houston State','Sam Houston'],['ULM','UL Monroe']]){
 assert.equal(defaultSchool(canonical,[display]),display)
 assert.equal(eligibleSchool(display,[canonical]),canonical)
 assert.ok(withSchoolAliases([canonical]).includes(display))
}
assert.equal(eligibleSchool('Miami (OH)',['Miami']),null)
assert.equal(favoriteGame('Miami (FL)',[{game_id:4,home:'Miami',away:'Baylor'}]),'4')
console.log('Favorite defaults: 37 policy assertions passed')
