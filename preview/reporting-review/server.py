#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Loopback-only reporting rehearsal. Never deploy this as the collection API."""
import argparse, hashlib, html, json, secrets, sqlite3, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

FIELDS = {'reportID','userResult','macOS','chip','memoryGiB','pear','wine','dxmt','appID','gameBuild','dateUTC','processMinutes','observedExit','note','supplemental'}
CHECKS = {'unknown','observed','failed','not-tested'}
STAGES = {'unknown','launch-failed','launched-unusable','menu-interactive','active-gameplay','regression'}
def validate(r):
    if not isinstance(r,dict) or set(r)-FIELDS: raise ValueError('fields')
    uuid.UUID(r['reportID'])
    if r.get('userResult') not in {'normal','problems','unknown'}: raise ValueError('result')
    for k in ('appID','memoryGiB','processMinutes'):
        if k in r and (type(r[k]) is not int or not 0 <= r[k] <= 4294967295): raise ValueError(k)
    for k in FIELDS-{'supplemental','appID','memoryGiB','processMinutes'}:
        if k in r and (not isinstance(r[k],str) or len(r[k]) > 4000): raise ValueError(k)
    s=r.get('supplemental',{})
    if not isinstance(s,dict) or set(s)-{'furthestResult','activePlayMinutes','input','audio','saveReload','recovery','settings'}: raise ValueError('details')
    if s.get('furthestResult','unknown') not in STAGES: raise ValueError('stage')
    for k in ('input','audio','saveReload','recovery'):
        if s.get(k,'unknown') not in CHECKS: raise ValueError('check')
    if 'activePlayMinutes' in s and (type(s['activePlayMinutes']) is not int or not 0 <= s['activePlayMinutes'] <= 1440): raise ValueError('minutes')
    if not isinstance(s.get('settings',''),str) or len(s.get('settings',''))>500: raise ValueError('settings')
    return r

def project(r):
    """Public allowlist; private note and exact timestamps cannot escape."""
    return {k:v for k,v in validate(r).items() if k != 'note'}

def card(r):
    e=lambda v:html.escape(str(v))
    s=r.get('supplemental',{})
    app=r.get('appID'); name='Megabonk' if app==3405340 else f'Steam App {app}' if app else 'Game not shared'
    link=f'<a href="https://store.steampowered.com/app/{app}/">View on Steam ↗</a>' if app else ''
    result={'normal':'Worked normally','problems':'Had problems','unknown':'Not confirmed'}[r['userResult']]
    rows=[('Mac / macOS',f"{r.get('chip','Unknown')} · {r.get('memoryGiB','Unknown')} GB · macOS {r.get('macOS','Unknown')}"),('Versions',f"Pear {r.get('pear','Unknown')} · Wine {r.get('wine','Unknown')} · DXMT {r.get('dxmt','Unknown')}"),('Game build',r.get('gameBuild','Unknown')),('Date (UTC)',r.get('dateUTC','Not shared')),('Process minutes',r.get('processMinutes','Unknown')),('Observed exit',r.get('observedExit','Unknown')),('Furthest result',s.get('furthestResult','unknown')),('Active play minutes · user supplied',s.get('activePlayMinutes','Not measured'))]+[(k,s.get(v,'unknown')) for k,v in [('Input','input'),('Audio','audio'),('Save / reload','saveReload'),('Recovery','recovery')]]+[('Game settings',s.get('settings') or 'Not recorded')]
    return f'<article><h2>{e(name)}</h2>{link}<p class="badge {e(r["userResult"])}">User report · {e(result)}</p><p>Process time is not verified play time. This report is not a Pass or qualification.</p><dl>'+''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k,v in rows)+'</dl></article>'

STYLE='body{font:16px system-ui;color:#263027;background:#faf9f3;margin:40px auto;max-width:1050px;padding:0 24px}h1{font-size:36px}h2{font-size:25px}article{background:white;border:1px solid #dedfd7;border-radius:14px;padding:24px;margin:20px 0}a{color:#40643a}button{padding:12px 18px;background:#40643a;color:white;border:0;border-radius:8px;cursor:pointer;margin:8px}dl{display:grid;grid-template-columns:240px 1fr;gap:12px}dt{font-weight:600}dd{margin:0}.badge{display:inline-block;padding:8px 12px;border-radius:8px;background:#eee}.normal{background:#e4f1e3}.problems{background:#f9e3df}.notice{padding:18px;background:#eeefe5;border-radius:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,code,value,kind='application/json'):
        data=(json.dumps(value) if kind=='application/json' else value).encode()
        self.send_response(code);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def host_ok(self): return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
    def read(self):
        n=int(self.headers.get('Content-Length','0'))
        if not 0<n<=16384: raise ValueError('size')
        return self.rfile.read(n)
    def do_PUT(self):
        if not self.host_ok(): return self.send(403,{'error':'host'})
        try:
            report_id=str(uuid.UUID(self.path.removeprefix('/reports/')))
            if self.path!=f'/reports/{report_id}': raise ValueError('path')
            auth=self.headers.get('Authorization','').removeprefix('Bearer ')
            if len(auth)!=64 or any(c not in '0123456789abcdef' for c in auth): return self.send(403,{'error':'capability'})
            v=json.loads(self.read())
            if set(v)!={'schemaVersion','requestID','revision','report'} or v['schemaVersion']!=1 or type(v['revision']) is not int or v['revision']<1: raise ValueError('envelope')
            uuid.UUID(v['requestID']);r=validate(v['report'])
            if r['reportID'].lower()!=report_id: raise ValueError('identity')
            owner=hashlib.sha256(auth.encode()).hexdigest();payload=json.dumps(r,sort_keys=True)
            with sqlite3.connect(self.server.db) as db:
                row=db.execute('select owner,revision,request,payload from reports where id=?',(report_id,)).fetchone()
                if row:
                    if not secrets.compare_digest(row[0],owner): return self.send(403,{'error':'owner'})
                    if row[1]==v['revision'] and row[2]==v['requestID'] and row[3]==payload: pass
                    elif v['revision']<=row[1]: return self.send(409,{'error':'revision'})
                    else: db.execute("update reports set revision=?,request=?,payload=?,state='Needs review',approved=null where id=?",(v['revision'],v['requestID'],payload,report_id))
                else: db.execute("insert into reports(id,owner,revision,request,payload,state) values(?,?,?,?,?,'Needs review')",(report_id,owner,v['revision'],v['requestID'],payload))
            self.send(200,{'reportID':r['reportID'],'requestID':v['requestID'],'revision':v['revision']})
        except (ValueError,KeyError,TypeError): self.send(400,{'error':'invalid report'})
    def do_POST(self):
        if not self.host_ok() or self.headers.get('Origin')!=f'http://127.0.0.1:{self.server.server_port}': return self.send(403,{'error':'origin'})
        try:
            form=parse_qs(self.read().decode())
            if not secrets.compare_digest(form.get('csrf',[''])[0],self.server.csrf): return self.send(403,{'error':'csrf'})
            with sqlite3.connect(self.server.db) as db:
                if self.path=='/approve':
                    row=db.execute('select payload from reports where id=? and revision=?',(form['id'][0],int(form['revision'][0]))).fetchone()
                    if not row: return self.send(409,{'error':'stale review'})
                    r=project(json.loads(row[0]))
                    if not r.get('appID'): return self.send(409,{'error':'App ID not shared; keep private until supplied'})
                    db.execute("update reports set approved=?,state='Queued' where id=?",(json.dumps(r),form['id'][0]))
                elif self.path=='/publish': db.execute("update reports set published=approved,state='Published' where state='Queued'")
                else: return self.send(404,{})
            self.send_response(303);self.send_header('Location','/');self.end_headers()
        except (ValueError,KeyError): self.send(400,{})
    def do_GET(self):
        if not self.host_ok(): return self.send(403,{})
        with sqlite3.connect(self.server.db) as db: rows=db.execute('select id,revision,payload,state,published from reports order by rowid desc').fetchall()
        if self.path=='/catalog.json': return self.send(200,{'schemaVersion':1,'reports':[json.loads(r[4]) for r in rows if r[4]]})
        if self.path not in ('/','/catalog'): return self.send(404,{})
        page='<h1>'+('Catalog preview' if self.path=='/catalog' else 'Private report review')+'</h1><p class="notice">LOCAL REHEARSAL · Data stays on this Mac. Nothing is published to GitHub or the public website. This is not production authentication or hosting validation.</p><nav><a href="/">Review reports</a> · <a href="/catalog">Catalog preview</a> · <a href="/catalog.json">Public projection JSON</a></nav>'
        token=f'<input type="hidden" name="csrf" value="{self.server.csrf}">'
        if self.path=='/': page+=f'<form action="/publish" method="post">{token}<button>Apply approved reports to local catalog</button></form><p>This simulates the daily batch. Approval alone does not publish.</p>'
        for rid,rev,payload,state,published in rows:
            if self.path=='/catalog':
                if published: page+=card(json.loads(published))
            else:
                r=json.loads(payload);page+=card(project(r))+f'<p><strong>{html.escape(state)}</strong> · Revision {rev}</p><details><summary>Private note · never in catalog</summary><pre>{html.escape(r.get("note", "No note shared"))}</pre></details><form action="/approve" method="post">{token}<input type="hidden" name="id" value="{rid}"><input type="hidden" name="revision" value="{rev}"><button>Approve for next update</button></form>'
        if not rows: page+='<p>No reports yet. Share a result from Pear Reporting Review.</p>'
        self.send(200,'<!doctype html><meta charset="utf-8"><title>Pear · Local report review</title><style>'+STYLE+'</style>'+page,'text/html')

def main():
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--port',type=int,default=8964);a=p.parse_args()
    root=Path(a.state).resolve();root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
    db=root/'reports.sqlite'
    with sqlite3.connect(db) as c: c.execute('create table if not exists reports(id text primary key,owner text,revision integer,request text,payload text,state text,approved text,published text)')
    db.chmod(0o600)
    server=HTTPServer(('127.0.0.1',a.port),Handler);server.db=str(db);server.csrf=secrets.token_hex(32)
    print(f'Local-only review: http://127.0.0.1:{a.port}',flush=True);server.serve_forever()
if __name__=='__main__': main()
