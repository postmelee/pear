// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import {uuid,validate,publicReport,smallJSON,smallText,digest,sameSecret,githubSource} from './policy.mjs';
import {reviewer,authRoute} from './auth.mjs';
import {adminPage} from './view.mjs';
const reply=(v,status=200)=>Response.json(v,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const bearer=r=>r.headers.get('authorization')?.match(/^Bearer ([0-9a-f]{64})$/)?.[1];
async function limited(req,env) {
 if(!env.RATE_SALT)return false;
 const now=Math.floor(Date.now()/1000),slot=Math.floor(now/60);
 // Short-lived keyed buckets; never retain raw IPs in application storage/logs.
 const key=await digest(env.RATE_SALT+':'+slot+':'+(req.headers.get('CF-Connecting-IP')||'unknown'));
 const row=await env.DB.prepare('INSERT INTO rate_limits(key,count,expires) VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count').bind(key,now+120).first();return row.count<=20;
}
async function ingest(req,env,id) {
 if(env.INGEST_ENABLED!=='true')return reply({error:'Collection not enabled'},503);
 if(!await limited(req,env))return reply({error:'Try later'},429);
 const cap=bearer(req);if(!cap)return reply({error:'Unauthorized'},401);
 const owner=await digest(cap),now=Date.now();
 if(req.method==='DELETE') {
  const row=await env.DB.prepare('UPDATE reports SET payload=NULL,approved=NULL,published=NULL,state=\'deleted\',deleted=1,updated=? WHERE id=? AND owner=? RETURNING id').bind(now,id,owner).first();
  return row?reply({deleted:true}):reply({error:'Not found'},404);
 }
 if(req.method!=='PUT')return reply({error:'Method'},405);
 const v=await smallJSON(req);
 if(Object.keys(v).sort().join(',')!=='report,requestID,revision,schemaVersion'||v.schemaVersion!==1||!uuid.test(v.requestID)||!Number.isSafeInteger(v.revision)||v.revision<1) return reply({error:'Invalid envelope'},400);
 const report=validate(v.report);if(report.reportID.toLowerCase()!==id)return reply({error:'Identity mismatch'},400);
 report.reportID=id;const payload=JSON.stringify(report);
 await env.DB.prepare(`INSERT INTO reports(id,owner,revision,request_id,payload,updated) VALUES (?,?,?,?,?,?)
 ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,request_id=excluded.request_id,payload=excluded.payload,updated=excluded.updated,state='review',approved=NULL,approved_revision=NULL
 WHERE reports.owner=excluded.owner AND reports.deleted=0 AND excluded.revision>reports.revision`)
 .bind(id,owner,v.revision,v.requestID,payload,now).run();
 const row=await env.DB.prepare('SELECT owner,deleted,revision,request_id,payload FROM reports WHERE id=?').bind(id).first();
 if(row.owner!==owner)return reply({error:'Unauthorized'},403);
 if(row.deleted)return reply({error:'Deleted'},410);
 if(row.revision!==v.revision||row.request_id!==v.requestID||row.payload!==payload)return reply({error:'Stale revision'},409);
 return reply({reportID:id,requestID:v.requestID,revision:v.revision});
}
async function batch(req,env) {
 if(!await sameSecret(bearer(req),env.EXPORT_TOKEN))return reply({error:'Unauthorized'},401);
 const v=await smallJSON(req,1024);if(!uuid.test(v.id)||!['prepare','published'].includes(v.action)||Object.keys(v).sort().join(',')!=='action,id')return reply({error:'Invalid batch'},400);
 let saved=await env.DB.prepare('SELECT * FROM batches WHERE id=?').bind(v.id).first();
 if(v.action==='prepare') {
  if(saved)return reply(JSON.parse(saved.payload));
  const rows=await env.DB.prepare("SELECT id,revision,approved,approved_revision,published,published_revision,state FROM reports WHERE deleted=0 ORDER BY id LIMIT 10001").all();
  if(rows.results.length>10000)return reply({error:'Export capacity'},503);
  const reports=rows.results.flatMap(r=>{const p=r.state==='queued'?r.approved:r.published;return p?[{revision:r.state==='queued'?r.approved_revision:r.published_revision,report:publicReport(JSON.parse(p))}]:[];});
  const value={schemaVersion:1,batchID:v.id,reports};
  await env.DB.prepare('INSERT INTO batches(id,payload,created) VALUES (?,?,?) ON CONFLICT(id) DO NOTHING').bind(v.id,JSON.stringify(value),Date.now()).run();
  saved=await env.DB.prepare('SELECT payload FROM batches WHERE id=?').bind(v.id).first();return reply(JSON.parse(saved.payload));
 }
 if(!saved)return reply({error:'Missing batch'},404);if(saved.published)return reply({published:true});
 const newer=await env.DB.prepare('SELECT id FROM batches WHERE published IS NOT NULL AND created>=?').bind(saved.created).first();if(newer)return reply({error:'Newer batch published'},409);
 await env.DB.batch([
  env.DB.prepare(`UPDATE reports SET published=(SELECT json_extract(value,'$.report') FROM json_each(?,'$.reports') WHERE json_extract(value,'$.report.reportID')=reports.id),
  published_revision=(SELECT json_extract(value,'$.revision') FROM json_each(?,'$.reports') WHERE json_extract(value,'$.report.reportID')=reports.id)
  WHERE deleted=0 AND NOT EXISTS(SELECT 1 FROM batches WHERE published IS NOT NULL AND created>=?)`).bind(saved.payload,saved.payload,saved.created),
  env.DB.prepare("UPDATE reports SET state='published' WHERE state='queued' AND revision=published_revision AND deleted=0 AND NOT EXISTS(SELECT 1 FROM batches WHERE published IS NOT NULL AND created>=?)").bind(saved.created),
  env.DB.prepare('UPDATE batches SET published=? WHERE id=? AND NOT EXISTS(SELECT 1 FROM batches WHERE published IS NOT NULL AND created>=?)').bind(Date.now(),v.id,saved.created)
 ]);
 const receipt=await env.DB.prepare('SELECT published FROM batches WHERE id=?').bind(v.id).first();
 return receipt?.published?reply({published:true}):reply({error:'Newer batch published'},409);
}
async function admin(req,env,url) {
 if(!await reviewer(req,env))return new Response('Administrator sign-in required. <a href="/auth/login">Sign in with GitHub</a>',{status:403,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"}});
 if(req.method==='GET') {
  const tab=['review','queued','published','github'].includes(url.searchParams.get('tab'))?url.searchParams.get('tab'):'review';
  const rows=tab==='github'?(await env.DB.prepare('SELECT * FROM github_sources ORDER BY updated DESC LIMIT 200').all()).results:(await env.DB.prepare('SELECT * FROM reports WHERE state=? AND deleted=0 ORDER BY updated DESC LIMIT 200').bind(tab).all()).results;
  const counts=(await env.DB.prepare('SELECT state,count(*) count FROM reports WHERE deleted=0 GROUP BY state').all()).results;
  return new Response(adminPage(tab,rows,counts),{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"}});
 }
 if(req.method!=='POST'||req.headers.get('Origin')!==url.origin)return reply({error:'Origin'},403);
 if(!req.headers.get('content-type')?.startsWith('application/x-www-form-urlencoded'))return reply({error:'Type'},415);
 const raw=await smallText(req,4096);const v=Object.fromEntries(new URLSearchParams(raw));
 if(v.action==='link') {
  if(!uuid.test(v.reportID))return reply({error:'Report ID required'},400);
  const row=await env.DB.prepare('SELECT id FROM reports WHERE id=? AND deleted=0').bind(v.reportID).first();if(!row)return reply({error:'Unknown report'},404);
  await env.DB.prepare('UPDATE github_sources SET report_id=?,needs_review=0 WHERE id=?').bind(v.reportID,v.sourceID).run();
 } else {
  if(!uuid.test(v.id)||!['approve','unqueue','withdraw'].includes(v.action)||!Number.isSafeInteger(Number(v.revision)))return reply({error:'Invalid decision'},400);
  const row=await env.DB.prepare('SELECT * FROM reports WHERE id=? AND revision=? AND deleted=0').bind(v.id,Number(v.revision)).first();if(!row)return reply({error:'Stale review'},409);
  const pub=publicReport(JSON.parse(row.payload));if(v.action==='approve'&&!pub.appID)return reply({error:'App ID required for catalog'},409);
  const state=v.action==='approve'?'queued':'review';
  const updated=await env.DB.prepare(`UPDATE reports SET state=?,approved=?,approved_revision=?,published=CASE WHEN ?='withdraw' THEN NULL ELSE published END WHERE id=? AND revision=? AND deleted=0 RETURNING id`)
  .bind(state,v.action==='approve'?JSON.stringify(pub):null,v.action==='approve'?row.revision:null,v.action,v.id,row.revision).first();if(!updated)return reply({error:'Stale review'},409);
 }
 const tab=['review','queued','published','github'].includes(v.tab)?v.tab:'review';return new Response(null,{status:303,headers:{Location:'/admin?tab='+tab}});
}
async function github(req,env) {
 if(!await sameSecret(bearer(req),env.IMPORT_TOKEN))return reply({error:'Unauthorized'},401);
 const v=githubSource(await smallJSON(req,4096));
 await env.DB.prepare(`INSERT INTO github_sources(id,kind,url,title,updated) VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,updated=excluded.updated,needs_review=1 WHERE excluded.updated>github_sources.updated`)
 .bind(v.id,v.kind,v.url,v.title,v.updated).run();return reply({stored:true});
}
export default {
 async fetch(req,env) {
  try {
   const url=new URL(req.url);
   if(url.pathname==='/health')return reply({service:'Pear reports',collection:env.INGEST_ENABLED==='true'});
   if(url.pathname.startsWith('/auth/'))return await authRoute(req,env);
   if(url.pathname==='/admin')return await admin(req,env,url);
   if(url.pathname==='/internal/batch'&&req.method==='POST')return await batch(req,env);
   if(url.pathname==='/internal/github'&&req.method==='POST')return await github(req,env);
   const id=url.pathname.match(/^\/reports\/([0-9a-f-]+)$/i)?.[1];if(id&&uuid.test(id))return await ingest(req,env,id.toLowerCase());
   return reply({error:'Not found'},404);
  }catch{return reply({error:'Request rejected'},400);}
 },
 async scheduled(event,env,ctx) {
  // Deleted IDs/capability hashes remain tombstones to reject replayed queues.
  const now=Date.now();ctx.waitUntil(env.DB.batch([
   env.DB.prepare('DELETE FROM oauth_states WHERE expires<?').bind(now),
   env.DB.prepare('DELETE FROM admin_sessions WHERE expires<?').bind(now),
   env.DB.prepare('DELETE FROM rate_limits WHERE expires<?').bind(Math.floor(now/1000)),
   env.DB.prepare("UPDATE reports SET payload=NULL,approved=NULL,published=NULL,deleted=1,state='deleted' WHERE deleted=0 AND updated<? AND (published IS NULL OR updated<?)").bind(now-180*86400000,now-365*86400000),
   env.DB.prepare('DELETE FROM batches WHERE created<?').bind(now-7*86400000)
  ]));
 }
};
