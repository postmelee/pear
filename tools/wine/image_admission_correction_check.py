# SPDX-License-Identifier: MIT
"""Replay same-candidate large-image loader evidence; fixtures are not a game gate."""
from pathlib import Path
import argparse,json,re
from tools.wine.image_admission_inputs import checked,read,save,fact,need
from tools.wine.image_admission_correction_runtime import admit as runtime_admit
from tools.wine.image_admission_fixtures import admit as fixtures_admit
from tools.wine.image_admission_check import LINE
from tools.fex import memory_wine_run as supervisor

def terminal(raw,role):
    lines=raw.decode().splitlines();need(lines and json.loads(lines[0]).get('record_kind')=='pear_bootstrap_helper','loader_bootstrap')
    lines=lines[1:];need(lines[0]=='PEAR_LOADER_BEGIN role='+('arm64' if role=='aarch64' else 'x64') and lines[-1]=='PEAR_LOADER_END passed=8','loader_terminal')
    success=[];reject=[];attach=0
    for line in lines[1:-1]:
        if line=='PEAR_LOADER_ATTACH_REJECT':attach+=1;continue
        m=re.fullmatch(r'PEAR_LOADER_PASS case=([0-9a-f]{16}) round=([0-9a-f]{16}) base=([0-9a-f]{16}) bytes=([0-9a-f]{16})',line)
        if m:success.append(tuple(int(x,16) for x in m.groups()));continue
        m=re.fullmatch(r'PEAR_LOADER_REJECT case=([0-9a-f]{16}) round=([0-9a-f]{16}) error=([0-9a-f]{16})',line)
        need(m is not None,'loader_unknown_record');reject.append(tuple(int(x,16) for x in m.groups()))
    need(attach==2 and [(a,b) for a,b,c in reject]==[(10,0),(10,1),(20,0),(20,1)] and all(c for a,b,c in reject),'loader_rejection_incomplete')
    need([(a,b,d) for a,b,c,d in success]==[(30,0,57647104),(30,1,57647104),(40,0,67108864),(40,1,67108864)],'loader_success_incomplete')
    need(all(c and c!=0x180000000 and c%65536==0 for a,b,c,d in success) and success[0][2]==success[1][2] and success[2][2]==success[3][2],'loader_relocation_reuse')
    return dict(successes=success,rejections=reject,attach_rejections=attach)

def ownership(r):
    need(r['outcome']=='exited' and r['processes']['loader']['exit_code']==42 and r['error'] is None and r['stream_error'] is None and not r['cleanup_errors'],'loader_execution')
    for key in ('cleanup','sentinel_cleanup'):
        c=r[key];need(c['complete'] and not c['errors'] and not c['observation_gap'] and c['reaped'] and all(c['reaped'].values()),'loader_cleanup')
    need(r['sentinel_survived'] and r['processes']['sentinel']['exit_code']==0 and r['authorization_before_after_passed'] and r['fixtures_unchanged'] and r['runtime_unchanged'],'loader_ownership')

def check(folder):
    folder=Path(folder).resolve();r=read(folder/'case.json')
    need(r['kind']=='image_loader_observation' and not r['diagnostic_only'],'loader_scope')
    for key in ('producer_ref','inputs_ref','runtime_ref','fixtures_ref'):checked(r[key])
    runtime=Path(r['runtime_ref']['path']).parent;v=runtime_admit(runtime)
    fixtures=Path(r['fixtures_ref']['path']).parent;f=fixtures_admit(fixtures);role=r['role']
    need(r['fixture']==f['roles'][role]['driver'] and r['runtime_ref']['sha256']==r['runtime_sha256'] and v['image_admission_correction_overlay']['inputs_ref']==r['inputs_ref'],'loader_input_binding')
    ownership(r)
    for side in ('before','after'):
        c=read(folder/side/'control.json');need(c['passed'] and c['runtime_sha256']==r['runtime_sha256'],'loader_authorization_pair')
    raw=supervisor.verify_logs(folder/'run',r)
    for who,events in r['events'].items():need([json.loads(line) for line in raw[(who,'events')].splitlines()]==events,'loader_event_integrity')
    result=terminal(raw[('loader','stdout')],role)
    events=[e for rows in r['events'].values() for e in rows];native=[e for e in events if 'translation_value' in e];images=[e for e in events if e['event']=='image']
    need(native and all(e['cpu_type']==16777228 and e['translation_value']==0 and e['translation_error']==0 for e in native),'loader_host_architecture')
    need(images and all(e['cpu_type']==16777228 for e in images),'loader_module_architecture')
    loader=next(x for x in r['launches'] if x['role']=='loader');need(loader['argv'][-1]==r['fixture']['path'],'loader_fixture_launch')
    stderr=raw[('loader','stderr')];pid=r['processes']['loader']['identity']['pid'];mappings={}
    for name in ('required.dll','ceiling.dll','beyond.dll','attach-fail.dll'):
        st=(fixtures/role/name).stat();rows=[m for m in LINE.finditer(stderr) if tuple(map(int,(m[1],m[3],m[4],m[5])))==(pid,st.st_dev,st.st_ino,st.st_size)]
        if name=='beyond.dll':
            need(sum(m[6]==b'parser.return08' and m[7]==b'c00000bb' for m in rows)==2,'loader_limit_refusal')
        else:need(sum(m[6]==b'caller.published' and m[7]==b'00000000' for m in rows)==2,'loader_publication_missing')
        mappings[name]=len(rows)
    published=[e for e in r['events']['loader'] if e['event']=='arena_publish' and e['size'] in (57647104,67108864)]
    retired=[e for e in r['events']['loader'] if e['event']=='arena_retire']
    need(len(published)==6,'loader_publication_count')
    for e in published:
        need(e['policy']=='page-wx' and (e['code_pages']>0 if role=='aarch64' else e['code_pages']==0),'loader_role_publication')
        need(any(all(x[k]==e[k] for k in ('slot','slot_generation','base','size','capacity')) and x['arena_sequence']>e['arena_sequence'] for x in retired),'loader_retirement_missing')
    for index,(case,round,base,size) in enumerate(result['successes']):
        e=published[index+2]
        need(e['base']==base and e['size']==size and e['relocations']>=2 and e['original_base']==0x180000000,'loader_fixup_binding')
        if round:
            before=published[index+1]
            need(e['reused'] and e['slot']==before['slot'] and e['slot_generation']==before['slot_generation']+1,'loader_generation_reuse')
    # Attach failure must release its compatible slot before the successful DLL.
    need(published[0]['slot']==published[1]['slot']==published[2]['slot'] and
         published[1]['slot_generation']==published[0]['slot_generation']+1 and
         published[2]['slot_generation']==published[1]['slot_generation']+1,'loader_attach_rollback')
    result['publications']=[{k:e[k] for k in ('slot','slot_generation','size','capacity','code_pages','data_pages','relocations','reused')} for e in published]
    need(not re.search(rb'Exception c0000005|Pear FEX assertion:|Pear source guard refused',stderr),'loader_unexpected_fault')
    if role=='x86_64':need(b'Pear FEX init ProcessInit.complete: status=00000000' in stderr and any(e['event']=='stage3_guest_exit' and e['exit_code']==42 for e in r['events']['loader']),'loader_guest_execution')
    result.update(passed=True,scope='large_image_loader_fixtures',role=role,run_ref=fact(folder/'case.json'),runtime_ref=r['runtime_ref'],fixtures_ref=r['fixtures_ref'],mapping_records=mappings,game_qualified=False,complete_late_load_coverage=False)
    save(folder/'assessment.json',result);print(dict(passed=True,role=role,checks=8,game_qualified=False));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--require',choices=['loader'],required=True);a=p.parse_args();check(a.run)
