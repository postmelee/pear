#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded CI bridge: GitHub source links and reviewed public catalog snapshots."""
import argparse, json, os, uuid
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit, urlencode
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def request(url,token,body=None):
    if urlsplit(url).scheme!='https': raise ValueError('HTTPS required')
    req=Request(url,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/vnd.github+json','User-Agent':'Pear-reviewed-catalog'})
    with build_opener(NoRedirect()).open(req,timeout=30) as res:
        data=res.read(8*1024*1024+1)
        if len(data)>8*1024*1024: raise ValueError('Response too large')
        return json.loads(data)

def endpoint():
    base=os.environ['PEAR_REPORTS_URL'].rstrip('/');u=urlsplit(base)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path: raise ValueError('Invalid API origin')
    return base

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','published','github']);p.add_argument('--output');p.add_argument('--batch');a=p.parse_args()
    base=endpoint()
    if a.action=='github':
        gh=os.environ['GH_TOKEN'];key=os.environ['PEAR_REPORTS_IMPORT_TOKEN'];label=os.environ.get('PEAR_REPORTS_ISSUE_LABEL','pear-report');category=os.environ.get('PEAR_REPORTS_DISCUSSION_CATEGORY','')
        for page in range(1,11):
            rows=request('https://api.github.com/repos/postmelee/pear/issues?'+urlencode({'state':'all','labels':label,'per_page':100,'page':page}),gh)
            for r in rows:
                if 'pull_request' not in r: request(base+'/internal/github',key,{'id':r['node_id'],'kind':'issue','url':r['html_url'],'title':r['title'][:300],'updated':r['updated_at']})
            if len(rows)<100: break
        else: raise ValueError('Issue scan capacity reached')
        if category:
            cursor=None
            query='query($cursor:String){repository(owner:"postmelee",name:"pear"){discussions(first:100,after:$cursor){nodes{id url title updatedAt category{name}} pageInfo{hasNextPage endCursor}}}}'
            for _ in range(10):
                response=request('https://api.github.com/graphql',gh,{'query':query,'variables':{'cursor':cursor}})
                if response.get('errors'): raise ValueError('GitHub query failed')
                result=response['data']['repository']['discussions']
                for r in result['nodes']:
                    if r['category']['name']==category:request(base+'/internal/github',key,{'id':r['id'],'kind':'discussion','url':r['url'],'title':r['title'][:300],'updated':r['updatedAt']})
                if not result['pageInfo']['hasNextPage']:break
                cursor=result['pageInfo']['endCursor']
            else:raise ValueError('Discussion scan capacity reached')
        return
    batch=a.batch or str(uuid.uuid5(uuid.NAMESPACE_URL,'pear-pages:'+os.environ['GITHUB_RUN_ID']))
    value=request(base+'/internal/batch',os.environ['PEAR_REPORTS_EXPORT_TOKEN'],{'action':a.action,'id':batch})
    if a.action=='prepare':
        if value.get('batchID')!=batch:raise ValueError('Wrong snapshot')
        from community_reports import validate
        validate(value)
        Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(value)+'\n')
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('batch='+batch+'\n')
if __name__=='__main__':main()
