const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export function token(){return typeof window!=="undefined"?localStorage.getItem("najm_token"):null}
export async function api<T=any>(path:string,options:RequestInit={}):Promise<T>{const headers=new Headers(options.headers);const t=token();if(t)headers.set("Authorization",`Bearer ${t}`);if(options.body&&!(options.body instanceof FormData))headers.set("Content-Type","application/json");const res=await fetch(API+path,{...options,headers});if(res.status===401&&typeof window!=="undefined"){localStorage.removeItem("najm_token");if(!location.pathname.match(/^\/(login|register)/))location.href="/login"}if(!res.ok){let msg="Unable to complete the request";try{msg=(await res.json()).detail||msg}catch{}throw new Error(msg)}return res.status===204?undefined as T:res.json()}
export const post=(path:string,body:any)=>api(path,{method:"POST",body:body instanceof FormData?body:JSON.stringify(body)});
export const put=(path:string,body:any)=>api(path,{method:"PUT",body:JSON.stringify(body)});
export const del=(path:string)=>api(path,{method:"DELETE"});
export async function apiBlob(path:string):Promise<Blob>{const headers=new Headers(),t=token();if(t)headers.set("Authorization",`Bearer ${t}`);const res=await fetch(API+path,{headers});if(!res.ok)throw new Error("Unable to open this material");return res.blob()}
