# SPDX-License-Identifier: MIT
"""Private, identity-bound inputs for Task #40 image-admission diagnosis."""
from pathlib import Path
import argparse, hashlib, json, os, struct, subprocess, sys
from tools.wine.common import need
from tools.dxmt.translated_inputs import fact, read, save, digest
REPO = Path(__file__).resolve().parents[2]
BASELINE = 'f90b2a601f556595a07b38bfa695def75b7f1def9bb1018e7dacb73bf7444f5f'
BUILD = '1ba8ac8b92ba72ef54b85ef3a02d973660eb5168d89c5eaa393d085363f2dc90'
PATCH = REPO/'runtime/wine/patches/gameassembly/0001-admission-diagnostics.patch'

def fresh(path):
    path=Path(path).absolute(); parent=REPO/'.build/task40'
    need(path.parent==parent and not path.exists() and not path.is_symlink(),'image_fresh_output')
    parent.mkdir(parents=True,exist_ok=True)
    need(parent.resolve()==parent,'image_output_alias');path.mkdir(mode=0o700);return path

def checked(row):
    need(fact(row['path'])==row,'image_input_changed');return Path(row['path'])

def baseline(repo, seed=False):
    # Execute the unchanged historical reader in its own import namespace.
    code="from pathlib import Path; from tools.dxmt.translated_surface_runtime import admit; r=Path('.build/task8/surface-runtime4'); admit(r.resolve())"
    if seed:code+="; from tools.dxmt.translated_check import device; device(Path('.build/task8/device15').resolve(),r.resolve())"
    result=subprocess.run([sys.executable,'-B','-c',code],cwd=repo,capture_output=True,timeout=300,
                          env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')})
    need(result.returncode==0,'image_baseline_admission: '+result.stderr.decode(errors='replace')[-1500:])

def pe_facts(path):
    data=Path(path).read_bytes()
    def u(fmt,off):
        need(0<=off and off+struct.calcsize(fmt)<=len(data),'image_pe_bounds')
        return struct.unpack_from('<'+fmt,data,off)[0]
    need(u('H',0)==0x5a4d,'image_dos');nt=u('I',60);need(u('I',nt)==0x4550,'image_nt')
    opt=nt+24;need(u('H',opt)==0x20b,'image_pe64');section=opt+u('H',nt+20);rows=[]
    for i in range(u('H',nt+6)):
        at=section+40*i
        rows.append(dict(rva=u('I',at+12),virtual=u('I',at+8),raw_bytes=u('I',at+16),raw_offset=u('I',at+20),flags=u('I',at+36)))
    image=u('I',opt+56);reloc_rva=u('I',opt+112+5*8);reloc_bytes=u('I',opt+116+5*8)
    return dict(machine=u('H',nt+4),flags=u('H',nt+22),dll_flags=u('H',opt+70),image_bytes=image,
                section_alignment=u('I',opt+32),file_alignment=u('I',opt+36),sections=rows,
                slot_bytes=(image+65535)//65536*65536,page_metadata_bytes=image//4096,
                relocation_directory_bytes=reloc_bytes,relocation_rva=reloc_rva,
                conservative_relocation_array_bytes=(reloc_bytes//2)*4,
                staging_bytes=image,sha256=digest(data),file_bytes=len(data))

def prepare(repo, output):
    repo=repo.resolve(strict=True);root=repo/'.build/task8';out=fresh(output)
    rv=fact(root/'surface-runtime4/runtime.json');bv=fact(root/'build3/build.json')
    need(rv['sha256']==BASELINE and bv['sha256']==BUILD,'image_baseline_identity')
    print('admitting retained runtime and prefix evidence',flush=True);baseline(repo,True)
    prior=read(root/'megabonk-start1/case.json');files=prior['source_files']
    need(len(files)==69 and all(fact(r['path'])==r for r in files),'image_game_changed')
    game=next(Path(r['path']).parent for r in files if Path(r['path']).name=='GameAssembly.dll')
    cpu=read(Path(read(Path(rv['path']))['prior_runtime_ref']['path']))
    native=next(r for r in cpu['source_ledger'] if r['runtime_path'].endswith('/ntdll.so'))
    native_build=Path(native['origin_root'])
    need(digest((native_build/native['origin']['path']).read_bytes())==native['origin']['sha256'],'image_native_origin')
    value=dict(kind='image_admission_inputs',diagnostic_only=True,producer=fact(Path(__file__)),
               baseline_repo=str(repo),runtime_ref=rv,build_ref=bv,native_build_ref=fact(native_build/'build.json'),
               failure_ref=fact(root/'megabonk-start1/case.json'),seed_ref=prior['prefix_origin']['seed_ref'],
               snapshot_ref=prior['snapshot_ref'],game=str(game),game_files=files,
               pe=pe_facts(game/'GameAssembly.dll'),patch_ref=fact(PATCH),series_ref=fact(PATCH.with_suffix('.json')))
    save(out/'inputs.json',value);print(json.dumps(value['pe']),flush=True)

def admit(root):
    v=read(Path(root)/'inputs.json')
    need(v['kind']=='image_admission_inputs' and v['producer']==fact(Path(__file__)),'image_input_producer')
    for k in ('runtime_ref','build_ref','native_build_ref','failure_ref','seed_ref','snapshot_ref','patch_ref','series_ref'):checked(v[k])
    need(v['runtime_ref']['sha256']==BASELINE and v['build_ref']['sha256']==BUILD,'image_input_pin')
    for row in v['game_files']:checked(row)
    need(pe_facts(Path(v['game'])/'GameAssembly.dll')==v['pe'],'image_pe_changed')
    return v

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.baseline_repo,a.output)
