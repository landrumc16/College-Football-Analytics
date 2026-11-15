import assert from 'node:assert/strict'
import {test} from 'node:test'
import {captureAcknowledgment} from './posthog-capture-response.mjs'

test('recognizes documented and legacy acknowledgments',()=>{
 assert.deepEqual(captureAcknowledgment(200,{status:'Ok'}),{acceptedByCaptureApi:true,acknowledgment:'Ok',quotaLimited:false})
 assert.equal(captureAcknowledgment(200,{status:1}).acceptedByCaptureApi,true)
 assert.equal(captureAcknowledgment(200,{status:'Ok',quota_limited:[]}).acceptedByCaptureApi,true)
})
test('HTTP errors, quota limits, malformed and unknown replies fail closed',()=>{
 for(const status of [400,401,429,500])assert.equal(captureAcknowledgment(status,{status:'Ok'}).acceptedByCaptureApi,false)
 for(const data of [null,1,'Ok',[],{}, {status:0},{status:'error'},{status:'Ok',error:'rejected'},{status:'Ok',errors:['rejected']},{status:'Ok',quota_limited:['events']},{status:'Ok',quota_limited:true}])assert.equal(captureAcknowledgment(200,data).acceptedByCaptureApi,false)
})
test('diagnostics never retain arbitrary response fields',()=>{
 const safe=captureAcknowledgment(200,{status:'Ok',detail:'DO_NOT_RECORD',token:'DO_NOT_RECORD'})
 assert.ok(!JSON.stringify(safe).includes('DO_NOT_RECORD'))
})
