# SPDX-License-Identifier: MIT
"""Attribute a diagnostic refusal to the exact owned image and mapping attempt."""
from pathlib import Path
import argparse,re
from tools.wine.image_admission_inputs import admit as admit_inputs,checked,read,save,fact,need,digest
from tools.wine.image_admission_runtime import admit as admit_runtime
from tools.fex import memory_wine_run as supervisor
LINE=re.compile(rb'PEAR_IMAGE_ADMISSION pid=(\d+) fd=(\d+) dev=(\d+) ino=(\d+) bytes=(\d+) phase=([a-zA-Z0-9.]+) status=([0-9a-f]{8})')

def refusal(raw,target,pid):
    rows=[]
    for m in LINE.finditer(raw):
        p,fd,dev,ino,size=map(int,m.groups()[:5])
        if p==pid and (dev,ino,size)==(target['dev'],target['ino'],target['bytes']):
            rows.append(dict(fd=fd,phase=m[6].decode(),status=m[7].decode()))
    need(rows and rows[0]['phase']=='caller.begin','image_target_identity_missing')
    attempts=[];current=[]
    for row in rows:
        if row['phase']=='caller.begin':
            if current:attempts.append(current)
            current=[]
        current.append(row)
    if current:attempts.append(current)
    for attempt in attempts:
        denied=[r for r in attempt if r['status']!='00000000']
        if not denied:continue
        first=denied[0]
        need(len({r['fd'] for r in attempt})==1,'image_attempt_fd_changed')
        need(first['phase'].startswith('parser.return'),'image_refusal_outside_parser')
        need(any(r['phase']=='parser.begin' and r['status']=='00000000' for r in attempt),'image_parser_begin_missing')
        need(attempt[-1]['phase']=='caller.parsed' and attempt[-1]['status']==first['status'],'image_parser_return_missing')
        return dict(first_refusal=first['phase'],status=first['status'],attempt=attempt)
    need(False,'image_no_refusal')

def ownership(r):
    need(r['outcome']=='image_refused' and r['error'] is None and r['stream_error'] is None and not r['cleanup_errors'],'image_run_incomplete')
    for key in ('cleanup','sentinel_cleanup'):
        c=r[key];need(c['complete'] and not c['errors'] and not c['observation_gap'] and c['reaped'] and all(c['reaped'].values()),'image_cleanup_incomplete')
    need(r['sentinel_survived'] and r['processes']['sentinel']['exit_code']==0 and r['authorization_before_after_passed'],'image_ownership_failed')
    need(r['original_files_unchanged'] and r['runtime_unchanged'],'image_run_integrity')

def check(folder):
    folder=Path(folder).resolve(strict=True);r=read(folder/'case.json')
    need(r['scope']=='image_admission_diagnostic' and r['diagnostic_only'],'image_run_scope')
    checked(r['producer_ref']);checked(r['inputs_ref']);checked(r['runtime_ref'])
    i=admit_inputs(Path(r['inputs_ref']['path']).parent);runtime=Path(r['runtime_ref']['path']).parent;v=admit_runtime(runtime)
    need(r['runtime_ref']['sha256']==r['runtime_sha256'] and v['image_admission_overlay']['inputs_ref']==r['inputs_ref'],'image_run_binding')
    ownership(r)
    for side in ('before','after'):
        c=read(folder/side/'control.json');need(c['passed'] and c['runtime_sha256']==r['runtime_sha256'],'image_authorization_pair')
    raw=supervisor.verify_logs(folder/'run',r)
    for role,events in r['events'].items():
        import json
        need([json.loads(line) for line in raw[(role,'events')].splitlines()]==events,'image_events_changed')
    source=Path(i['game'])/'GameAssembly.dll';clone=folder/'game/GameAssembly.dll';st=clone.stat()
    need(digest(source.read_bytes())==digest(clone.read_bytes())==i['pe']['sha256']==r['target_identity']['sha256'],'image_clone_changed')
    need(r['target_identity']==dict(dev=st.st_dev,ino=st.st_ino,bytes=st.st_size,sha256=i['pe']['sha256']),'image_clone_identity')
    result=refusal(raw[('loader','stderr')],r['target_identity'],r['processes']['loader']['identity']['pid'])
    events=[e for rows in r['events'].values() for e in rows];native=[e for e in events if 'translation_value' in e]
    need(native and all(e['cpu_type']==16777228 and e['translation_value']==0 and e['translation_error']==0 for e in native),'image_native_observation')
    images=[e for e in events if e['event']=='image']
    need(images and all(e['cpu_type']==16777228 for e in images),'image_observed_module_not_arm64')
    result.update(scope='image_admission_refusal',passed=True,diagnostic_only=True,run_ref=fact(folder/'case.json'),runtime_ref=r['runtime_ref'],pe=i['pe'],game_qualified=False,complete_late_load_coverage=False)
    save(folder/'assessment.json',result);print({k:result[k] for k in ('passed','first_refusal','status','game_qualified')})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--require',choices=['refusal'],required=True)
    a=p.parse_args();check(a.run)
