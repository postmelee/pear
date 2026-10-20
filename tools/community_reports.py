# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reviewed app observations stay separate from qualified compatibility evidence."""
import html, uuid
FIELDS=set('reportID userResult macOS chip memoryGiB pear wine dxmt appID gameBuild dateUTC processMinutes observedExit supplemental'.split())
def validate(snapshot):
    if set(snapshot)!={'schemaVersion','batchID','reports'} or snapshot['schemaVersion']!=1:raise ValueError('Invalid snapshot')
    uuid.UUID(snapshot['batchID']);seen=set()
    if not isinstance(snapshot['reports'],list) or len(snapshot['reports'])>10000:raise ValueError('Report capacity')
    for item in snapshot['reports']:
        if set(item)!={'revision','report'} or type(item['revision']) is not int or item['revision']<1:raise ValueError('Revision')
        r=item['report'];uuid.UUID(r['reportID'])
        if set(r)-FIELDS or r['reportID'] in seen or r.get('userResult') not in ('normal','problems','unknown'):raise ValueError('Invalid public report')
        seen.add(r['reportID'])
        if type(r.get('appID')) is not int or not 0<r['appID']<=4294967295:raise ValueError('Missing game identity')
        for key in ('memoryGiB','processMinutes'):
            if key in r and (type(r[key]) is not int or not 0<=r[key]<=4294967295):raise ValueError('Number')
        for key in FIELDS-{'supplemental','appID','memoryGiB','processMinutes'}:
            if key in r and (not isinstance(r[key],str) or len(r[key])>4000):raise ValueError('Text')
        s=r.get('supplemental',{})
        if not isinstance(s,dict) or set(s)-{'furthestResult','activePlayMinutes','input','audio','saveReload','recovery','settings'}:raise ValueError('Private or unknown details')
        for k,v in s.items():
            if k=='activePlayMinutes':
                if type(v) is not int or not 0<=v<=1440:raise ValueError('Play minutes')
            elif not isinstance(v,str) or len(v)>500:raise ValueError('Details')
    return snapshot

def cards(items):
    if not items: return '<p>No app-submitted reports have been published yet.</p>'
    out='';e=lambda v:html.escape(str(v),quote=True)
    for item in items:
        r=item['report'];s=r.get('supplemental',{})
        result={'normal':'Worked normally','problems':'Had problems','unknown':'Not confirmed'}[r['userResult']]
        facts=[('macOS',r.get('macOS','Unknown')),('Chip',r.get('chip','Unknown')),('Memory',r.get('memoryGiB','Unknown')),('Pear',r.get('pear','Unknown')),('Wine / DXMT',r.get('wine','Unknown')+' / '+r.get('dxmt','Unknown')),('Game build',r.get('gameBuild','Unknown')),('Process minutes',r.get('processMinutes','Unknown')),('Observed exit',r.get('observedExit','Unknown')),('Active play minutes — user supplied',s.get('activePlayMinutes','Not measured'))]+[(k,s.get(v,'Unknown')) for k,v in [('Furthest result','furthestResult'),('Input','input'),('Audio','audio'),('Save / reload','saveReload'),('Recovery','recovery'),('Settings','settings')]]
        out+=f'<article class="report"><h3>Steam App {r["appID"]} · {e(result)}</h3><p class="meta">{e(r.get("dateUTC","Date not shared"))} · User report · Not qualified</p><p>Process time is not verified play time. Publication approval does not establish Pass.</p><a href="https://store.steampowered.com/app/{r["appID"]}/">View on Steam ↗</a><details><summary>Environment and optional test details</summary><dl class="facts">'+''.join(f'<dt>{e(k)}</dt><dd translate="no">{e(v)}</dd>' for k,v in facts)+'</dl></details></article>'
    return out
