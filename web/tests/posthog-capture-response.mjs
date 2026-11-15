// Public capture acknowledgments only; never return or log arbitrary response data.
// https://posthog.com/docs/api#responses documents {status: 'Ok'}.
export function captureAcknowledgment(httpStatus,data){
 const object=data!==null&&typeof data==='object'&&!Array.isArray(data)
 const acknowledgment=object&&data.status==='Ok'?'Ok':object&&data.status===1?'legacy-1':'unrecognized'
 const quotaLimited=object&&data.quota_limited!==undefined&&data.quota_limited!==false&&!(Array.isArray(data.quota_limited)&&data.quota_limited.length===0)
 const accepted=httpStatus>=200&&httpStatus<300&&acknowledgment!=='unrecognized'&&!quotaLimited&&!data.error&&!data.errors
 return {acceptedByCaptureApi:Boolean(accepted),acknowledgment,quotaLimited:Boolean(quotaLimited)}
}
