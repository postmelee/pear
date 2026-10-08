# SPDX-License-Identifier: MIT
"""Admit immutable CPU/graphics inputs for the declared translated D3D11 route."""
from pathlib import Path
import argparse
import hashlib
import json
import stat
from tools.wine.common import need, relative, read_relative, decode_json
from tools.cpu.runtime import admit_pair
from tools.cpu.fex_build import admit_correction
from tools.fex import memory_wine_runtime as signing

REPO=Path(__file__).resolve().parents[2]
GRAPHICS_BUILD='5eb2a22a1e6132043ba3be3985683573e23f81893f91b9729b55ef00fb57a31d'
GRAPHICS_RECONSTRUCTION='be94089919d2314e08ae4482db292d150632a40cdb8f8dffebb122ea1ac2c556'
CPU_RUNTIME='00d444592a45b4afbda83c79805d4d8939cdedab27972af3c6ea0488845a98fe'
FEX_DLL='2925abaafea4d4c3293c30e778629208b507d9690e7d2b128e9b500733608364'

def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return decode_json(Path(path).read_bytes(),64*1024**2,max_nodes=1000000)
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def pin(path,expected):
    raw=Path(path).read_bytes();need(digest(raw)==expected,'translated_input_changed');return decode_json(raw,64*1024**2,max_nodes=1000000)
def fact(path):
    p=Path(path);need(p.is_file() and not p.is_symlink(),'translated_regular_file')
    return dict(path=str(p),sha256=digest(p.read_bytes()),size_bytes=p.stat().st_size)
def fresh(path):
    p=Path(path).absolute();parent=REPO/'.build/task8'
    need(p.parent==parent and not p.exists() and not p.is_symlink(),'translated_fresh_output')
    parent.mkdir(parents=True,exist_ok=True);need(parent.resolve()==parent,'translated_output_alias')
    p.mkdir(mode=0o700);return p

def check_files(root,rows):
    need(rows and len({r['path'] for r in rows})==len(rows),'translated_inventory_set')
    for row in rows:
        relative(row['path']);p=Path(root)/row['path'];raw=read_relative(root,row['path'],64*1024**2)
        need(digest(raw)==row['sha256'] and len(raw)==row['size_bytes'],'translated_inventory_changed')
        if 'mode' in row:need(stat.S_IMODE(p.stat().st_mode)==row['mode'],'translated_inventory_mode')

def prepare(cpu_repo,wine_repo,graphics_repo,output):
    output=fresh(output);v=dict(kind='translated_graphics_inputs',passed=False,guest_execution=False)
    try:
        receipts=admit_pair(wine_repo)
        cpu=cpu_repo/'.build/task6/stage3-fex3';correction=admit_correction(cpu,receipts)
        need(correction['dll_sha256']==FEX_DLL,'translated_final_cpu')
        runtime=cpu_repo/'.build/task6/stage3-regression-runtime1';rv=pin(runtime/'runtime.json',CPU_RUNTIME)
        helpers,_=signing.signing_helpers(graphics_repo);reader=helpers.legacy(REPO)
        need(reader.inventory(runtime/signing.BUNDLE)==rv['bundle_inventory'],'translated_cpu_payload')
        graphics=graphics_repo/'.build/task7/stage5-deterministic8';gv=pin(graphics/'build.json',GRAPHICS_BUILD)
        reconstruction=graphics_repo/'.build/task7/stage5-reserved-comparison2'
        replay=pin(reconstruction/'reproduction.json',GRAPHICS_RECONSTRUCTION)
        need(replay['reconstruction_complete'] is True,'translated_graphics_incomplete')
        check_files(graphics,gv['artifacts'])
        for component,value in gv['source'].items():check_files(graphics/component/'source',value['after_files'])
        for name,value in gv['producers'].items():need(digest((graphics_repo/name).read_bytes())==value,'translated_graphics_producer')
        source=wine_repo/'.build/task5/stage6-wine3'
        series=read(REPO/'runtime/dxmt/patches/series.json');patch=series['patches'][0]
        need(patch['component']=='wine','translated_patch_component')
        for row in patch['changes']:
            p=source/'source'/row['path'];actual=digest(p.read_bytes()) if p.exists() else None
            need(actual==row['before_sha256'],'translated_bridge_preimage')
        toolroot=Path(gv['wine_tools_ref']['path'])
        need(digest((toolroot/'prepared.json').read_bytes())==gv['wine_tools_ref']['sha256'],'translated_tools_receipt')
        v.update(passed=True,wine_repo=str(wine_repo),cpu_repo=str(cpu_repo),graphics_repo=str(graphics_repo),
                 wine=str(source),cpu=str(cpu),cpu_runtime=str(runtime),graphics=str(graphics),tools=str(toolroot),
                 baseline_receipts=receipts,cpu_correction=correction,
                 bindings=[fact(p) for p in [source/'build.json',cpu/'build.json',runtime/'runtime.json',graphics/'build.json',reconstruction/'reproduction.json',toolroot/'prepared.json',REPO/'runtime/dxmt/patches/series.json']],
                 artifacts=gv['artifacts'],graphics_scope='retained_native_evidence_not_translated_graphics',
                 tool_files=[fact((toolroot/'llvm-mingw/bin'/name).resolve()) for name in ['clang','lld','llvm-ar','llvm-dlltool','llvm-objcopy']],
                 producer_sha256=digest(Path(__file__).read_bytes()))
    finally:save(output/'inputs.json',v)
    print(json.dumps(dict(passed=True,bridge_preimages=len(patch['changes']),graphics_artifacts=len(gv['artifacts']))),flush=True)

def admit(root):
    v=read(Path(root)/'inputs.json');need(v['kind']=='translated_graphics_inputs' and v['passed'] is True,'translated_inputs_incomplete')
    need(v['producer_sha256']==digest(Path(__file__).read_bytes()),'translated_input_producer')
    for row in v['bindings']+v['tool_files']:need(fact(row['path'])==row,'translated_binding_changed')
    check_files(Path(v['graphics']),v['artifacts']);return v

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('cpu-repo','wine-repo','graphics-repo','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();prepare(a.cpu_repo.resolve(),a.wine_repo.resolve(),a.graphics_repo.resolve(),a.output)
