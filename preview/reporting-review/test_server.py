# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import json, sqlite3, tempfile, threading, unittest, urllib.request, urllib.error, uuid
from pathlib import Path
from server import Handler, HTTPServer, project, card
class Flow(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'r.db'
            with sqlite3.connect(db) as c: c.execute('create table reports(id text primary key,owner text,revision integer,request text,payload text,state text,approved text,published text)')
            s=HTTPServer(('127.0.0.1',0),Handler);s.db=str(db);s.csrf='test-csrf'
            t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            base=f'http://127.0.0.1:{s.server_port}';rid=str(uuid.uuid4())
            r={'reportID':rid,'userResult':'normal','appID':3405340,'processMinutes':20,'note':'PRIVATE NOTE'}
            v={'schemaVersion':1,'requestID':str(uuid.uuid4()),'revision':1,'report':r}
            def put(body,key='a'*64):
                req=urllib.request.Request(base+'/reports/'+rid,data=json.dumps(body).encode(),method='PUT',headers={'Authorization':'Bearer '+key})
                try:
                    with urllib.request.urlopen(req) as out:return out.status,json.load(out)
                except urllib.error.HTTPError as e:
                    code=e.code;e.close();return code,{}
            try:
                self.assertEqual(put(v)[0],200);self.assertEqual(put(v)[0],200)
                self.assertEqual(put(v,'b'*64)[0],403)
                with urllib.request.urlopen(base+'/catalog.json') as out:self.assertEqual(json.load(out)['reports'],[])
                from urllib.parse import urlencode
                def post(path,data):
                    req=urllib.request.Request(base+path,data=urlencode({'csrf':'test-csrf',**data}).encode(),headers={'Origin':base})
                    with urllib.request.urlopen(req) as out: return out.read().decode()
                post('/approve',{'id':rid,'revision':1})
                with urllib.request.urlopen(base+'/catalog.json') as out:self.assertEqual(json.load(out)['reports'],[])
                post('/publish',{})
                with urllib.request.urlopen(base+'/catalog.json') as out:
                    public=json.load(out);self.assertEqual(len(public['reports']),1);self.assertNotIn('PRIVATE NOTE',json.dumps(public))
                v['revision']=2;v['requestID']=str(uuid.uuid4());v['report']['userResult']='problems'
                self.assertEqual(put(v)[0],200)
                with sqlite3.connect(db) as c:self.assertEqual(c.execute('select count(*),state from reports').fetchone(),(1,'Needs review'))
                with urllib.request.urlopen(base+'/catalog.json') as out:self.assertEqual(json.load(out)['reports'][0]['userResult'],'normal')
                self.assertIn('Not measured',card(project(r)))
                self.assertIn('store.steampowered.com/app/3405340',card(project(r)))
            finally:s.shutdown();s.server_close();t.join()
if __name__=='__main__':unittest.main()
