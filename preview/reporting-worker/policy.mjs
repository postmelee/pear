// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
export const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const allowed = new Set('reportID userResult macOS chip memoryGiB pear wine dxmt appID gameBuild dateUTC processMinutes observedExit note supplemental'.split(' '));
export function validate(r) {
 if (!r || typeof r!=='object' || Array.isArray(r) || Object.keys(r).some(k=>!allowed.has(k)) || !uuid.test(r.reportID) || !['normal','problems','unknown'].includes(r.userResult)) throw Error('report');
 for(const k of ['memoryGiB','appID','processMinutes']) if(r[k]!==undefined && (!Number.isSafeInteger(r[k]) || r[k]<0 || r[k]>4294967295)) throw Error(k);
 for(const k of [...allowed].filter(k=>!['memoryGiB','appID','processMinutes','supplemental'].includes(k))) if(r[k]!==undefined && (typeof r[k]!=='string' || r[k].length>4000)) throw Error(k);
 if(r.dateUTC!==undefined && !/^\d{4}-\d{2}-\d{2}$/.test(r.dateUTC)) throw Error('date');
 if(r.observedExit!==undefined && !['exited','interrupted','unknown'].includes(r.observedExit)) throw Error('exit');
 if(r.supplemental!==undefined) {
  const s=r.supplemental;
  if(!s || typeof s!=='object' || Array.isArray(s) || Object.keys(s).some(k=>!['furthestResult','activePlayMinutes','input','audio','saveReload','recovery','settings'].includes(k))) throw Error('supplement');
  if(s.furthestResult!==undefined && !['unknown','launch-failed','launched-unusable','menu-interactive','active-gameplay','regression'].includes(s.furthestResult)) throw Error('result');
  for(const k of ['input','audio','saveReload','recovery']) if(s[k]!==undefined && !['unknown','observed','failed','not-tested'].includes(s[k])) throw Error(k);
  if(s.activePlayMinutes!==undefined && (!Number.isSafeInteger(s.activePlayMinutes) || s.activePlayMinutes<0 || s.activePlayMinutes>1440)) throw Error('minutes');
  if(s.settings!==undefined && (typeof s.settings!=='string' || s.settings.length>500)) throw Error('settings');
 }
 return r;
}
export function publicReport(r) { validate(r); const out={};for(const k of allowed) if(k!=='note' && r[k]!==undefined) out[k]=r[k];return out; }
export async function smallText(req,max=16384) {
 const reader=req.body?.getReader();if(!reader)throw Error('body');const chunks=[];let size=0;
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();throw Error('size');}chunks.push(value);}
 const data=new Uint8Array(size);let i=0;for(const c of chunks){data.set(c,i);i+=c.length;}return new TextDecoder('utf-8',{fatal:true}).decode(data);
}
export async function smallJSON(req,max=16384) {
 if(!req.headers.get('content-type')?.startsWith('application/json')) throw Error('type');
 return JSON.parse(await smallText(req,max));
}
export async function digest(value) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(x=>x.toString(16).padStart(2,'0')).join(''); }
export async function sameSecret(a,b) { if(!a||!b)return false;const x=await digest(a),y=await digest(b);let diff=0;for(let i=0;i<x.length;i++)diff|=x.charCodeAt(i)^y.charCodeAt(i);return diff===0; }
export function githubSource(v) {
 if(!v || !['issue','discussion'].includes(v.kind) || typeof v.id!=='string' || !/^[A-Za-z0-9_=-]{1,160}$/.test(v.id) || typeof v.title!=='string' || v.title.length>300 || typeof v.updated!=='string' || !Number.isFinite(Date.parse(v.updated))) throw Error('source');
 const prefix=v.kind==='issue'?'issues':'discussions';if(typeof v.url!=='string'||!new RegExp('^https://github.com/postmelee/pear/'+prefix+'/[1-9][0-9]*$').test(v.url))throw Error('url');
 return {id:v.id,kind:v.kind,url:v.url,title:v.title,updated:v.updated};
}
