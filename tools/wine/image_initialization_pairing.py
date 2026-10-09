# SPDX-License-Identifier: MIT
"""Rerun the unchanged native 39-case oracle on the combined candidate."""
from pathlib import Path
from contextlib import contextmanager
import importlib.util
import ast
from types import SimpleNamespace
import sys
import subprocess
from tools.dxmt import common
from tools.dxmt.translated_inputs import REPO,read,save,fact,digest
from tools.fex import memory_wine_run as supervisor,memory_wine_runtime as signing
from tools.fex.integration_run import admission

@contextmanager
def reader():
    # Legacy DXMT tools use local imports. Restore that namespace after use;
    # the isolated adapter only supplies #8's admitted runtime packet mapping.
    previous=sys.modules.get('common');sys.modules['common']=common
    spec=importlib.util.spec_from_file_location('_pear_translated_pairing',REPO/'tools/dxmt/run_pairing.py')
    module=importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        module.assessment_packet=supervisor.assessment_packet
        yield module
    finally:
        if previous is None:sys.modules.pop('common',None)
        else:sys.modules['common']=previous

def current_helpers(helpers,value):
    """Keep the original event/slot oracles with #5's source-extended arena size.

    Only the declared mapping-byte constant differs. Dynamic tail placement,
    sequence, permissions, slot reuse and all 39 bridge oracles stay unchanged.
    """
    size=1588985856
    build=Path(value['build_ref']['path']).parent
    header=build/'source/dlls/ntdll/unix/pear_pe_arena.h'
    inventory=read(build/'source-files.json')
    entry=next(r for r in inventory['files'] if r['path']=='dlls/ntdll/unix/pear_pe_arena.h')
    common.need(digest(header.read_bytes())==entry['sha256'] and
                '_Static_assert(PEAR_ARENA_MAPPING_BYTES == UINT64_C(1588985856)' in header.read_text(),
                'translated_pairing_mapping_source')
    def function(source,name,namespace,transform=None):
        tree=ast.parse(Path(source).read_bytes())
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
        common.need(len(nodes)==1,'translated_pairing_oracle_function')
        if transform:transform(nodes[0])
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(source),'exec'),namespace)
        return namespace[name]
    def mapping_total(node):
        matches=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and
                 len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='total']
        common.need(len(matches)==1 and ast.unparse(matches[0].value)=="limits['interior_bytes'] + LIMITS['bytes'] + 65536",'translated_dynamic_mapping_expression')
        matches[0].value=ast.Constant(size)
    def arena_total(node):
        matches=[(n,i) for n in ast.walk(node) if isinstance(n,ast.Dict)
                 for i,k in enumerate(n.keys) if isinstance(k,ast.Constant) and k.value=='mapping_bytes']
        common.need(len(matches)==1,'translated_arena_mapping_expression')
        n,i=matches[0]
        common.need(ast.unparse(n.values[i])=="limits['interior_bytes'] + limits['alignment'] + dynamic_bytes",'translated_arena_mapping_original')
        n.values[i]=ast.Constant(size)
    dyn=dict(vars(helpers.dynamic))
    function(REPO/'tools/wine/dynamic_evidence.py','validate_budget',dyn,mapping_total)
    function(REPO/'tools/wine/dynamic_evidence.py','_process',dyn)
    api=dict(vars(helpers.api));api['validate_budget']=dyn['validate_budget']
    function(REPO/'tools/wine/api_runner.py','assess_arena_events',api,arena_total)
    return SimpleNamespace(**{**vars(helpers),'api':SimpleNamespace(**api),'dynamic':SimpleNamespace(**dyn)})

def without_desktop_menu(raw):
    """Disable only Wine's optional XDG desktop integration in synthetic tests.

    The original initialized prefix remains unchanged. This is test setup,
    never a waiver of a started process's failure or of the native 39 cases.
    """
    lines=raw.splitlines(keepends=True)
    section=None;removed=[];kept=[]
    for line in lines:
        if line.startswith(b'['):section=line.split(b']',1)[0]+b']'
        if line.startswith(b'"winemenubuilder"='):
            common.need(section==b'[Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\RunServices]',
                        'translated_menu_registry_scope')
            common.need(line.rstrip()==b'"winemenubuilder"="C:\\\\windows\\\\system32\\\\winemenubuilder.exe -a -r"',
                        'translated_menu_registry_value')
            removed.append(line)
        else:kept.append(line)
    common.need(len(removed)==1,'translated_menu_registry_count')
    return b''.join(kept)

def run(runtime,output,reuse,seed,diagnostic=False):
    from tools.wine.image_admission_inputs import fresh
    from tools.dxmt.translated_runtime import admit_build
    from tools.wine.image_admission_correction_runtime import admit as admit_runtime
    v=admit_runtime(runtime)
    common.need(v['kind']=='translated_graphics_development_runtime' and v['passed'],'translated_pairing_runtime')
    common.need(fact(v['build_ref']['path'])==v['build_ref'],'translated_pairing_build')
    admit_build(Path(v['build_ref']['path']).parent)
    from tools.dxmt.translated_check import device
    from tools.fex.integration_run import prefix_inventory
    device(seed,runtime)
    template=seed/'run/prefix';inventory=prefix_inventory(template)
    inf=runtime/signing.PAYLOAD/'share/wine/wine.inf'
    common.need((template/'.update-timestamp').read_text().strip()==str(int(inf.stat().st_mtime)),
                'translated_pairing_prefix_update')
    output=fresh(output);(output/'producer.py').write_bytes(Path(__file__).read_bytes());save(output/'inputs.json',dict(runtime_ref=fact(runtime/'runtime.json'),
            pairing_reader=fact(REPO/'tools/dxmt/run_pairing.py'),adapter=fact(Path(__file__)),
            seed_ref=fact(seed/'case.json'),prefix_inventory=inventory,cold_prefix_initialization=False,diagnostic_only=diagnostic))
    admission(runtime,v,output/'before',reuse)
    v['entrypoints']['fixture_pe']=v['fixtures']['pairing']['path']
    v['entrypoints']['winemac_native']=signing.PAYLOAD+'/lib/wine/aarch64-unix/winemac.so'
    work=output/'run';work.mkdir()
    try:
        with reader() as pairing:
            original_environment=pairing.environment
            def seeded_environment(work,prefix,nonce):
                common.need(not list(prefix.iterdir()),'translated_pairing_prefix_not_empty')
                common.need(prefix_inventory(template)==inventory,'translated_pairing_seed_changed')
                subprocess.run(['/bin/cp','-cRp',str(template)+'/.',str(prefix)],check=True,timeout=30)
                common.need(prefix_inventory(prefix)==inventory,'translated_pairing_prefix_clone')
                if not diagnostic:
                    registry=prefix/'system.reg';before=registry.read_bytes()
                    after=without_desktop_menu(before);registry.write_bytes(after)
                    save(output/'prefix-configuration.json',dict(
                        scope='synthetic_native_pairing_prefix_only',
                        operation='disable_optional_XDG_desktop_menu_autorun',
                        before_sha256=digest(before),after_sha256=digest(after),
                        original_seed_unchanged=prefix_inventory(template)==inventory))
                env=original_environment(work,prefix,nonce)
                if diagnostic:env['WINEDEBUG']='-all,+process,+menubuilder,err+all'
                return env
            pairing.environment=seeded_environment
            with pairing.wine_helpers(REPO) as helpers:
                result,assessment=pairing.run_case(runtime,v,work,current_helpers(helpers,v))
        save(output/'result.json',dict(passed=True,runtime_ref=fact(runtime/'runtime.json'),case_ref=fact(work/'case.json'),observations=assessment))
    finally:admission(runtime,v,output/'after',reuse)

def verify(runtime,output):
    import re
    from tools.dxmt.translated_check import device
    from tools.fex.integration_run import prefix_inventory
    from tools.wine.image_admission_correction_runtime import admit as admit_runtime
    v=admit_runtime(runtime);inputs=read(output/'inputs.json');result=read(output/'result.json')
    common.need(not inputs['diagnostic_only'] and inputs['runtime_ref']==fact(runtime/'runtime.json') and
                result['runtime_ref']==inputs['runtime_ref'] and result['passed'] is True,'translated_pairing_input_binding')
    common.need(inputs['pairing_reader']==fact(REPO/'tools/dxmt/run_pairing.py') and
                inputs['adapter']==fact(Path(__file__)) and
                digest((output/'producer.py').read_bytes())==inputs['adapter']['sha256'],'translated_pairing_producers')
    common.need(inputs['seed_ref']==fact(inputs['seed_ref']['path']),'translated_pairing_seed_binding')
    seed=Path(inputs['seed_ref']['path']).parent;device(seed,runtime)
    common.need(prefix_inventory(seed/'run/prefix')==inputs['prefix_inventory'],'translated_pairing_seed_inventory')
    configuration=read(output/'prefix-configuration.json')
    raw_registry=(seed/'run/prefix/system.reg').read_bytes()
    common.need(configuration==dict(scope='synthetic_native_pairing_prefix_only',
        operation='disable_optional_XDG_desktop_menu_autorun',before_sha256=digest(raw_registry),
        after_sha256=digest(without_desktop_menu(raw_registry)),original_seed_unchanged=True),
        'translated_pairing_configuration')
    common.need(result['case_ref']==fact(output/'run/case.json'),'translated_pairing_case_binding')
    for side in ('before','after'):
        control=read(output/side/'control.json')
        common.need(control['passed'] is True and control['runtime_sha256']==inputs['runtime_ref']['sha256'],'translated_pairing_authorization')
    v['entrypoints']['fixture_pe']=v['fixtures']['pairing']['path']
    v['entrypoints']['winemac_native']=signing.PAYLOAD+'/lib/wine/aarch64-unix/winemac.so'
    case=read(output/'run/case.json')
    with reader() as pairing:
        raw=pairing.verify_logs(output/'run',case)
        with pairing.wine_helpers(REPO) as helpers:
            actual=pairing.assess_case(case,raw,runtime,v,current_helpers(helpers,v))
        _,diagnostics=pairing.native_rows(raw[('loader','stderr')])
    common.need(actual==result['observations'],'translated_pairing_observations')
    pid=case['processes']['loader']['identity']['pid']
    for marker in ('Metal API Validation Enabled','Metal GPU Validation Enabled'):
        common.need(re.search(rb'wine\['+str(pid).encode()+rb':\d+\] '+marker.encode(),diagnostics) is not None,
                    'translated_pairing_validation')
    common.need(not re.search(rb'failed assertion|validation error|Exception c0000005|err:',diagnostics,re.I),
                'translated_pairing_diagnostic_error')
    return dict(passed=True,case_count=actual['case_count'],physical_lifetime=actual['physical_lifetime'],
                runtime_ref=fact(runtime/'runtime.json'),run_ref=fact(output/'run/case.json'),
                inputs_ref=fact(output/'inputs.json'),diagnostics_sha256=digest(diagnostics),
                validation_review='no_required_error_observed',game_qualified=False)
