# SPDX-License-Identifier: MIT
"""Fail closed on incomplete translated-device execution and backend evidence."""
from pathlib import Path
import argparse
import json
import re
from tools.dxmt.translated_inputs import REPO,read,save,digest,need,fact
from tools.fex import memory_wine_runtime as signing,memory_wine_run as supervisor


def terminal(raw):
    lines=raw.decode('utf-8').splitlines()
    need(lines and json.loads(lines[0]).get('record_kind')=='pear_bootstrap_helper','translated_bootstrap_record')
    graphics=lines[1:]
    need(graphics and graphics[0]=='PEAR_GRAPHICS_BEGIN suite=device version=1' and
         graphics[-1]=='PEAR_GRAPHICS_END suite=device cases=1 passed=1','translated_terminal_incomplete')
    devices=[r for r in graphics if r.startswith('PEAR_GRAPHICS_DEVICE ')]
    need(len(devices)==1 and re.fullmatch(r'PEAR_GRAPHICS_DEVICE hr=00000000 level=b000 device=0*[1-9a-fA-F][0-9a-fA-F]* context=0*[1-9a-fA-F][0-9a-fA-F]*',devices[0]),'translated_device_failed')
    modules={}
    for line in graphics:
        if not line.startswith('PEAR_GRAPHICS_MODULE '):continue
        m=re.fullmatch(r'PEAR_GRAPHICS_MODULE name=(\S+) base=([0-9a-fA-F]+) path=(.+)',line)
        need(m is not None and m[1] not in modules and int(m[2],16)>0,'translated_module_record')
        modules[m[1].lower()]=dict(base=int(m[2],16),path=m[3])
    need(set(modules)=={'d3d11.dll','dxgi.dll','winemetal.dll'},'translated_module_set')
    need(len([r for r in graphics if r.startswith('PEAR_GRAPHICS_ADAPTER ')])==1 and len(graphics)==7,'translated_device_record_set')
    return modules


def boundary(run,runtime,value):
    r=read(run/'case.json')
    need(r['kind']=='translated_graphics_observation' and r['runtime_sha256']==digest((runtime/'runtime.json').read_bytes()),'translated_run_runtime')
    need(not r.get('diagnostic_only',False),'translated_diagnostic_not_qualification')
    need(r['outcome']=='exited' and r['processes']['loader']['exit_code']==42 and
         r['error'] is None and r['stream_error'] is None and r['cleanup_errors']==[],'translated_execution_failed')
    for key in ('cleanup','sentinel_cleanup'):
        c=r[key];need(c['complete'] is True and c['errors']==[] and not c['observation_gap'] and all(c['reaped'].values()),'translated_cleanup_incomplete')
    need(r['sentinel_survived'] is True and r['processes']['sentinel']['exit_code']==0 and r['authorization_before_after_passed'] is True,'translated_ownership_failed')
    for side in ('before','after'):
        c=read(run/side/'control.json');need(c['passed'] is True and c['runtime_sha256']==r['runtime_sha256'],'translated_authorization_pair')
    raw=supervisor.verify_logs(run/'run',r)
    for role,events in r['events'].items():
        need([json.loads(line) for line in raw[(role,'events')].splitlines()]==events,'translated_events_changed')
    events=[e for rows in r['events'].values() for e in rows]
    native=[e for e in events if 'translation_value' in e]
    need(native and all(e['cpu_type']==16777228 and e['translation_value']==0 and e['translation_error']==0 for e in native),'translated_host_not_native')
    images=[e for e in events if e['event']=='image']
    need(images and all(e['cpu_type']==16777228 for e in images),'translated_image_not_arm64')
    need(any(e['event']=='stage3_guest_exit' and e['exit_code']==42 for e in r['events']['loader']),'translated_guest_exit_missing')
    return r,raw


def device(run,runtime):
    value=read(runtime/'runtime.json');r,raw=boundary(run,runtime,value)
    need(r['fixture_id']=='device' and r['fixture_sha256']==value['fixtures']['device']['sha256'],'translated_fixture_binding')
    modules=terminal(raw[('loader','stdout')]);stderr=raw[('loader','stderr')]
    backend(run,runtime,value,r,raw,modules)
    return dict(passed=True,scope='translated_device_only',run_ref=fact(run/'case.json'),runtime_ref=fact(runtime/'runtime.json'),
                no_rosetta_in_observed_processes_and_images=True,complete_late_load_coverage=False,game_qualified=False)

def backend(run,runtime,value,r,raw,modules):
    stderr=raw[('loader','stderr')]
    loader=next(x for x in r['launches'] if x['role']=='loader')
    need(loader['argv'][-1]==str(runtime/value['fixtures'][r['fixture_id']]['path']),'translated_fixture_launch')
    pid=r['processes']['loader']['identity']['pid']
    for marker in ('Metal API Validation Enabled','Metal GPU Validation Enabled'):
        need(re.search(rb'wine\['+str(pid).encode()+rb':\d+\] '+marker.encode(),stderr) is not None,'translated_validation_unobserved')
    need(b'Pear FEX init ProcessInit.complete: status=00000000' in stderr and b'Pear FEX init ECGate.' in stderr,'translated_fex_unobserved')
    need(not re.search(rb'Exception c0000005|Pear FEX assertion:|err:sync:|failed assertion|validation error',stderr,re.I),'translated_required_error')
    for name,row in modules.items():
        need(row['path'].lower()=='c:\\windows\\system32\\'+name,'translated_module_fallback')
        source=runtime/signing.PAYLOAD/'lib/wine/aarch64-windows'/name
        actual=run/'run/prefix/drive_c/windows/system32'/name
        need(actual.is_file() and digest(actual.read_bytes())==digest(source.read_bytes()),'translated_loaded_module_bytes')
        load=re.search(rb'Loaded L"C:\\\\windows\\\\system32\\\\'+re.escape(name.encode())+rb'" at ([0-9a-fA-F]+): builtin',stderr,re.I)
        need(load is not None and int(load[1],16)==row['base'],'translated_loaded_module_address')
    images=[e for e in r['events']['loader'] if e['event']=='image']
    for name in ('winemac.so','winemetal.so','libarm64ecfex.so'):
        expected=str((runtime/signing.PAYLOAD/'lib/wine/aarch64-unix'/name).resolve())
        need(any(str(Path(e['path']).resolve())==expected for e in images),'translated_backend_image_missing')
    need(any('/Metal.framework/' in e['path'] for e in images),'translated_metal_unobserved')

def stage_one(index_path):
    from tools.dxmt.translated_runtime import admit_build
    from tools.dxmt.translated_pairing import verify as pairing_verify
    from tools.dxmt.translated_regression import corpus,ordered
    from tools.fex.integration_run import admission
    index=read(index_path)
    need(index['scope']=='translated_graphics_stage1' and index['stage']==1,'translated_stage_index')
    runtime=Path(index['runtime']).resolve(strict=True);v=read(runtime/'runtime.json')
    need(runtime.parent==REPO/'.build/task8' and v['passed'] is True and not v.get('diagnostic_only'),
         'translated_stage_runtime')
    need(v['producer_sha256']==digest((REPO/'tools/dxmt/translated_runtime.py').read_bytes()),'translated_stage_producer')
    _,inputs=admit_build(Path(v['build_ref']['path']).parent)
    for key,module in [('owner_correction_ref','translated_owner'),('fex_correction_ref','translated_fex')]:
        need(key in v and fact(v[key]['path'])==v[key],'translated_stage_correction')
        import importlib
        m=importlib.import_module('tools.dxmt.'+module)
        (m.admit if module=='translated_owner' else m.admit_build)(Path(v[key]['path']).parent)
    output=Path(index['output']).absolute()
    from tools.dxmt.translated_inputs import fresh
    output=fresh(output)
    reuse=Path(inputs['graphics_repo']);cpu=Path(inputs['cpu_repo'])
    admission(runtime,v,output/'current',reuse)
    device_result=device(Path(index['device']),runtime)
    pairing_result=pairing_verify(runtime,Path(index['pairing']))
    # These readers require existing exact observations. They cannot launch a
    # missing test in replay mode, and preserve unsupported CPU features.
    cpu_result=corpus(runtime,cpu,reuse,output/'cpu.json',index['run_name'],verify_only=True)
    ordering_result=ordered(runtime,cpu,reuse,output/'ordering.json',index['run_name'],verify_only=True)
    result=dict(passed=True,stage=1,runtime_ref=fact(runtime/'runtime.json'),index_ref=fact(index_path),
                device=device_result,native_pairing=pairing_result,
                cpu=dict(cases=len(cpu_result['cases']),unsupported=[r['id'] for r in cpu_result['cases'] if r['status']!='passed']),
                ordering=dict(measured_pairs=ordering_result['candidate']['measured_pairs'],
                              workers=len(ordering_result['candidate']['workers'])),
                game_qualified=False,rendering_qualified=False,complete_late_load_coverage=False)
    save(output/'stage.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path)
    p.add_argument('--runtime',type=Path);p.add_argument('--require-stage',type=int)
    p.add_argument('--qualification',type=Path);p.add_argument('--pairing',type=Path)
    p.add_argument('--rendering',type=Path);p.add_argument('--cpu-boundaries',type=Path)
    a=p.parse_args()
    if a.qualification:
        need(a.require_stage in (1,4),'translated_stage_not_implemented')
        if a.require_stage==4:
            from tools.dxmt.translated_qualification import verify
            v=verify(a.qualification.resolve())
        else:v=stage_one(a.qualification.resolve())
    else:
        need(a.run is not None and a.runtime is not None and a.require_stage in (None,2,3),'translated_stage_requires_full_index')
        if a.require_stage==3:
            from tools.dxmt.translated_present_check import stage_three
            need(a.pairing is not None and a.rendering is not None and a.cpu_boundaries is not None,'present_stage_dependencies')
            v=stage_three(a.run.resolve(),a.runtime.resolve(),a.pairing.resolve(),a.rendering.resolve(),a.cpu_boundaries.resolve());save(a.run/'stage3-assessment.json',v)
        elif a.require_stage==2:
            from tools.dxmt.translated_render_check import verify
            v=verify(a.run.resolve(),a.runtime.resolve(),a.pairing.resolve() if a.pairing else None);save(a.run/'rendering-assessment.json',v)
        else:
            v=device(a.run.resolve(),a.runtime.resolve());save(a.run/'device-assessment.json',v)
    print(json.dumps(v))
