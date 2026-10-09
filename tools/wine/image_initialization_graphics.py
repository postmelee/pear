# SPDX-License-Identifier: MIT
"""Retain #8 graphics oracles while admitting the exact #40 candidate."""
from pathlib import Path
import ast
from tools.wine.image_admission_inputs import REPO,read,fact,need,save
from tools.wine.image_admission_correction_runtime import admit
from tools.dxmt import translated_check as device_reader,translated_render_check as render_reader,translated_present_check as present_reader
from tools.dxmt.translated_surface_check import controls
from tools.wine import image_initialization_pairing as pairing

def bind(run,runtime):
    value=admit(runtime);record=read(run/'case.json')
    need(record['runtime_sha256']==fact(runtime/'runtime.json')['sha256'],'image_graphics_candidate')
    need(fact(run/'producer.py')['sha256']==fact(REPO/'tools/wine/image_initialization_regression_run.py')['sha256'],'image_graphics_producer')
    launch=next(r for r in record['launches'] if r['role']=='loader')
    need(launch['argv'][-1]==str(runtime/value['fixtures'][record['fixture_id']]['path']),'image_graphics_launch')
    return value

def oracle(module,presentation=False):
    # Only candidate admission and the native pairing adapter change. All
    # pixel, shader, frame, callback, resource and error checks remain upstream.
    source=Path(module.__file__);tree=ast.parse(source.read_bytes())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify']
    need(len(nodes)==1,'image_graphics_oracle')
    node=nodes[0];count=2 if presentation else 1
    need(isinstance(node.body[count-1],ast.If) and 'managed_surface_overlay' in ast.unparse(node.body[count-1]),'image_graphics_admission_shape')
    node.body[:count]=ast.parse('value=admit(runtime)').body
    imports=[n for n in ast.walk(node) if isinstance(n,ast.ImportFrom) and n.module=='tools.dxmt.translated_pairing']
    need(len(imports)==(0 if presentation else 1),'image_graphics_pairing_shape')
    for n in imports:n.module='tools.wine.image_initialization_pairing'
    namespace={**vars(module),'admit':admit}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),namespace)
    return namespace['verify']

def verify(run,runtime,native=None):
    run=Path(run).resolve();runtime=Path(runtime).resolve();bind(run,runtime)
    case=read(run/'case.json')['fixture_id']
    if case=='device':result=device_reader.device(run,runtime)
    elif case in ('rendering','rendering-original'):
        need(native is not None,'image_graphics_native_required')
        result=oracle(render_reader)(run,runtime,Path(native).resolve())
        result['native_core_unchanged']=False
    elif case=='presentation-original':
        # Match #8 stage_three's original scalar-recovery gate. The dedicated
        # presentation-frames case retains all 18 visible-frame/lifetime checks.
        value=read(runtime/'runtime.json');record,raw=device_reader.boundary(run,runtime,value)
        result_terminal=present_reader.terminal(raw[('loader','stdout')])
        device_reader.backend(run,runtime,value,record,raw,result_terminal['modules'])
        need(record['fixture_id']=='presentation-original' and b'Unaligned.repaired' in raw[('loader','stderr')],'image_original_recovery')
        result=dict(passed=True,scope='original_scalar_presentation_recovery',run_ref=fact(run/'case.json'),runtime_ref=fact(runtime/'runtime.json'),
                    recovery_observed=True,qualified_display_timing=False,game_qualified=False)
    elif case in ('presentation','presentation-frames'):
        result=oracle(present_reader,True)(run,runtime)
    else:need(False,'image_graphics_case')
    result['image_admission_checker']=fact(Path(__file__))
    save(run/'graphics-assessment.json',result);return result

def native(runtime,folder):
    result=pairing.verify(runtime,folder)
    raw=(folder/'run/loader.stderr.log').read_bytes();result['surface_v2']=controls(raw)
    save(folder/'graphics-assessment.json',result);return result
