// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import test from 'node:test';import assert from 'node:assert/strict';
import {validate,publicReport,githubSource,sameSecret,smallJSON} from './policy.mjs';
import {reviewer,authRoute} from './auth.mjs';import worker from './worker.mjs';
const r={reportID:'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',userResult:'normal',appID:3405340,note:'PRIVATE',supplemental:{input:'unknown'}};
test('strict projection keeps observation separate and private notes excluded',()=>{assert.equal(publicReport(r).note,undefined);assert.equal(publicReport(r).supplemental.input,'unknown');assert.throws(()=>validate({...r,account:'secret'}));assert.throws(()=>validate({...r,processMinutes:'20'}));assert.throws(()=>validate({...r,supplemental:{activePlayMinutes:-1}}));});
test('bounded streaming request',async()=>{await assert.rejects(()=>smallJSON(new Request('https://test',{method:'POST',headers:{'Content-Type':'application/json'},body:'x'.repeat(20000)})));});
test('source linking only admits canonical Pear issues/discussions',()=>{const v={id:'I_123',kind:'issue',url:'https://github.com/postmelee/pear/issues/63',title:'Example',updated:'2026-10-18T00:00:00Z'};assert.equal(githubSource(v).id,'I_123');assert.throws(()=>githubSource({...v,url:'https://evil.test'}));});
test('admin fails closed without configuration and with spoofed identity header',async()=>{assert.equal(await reviewer(new Request('https://test/admin',{headers:{'Cf-Access-Authenticated-User-Email':'owner@example.com'}}),{}),false);assert.equal((await worker.fetch(new Request('https://test/admin'),{})).status,403);});
test('ingest and internal routes fail closed before provisioning',async()=>{assert.equal((await worker.fetch(new Request('https://test/reports/'+r.reportID,{method:'PUT'}),{})).status,503);assert.equal((await worker.fetch(new Request('https://test/internal/batch',{method:'POST'}),{})).status,401);assert.equal(await sameSecret('x','y'),false);});
import {DatabaseSync} from 'node:sqlite';import {readFileSync} from 'node:fs';
class D1 {
 constructor(){this.db=new DatabaseSync(':memory:');for(const file of ['0001_reports.sql','0002_admin_oauth.sql'])this.db.exec(readFileSync(new URL('./migrations/'+file,import.meta.url),'utf8'));}
 prepare(sql){const stmt=this.db.prepare(sql);let params=[];const q={bind(...p){params=p;return q;},async first(){return stmt.get(...params)||null;},async all(){return {results:stmt.all(...params)};},async run(){return stmt.run(...params);}};return q;}
 async batch(q){this.db.exec('BEGIN');try{const result=[];for(const x of q)result.push(await x.run());this.db.exec('COMMIT');return result;}catch(e){this.db.exec('ROLLBACK');throw e;}}
}
test('D1-compatible ownership, idempotency, batch acknowledgement, deletion and replay',async()=>{
 const db=new D1(),env={DB:db,INGEST_ENABLED:'true',RATE_SALT:'test-only',EXPORT_TOKEN:'e'.repeat(64)};
 const cap='a'.repeat(64),base='https://test/reports/'+r.reportID;
 const send=(url,method,body,token=cap)=>worker.fetch(new Request(url,{method,headers:{Authorization:'Bearer '+token,'Content-Type':'application/json','CF-Connecting-IP':'test'},body:body?JSON.stringify(body):undefined}),env);
 const body={schemaVersion:1,requestID:crypto.randomUUID(),revision:1,report:r};
 assert.equal((await send(base,'PUT',body)).status,200);assert.equal((await send(base,'PUT',body)).status,200);
 assert.equal((await send(base,'PUT',body,'b'.repeat(64))).status,403);
 const pub=JSON.stringify(publicReport(r));db.db.prepare("UPDATE reports SET state='queued',approved=?,approved_revision=1 WHERE id=?").run(pub,r.reportID);
 const id=crypto.randomUUID();const snap=await (await send('https://test/internal/batch','POST',{action:'prepare',id},env.EXPORT_TOKEN)).json();
 assert.equal(snap.reports.length,1);assert.equal(snap.reports[0].report.note,undefined);
 assert.equal((await send('https://test/internal/batch','POST',{action:'published',id},env.EXPORT_TOKEN)).status,200);
 assert.equal(db.db.prepare('SELECT state FROM reports').get().state,'published');
 assert.equal((await send(base,'PUT',{...body,requestID:crypto.randomUUID(),revision:3})).status,200);
 assert.equal(db.db.prepare('SELECT state FROM reports').get().state,'review');
 assert.equal((await send(base,'DELETE')).status,200);assert.equal((await send(base,'PUT',{...body,revision:4})).status,410);
 assert.equal(db.db.prepare('SELECT payload FROM reports').get().payload,null);
});

test('GitHub OAuth binds browser, consumes state, rejects other users and expires sessions',async()=>{
 const origin='https://pear-reports.postmelee.workers.dev';
 const env={DB:new D1(),GITHUB_CLIENT_ID:'test',GITHUB_CLIENT_SECRET:'test-secret',ADMIN_GITHUB_ID:'65849802',RATE_SALT:'test'};
 const start=async()=>{const res=await authRoute(new Request(origin+'/auth/login'),env);assert.equal(res.status,302);const u=new URL(res.headers.get('Location'));assert.equal(u.searchParams.get('scope'),'');assert.equal(u.searchParams.get('code_challenge_method'),'S256');return {state:u.searchParams.get('state'),cookie:res.headers.get('Set-Cookie').split(';')[0]};};
 const callback=(v,cookie=v.cookie)=>new Request(origin+'/auth/callback?code=test&state='+v.state,{headers:{Cookie:cookie}});
 let calls=0;const provider=async(url,options)=>{calls++;assert.equal(options.redirect,'manual');return Response.json(url.includes('access_token')?{access_token:'temporary',token_type:'bearer',scope:''}:{id:65849802});};
 const v=await start();assert.equal((await authRoute(callback(v,'__Host-pear-oauth='+'a'.repeat(64)),env,provider)).status,400);assert.equal(calls,0);
 const success=await authRoute(callback(v),env,provider);assert.equal(success.status,303);assert.equal(calls,2);
 assert.equal((await authRoute(callback(v),env,provider)).status,400);assert.equal(calls,2);
 const session=success.headers.getSetCookie().find(x=>x.startsWith('__Host-pear-session=')).split(';')[0];
 const req=new Request(origin+'/admin',{headers:{Cookie:session}});assert.equal(await reviewer(req,env),true);
 assert.equal(await reviewer(req,{...env,ADMIN_GITHUB_ID:'1'}),false);
 const invalidLogout=await authRoute(new Request(origin+'/auth/logout',{method:'POST',headers:{Cookie:session,Origin:'https://evil.test'}}),env);assert.equal(invalidLogout.status,403);
 assert.equal(await reviewer(req,env),true);
 const logout=await authRoute(new Request(origin+'/auth/logout',{method:'POST',headers:{Cookie:session,Origin:origin}}),env);assert.equal(logout.status,303);assert.equal(await reviewer(req,env),false);
 const other=await start();assert.equal((await authRoute(callback(other),env,async url=>Response.json(url.includes('access_token')?{access_token:'temporary',token_type:'bearer',scope:''}:{id:1}))).status,403);
 const expired=await start();env.DB.db.exec('UPDATE oauth_states SET expires=0');assert.equal((await authRoute(callback(expired),env,provider)).status,400);
 const broad=await start();assert.equal((await authRoute(callback(broad),env,async()=>Response.json({access_token:'temporary',token_type:'bearer',scope:'repo'}))).status,502);
 const redirected=await start();let redirectCalls=0;const denied=await authRoute(callback(redirected),env,async()=>{redirectCalls++;return new Response(null,{status:302,headers:{Location:'https://untrusted.invalid'}});});assert.equal(denied.status,502);assert.equal(redirectCalls,1);
 const good=await start();const res=await authRoute(callback(good),env,provider);const cookie=res.headers.getSetCookie().find(x=>x.startsWith('__Host-pear-session=')).split(';')[0];env.DB.db.exec('UPDATE admin_sessions SET expires=0');assert.equal(await reviewer(new Request(origin+'/admin',{headers:{Cookie:cookie}}),env),false);
});
