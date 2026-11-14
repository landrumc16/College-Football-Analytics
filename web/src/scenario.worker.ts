import { simulate } from './scenarios'
self.onmessage=event=>{try{self.postMessage({result:simulate(event.data.input,event.data.overrides,event.data.now)})}catch(error){self.postMessage({error:error instanceof Error?error.message:'Scenario unavailable'})}}
