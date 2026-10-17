// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// GitHub documented authorization-code flow with S256 PKCE. Web Crypto supplies
// random capability/session values; D1 stores only their SHA-256 digests.
import {digest,smallText} from './policy.mjs';
const origin='https://pear-reports.postmelee.workers.dev';
const callback=origin+'/auth/callback';
const random=()=>Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');
const cookie=(name,value,age)=>`${name}=${value}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=${age}`;
function readCookie(req,name){const matches=(req.headers.get('Cookie')||'').split(';').map(x=>x.trim()).filter(x=>x.startsWith(name+'='));return matches.length===1?matches[0].slice(name.length+1):'';}
const tokenPattern=/^[a-f0-9]{64}$/;
const configured=env=>env.GITHUB_CLIENT_ID&&env.GITHUB_CLIENT_SECRET&&/^[1-9][0-9]*$/.test(env.ADMIN_GITHUB_ID||'');
function response(text,status=400,headers={}){return new Response(text,{status,headers:{'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff',...headers}});}
export async function reviewer(req,env){
 if(new URL(req.url).origin!==origin||!configured(env))return false;
 const session=readCookie(req,'__Host-pear-session');if(!tokenPattern.test(session))return false;
 const row=await env.DB.prepare('SELECT user_id FROM admin_sessions WHERE hash=? AND expires>?').bind(await digest(session),Date.now()).first();
 return row?.user_id===env.ADMIN_GITHUB_ID;
}
export async function authRoute(req,env,fetcher=fetch){
 const url=new URL(req.url);if(url.origin!==origin)return response('Invalid origin',403);
 if(!configured(env))return response('Administrator login is not configured',503);
 if(url.pathname==='/auth/logout'){
  if(req.method!=='POST'||req.headers.get('Origin')!==origin)return response('Invalid origin',403);
  const session=readCookie(req,'__Host-pear-session');if(tokenPattern.test(session))await env.DB.prepare('DELETE FROM admin_sessions WHERE hash=?').bind(await digest(session)).run();
  return response('',303,{Location:'/admin','Set-Cookie':cookie('__Host-pear-session','',0)});
 }
 if(req.method!=='GET')return response('Method not allowed',405);
 if(url.pathname==='/auth/login'){
  const state=random(),browser=random(),verifier=random(),now=Date.now();
  const ip=req.headers.get('CF-Connecting-IP')||'unknown';
  if(!env.RATE_SALT)return response('Login unavailable',503);
  const key=await digest(env.RATE_SALT+':login:'+Math.floor(now/60000)+':'+ip);
  const rate=await env.DB.prepare('INSERT INTO rate_limits(key,count,expires) VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count').bind(key,Math.floor(now/1000)+120).first();
  if(rate.count>10)return response('Try again later',429);
  await env.DB.prepare('INSERT INTO oauth_states(hash,browser_hash,verifier,expires) VALUES (?,?,?,?)').bind(await digest(state),await digest(browser),verifier,now+600000).run();
  const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier)));
  const challenge=btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  const target=new URL('https://github.com/login/oauth/authorize');
  target.search=new URLSearchParams({client_id:env.GITHUB_CLIENT_ID,redirect_uri:callback,scope:'',state,code_challenge:challenge,code_challenge_method:'S256',allow_signup:'false'}).toString();
  return response('',302,{Location:target.href,'Set-Cookie':cookie('__Host-pear-oauth',browser,600)});
 }
 if(url.pathname!=='/auth/callback')return response('Not found',404);
 const state=url.searchParams.get('state'),code=url.searchParams.get('code'),browser=readCookie(req,'__Host-pear-oauth');
 if(!tokenPattern.test(state||'')||!tokenPattern.test(browser)||!code||code.length>512)return response('Login expired or rejected');
 const transaction=await env.DB.prepare('DELETE FROM oauth_states WHERE hash=? AND browser_hash=? AND expires>? RETURNING verifier').bind(await digest(state),await digest(browser),Date.now()).first();
 if(!transaction)return response('Login expired or already used');
 let stage='token-exchange';
 try{
  const exchanged=await fetcher('https://github.com/login/oauth/access_token',{method:'POST',redirect:'manual',signal:AbortSignal.timeout(10000),headers:{Accept:'application/json','Content-Type':'application/x-www-form-urlencoded','User-Agent':'Pear-report-review'},body:new URLSearchParams({client_id:env.GITHUB_CLIENT_ID,client_secret:env.GITHUB_CLIENT_SECRET,code,redirect_uri:callback,code_verifier:transaction.verifier})});
  stage='token-http-'+exchanged.status;
  if(!exchanged.ok)throw Error('exchange');
  stage='token-decoding';const token=JSON.parse(await smallText(exchanged,16384));
  if(['incorrect_client_credentials','bad_verification_code','redirect_uri_mismatch'].includes(token.error))return response('GitHub login failed: '+token.error+'. Start again.',502,{'Set-Cookie':cookie('__Host-pear-oauth','',0)});
  stage='token-response';
  if(typeof token.access_token!=='string'||token.token_type?.toLowerCase()!=='bearer'||token.scope)throw Error('scope');
  stage='account-lookup';
  const identity=await fetcher('https://api.github.com/user',{redirect:'manual',signal:AbortSignal.timeout(10000),headers:{Authorization:'Bearer '+token.access_token,Accept:'application/vnd.github+json','User-Agent':'Pear-report-review','X-GitHub-Api-Version':'2022-11-28'}});
  if(!identity.ok)throw Error('identity');const user=JSON.parse(await smallText(identity,65536));
  if(!Number.isSafeInteger(user.id)||String(user.id)!==env.ADMIN_GITHUB_ID)return response('This GitHub account is not an administrator',403,{'Set-Cookie':cookie('__Host-pear-oauth','',0)});
  stage='session-storage';
  const session=random(),now=Date.now();
  const old=readCookie(req,'__Host-pear-session');if(tokenPattern.test(old))await env.DB.prepare('DELETE FROM admin_sessions WHERE hash=?').bind(await digest(old)).run();
  await env.DB.prepare('INSERT INTO admin_sessions(hash,user_id,expires) VALUES (?,?,?)').bind(await digest(session),String(user.id),now+3600000).run();
  const headers=new Headers({Location:'/admin','Cache-Control':'no-store','Referrer-Policy':'no-referrer'});headers.append('Set-Cookie',cookie('__Host-pear-oauth','',0));headers.append('Set-Cookie',cookie('__Host-pear-session',session,3600));
  return new Response(null,{status:303,headers});
 }catch(error){const reason=String(error?.message||'').includes('Illegal invocation')?'invalid-fetch-binding':String(error?.message||'').includes('redirect')?'redirect-rejected':error?.name==='TimeoutError'?'timeout':error?.name==='TypeError'?'type-error':'request-error';return response('GitHub login failed ('+stage+'/'+reason+'). Start again.',502,{'Set-Cookie':cookie('__Host-pear-oauth','',0)});}
}
