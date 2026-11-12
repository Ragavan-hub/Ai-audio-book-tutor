const BASE=process.env.NEXT_PUBLIC_API_BASE||"http://localhost:8000";
async function call(path:string,init?:RequestInit){const r=await fetch(BASE+path,init);const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||"API request failed");return d}
export const upload=(f:File)=>{const d=new FormData();d.append("file",f);return call("/api/books/upload",{method:"POST",body:d})};
export const page=(id:string,n:number)=>call(`/api/books/${id}/page/${n}`);
export const ask=(book_id:string,question:string,provider:string)=>call("/api/ai/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({book_id,question,provider})});
export const explain=(book_id:string,page:number,style:string,provider:string)=>call("/api/ai/explain",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({book_id,page,style,provider})});
export const speak=(text:string)=>call("/api/audio/speak",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
export const save=(book_id:string,page:number,completed=false)=>call("/api/progress",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({book_id,page,completed})});
