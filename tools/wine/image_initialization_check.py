# SPDX-License-Identifier: MIT
"""Separate actual GameAssembly attach from later Unity progress and qualification."""
from pathlib import Path
import argparse,json,re
from tools.wine.image_admission_inputs import checked,read,save,fact,need,digest,admit as inputs_admit
from tools.wine.image_admission_correction_runtime import admit as runtime_admit
from tools.wine.image_admission_check import LINE
from tools.fex import memory_wine_run as supervisor

def attachment(raw,base):
    address=rb'0*'+format(base,'x').encode()
    begin=re.search(rb'([0-9a-f]+):trace:module:MODULE_InitDLL \('+address+rb' L"GameAssembly.dll",PROCESS_ATTACH,[0-9a-f]+\) - CALL',raw,re.I)
    need(begin is not None,'game_attach_call_missing')
    end=re.search(re.escape(begin[1])+rb':trace:module:MODULE_InitDLL \('+address+rb',PROCESS_ATTACH,[0-9a-f]+\) - RETURN ([0-9]+)',raw[begin.end():],re.I)
    need(end is not None and end[1]==b'1','game_attach_success_missing')
    finish=begin.end()+end.end()
    need(re.search(re.escape(begin[1])+rb':trace:module:process_attach \(L"GameAssembly.dll",[0-9a-f]+\) - END',raw[finish:],re.I),'game_attach_end_missing')
    return finish

def next_phase(raw,metadata_path):
    expected=('Z:'+str(metadata_path)).lower().replace('\\','/')
    for match in re.finditer(rb'([0-9a-f]+):trace:file:CreateFileW L"([^"\n]*global-metadata.dat)" GENERIC_READ FILE_SHARE_READ ',raw,re.I):
        observed=match[2].decode().replace('\\\\','/').replace('\\','/').lower()
        if observed!=expected:continue
        tid=match[1];following=raw[match.end():]
        returned=re.search(re.escape(tid)+rb':trace:file:CreateFileW returning ([0-9a-f]+)',following,re.I)
        another=re.search(re.escape(tid)+rb':trace:file:CreateFileW L"',following,re.I)
        need(returned is not None and (another is None or returned.start()<another.start()),'game_metadata_open_return')
        handle=int(returned[1],16);need(handle not in (0,0xffffffffffffffff),'game_metadata_open_failed')
        need(re.search(rb'trace:thread:SetThreadDescription \([0-9a-f]+, L"GC Finalizer"\)',following,re.I),'game_gc_worker_missing')
        return dict(name='IL2CPP metadata open and GC finalizer startup',metadata_open_succeeded=True,gc_finalizer_started=True)
    need(False,'game_next_phase_missing')

def inspect(folder,require_initialized=False):
    folder=Path(folder).resolve();r=read(folder/'case.json')
    need(r['scope']=='image_initialization_diagnostic','game_initialization_scope')
    for key in ('producer_ref','inputs_ref','runtime_ref'):checked(r[key])
    i=inputs_admit(Path(r['inputs_ref']['path']).parent);runtime=Path(r['runtime_ref']['path']).parent;v=runtime_admit(runtime)
    need(v['image_admission_correction_overlay']['inputs_ref']==r['inputs_ref'] and r['runtime_sha256']==r['runtime_ref']['sha256'],'game_initialization_binding')
    need(r['outcome'] in ('timeout','exited') and r['error'] is None and r['stream_error'] is None and not r['cleanup_errors'],'game_initialization_run_incomplete')
    for key in ('cleanup','sentinel_cleanup'):
        c=r[key];need(c['complete'] and not c['errors'] and not c['observation_gap'] and c['reaped'] and all(c['reaped'].values()),'game_initialization_cleanup')
    need(r['sentinel_survived'] and r['processes']['sentinel']['exit_code']==0 and r['authorization_before_after_passed'] and r['original_files_unchanged'] and r['runtime_unchanged'],'game_initialization_integrity')
    for side in ('before','after'):
        c=read(folder/side/'control.json');need(c['passed'] and c['runtime_sha256']==r['runtime_sha256'],'game_initialization_authorization')
    raw=supervisor.verify_logs(folder/'run',r)
    for role,events in r['events'].items():need([json.loads(line) for line in raw[(role,'events')].splitlines()]==events,'game_initialization_events')
    events=[e for rows in r['events'].values() for e in rows];native=[e for e in events if 'translation_value' in e];images=[e for e in events if e['event']=='image']
    need(native and all(e['cpu_type']==16777228 and e['translation_value']==0 and e['translation_error']==0 for e in native),'game_initialization_host')
    need(images and all(e['cpu_type']==16777228 for e in images),'game_initialization_images')
    clone=folder/'game/GameAssembly.dll';st=clone.stat();pid=r['processes']['loader']['identity']['pid']
    need(r['target_identity']==dict(dev=st.st_dev,ino=st.st_ino,bytes=st.st_size,sha256=digest(clone.read_bytes())) and r['target_identity']['sha256']==i['pe']['sha256'],'game_initialization_image')
    stderr=raw[('loader','stderr')]
    phases=[m for m in LINE.finditer(stderr) if tuple(map(int,(m[1],m[3],m[4],m[5])))==(pid,st.st_dev,st.st_ino,st.st_size)]
    need(sum(m[6]==b'caller.published' and m[7]==b'00000000' for m in phases)==1 and all(m[7]==b'00000000' for m in phases),'game_initialization_publication')
    loaded=re.findall(rb'trace:loaddll:build_module Loaded L"([^"\n]*GameAssembly.dll)" at ([0-9a-f]+): native',stderr,re.I)
    need(len(loaded)==1,'game_initialization_load_identity')
    path,addr=loaded[0];need(path.decode().replace('\\\\','\\').lower()==('Z:'+str(clone).replace('/','\\')).lower(),'game_initialization_load_path')
    base=int(addr,16);pub=[e for e in r['events']['loader'] if e['event']=='arena_publish' and e['base']==base]
    need(len(pub)==1 and pub[0]['size']==i['pe']['image_bytes'] and pub[0]['code_pages']==0 and pub[0]['relocations']==429566,'game_initialization_guest_publication')
    after=attachment(stderr,base)
    result=dict(scope='game_dll_initialization_observation',dll_initialized=True,run_ref=fact(folder/'case.json'),runtime_ref=r['runtime_ref'],gameassembly_sha256=i['pe']['sha256'],published_relocations=pub[0]['relocations'],outcome=r['outcome'],next_phase_confirmed=False,game_qualified=False,complete_late_load_coverage=False,player_log_ref=fact(folder/'Player.log'))
    if require_initialized:
        metadata=folder/'game/Megabonk_Data/il2cpp_data/Metadata/global-metadata.dat'
        relative=metadata.relative_to(folder/'game')
        source=next(row for row in i['game_files'] if Path(row['path'])==Path(i['game'])/relative)
        need(fact(metadata)['sha256']==source['sha256'],'game_metadata_identity')
        result['next_phase']=next_phase(stderr[after:],metadata)
        result['next_phase_confirmed']=True
        result['scope']='game_dll_initialization_and_next_phase'
    save(folder/'initialization-assessment.json',result);return result,stderr[after:]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--require',choices=['initialized']);a=p.parse_args();r,_=inspect(a.run,a.require=='initialized');print({k:r[k] for k in ('dll_initialized','next_phase_confirmed','outcome','game_qualified')})
