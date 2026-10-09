# SPDX-License-Identifier: MIT
"""Build original native/guest PE fixtures with the retained LLVM toolchain."""
from pathlib import Path
import argparse, os, struct, subprocess
from tools.wine.image_admission_inputs import REPO,fresh,read,save,fact,checked,need,admit as inputs_admit,pe_facts
SOURCE=REPO/'tests/wine/fixtures/image_admission_pe.c'

def admit(root):
    v=read(Path(root)/'fixtures.json')
    need(v['passed'] and v['producer']==fact(Path(__file__)),'loader_fixture_producer')
    for row in v['dependencies']+v['artifacts']:checked(row)
    for c in v['commands']:
        need(c['exit_code']==0,'loader_fixture_build');checked(c['log'])
    return v

def build(inputs,output):
    i=inputs_admit(inputs);old=Path(i['baseline_repo'])/'.build/task8/inputs1/inputs.json'
    tools=Path(read(old)['tools'])/'llvm-mingw/bin';out=fresh(output)
    result=dict(passed=False,producer=fact(Path(__file__)),dependencies=[fact(SOURCE),fact(old)],commands=[],artifacts=[],roles={})
    try:
        for role,machine in [('aarch64',0xaa64),('x86_64',0x8664)]:
            folder=out/role;folder.mkdir();cc=tools/(role+'-w64-mingw32-clang');result['dependencies'].append(fact(cc.resolve()))
            for name,flags in [('driver.exe',[]),('large.dll',['-DPEAR_DLL','-shared','-Wl,--entry,DllMain','-Wl,--image-base,0x180000000']),('fail.dll',['-DPEAR_DLL','-DPEAR_FAIL_ATTACH','-shared','-Wl,--entry,DllMain','-Wl,--image-base,0x180000000'])]:
                args=['/usr/bin/arch','-arm64',str(cc),'-O2','-nostdlib','-fno-stack-protector',str(SOURCE),'-o',str(folder/name),*flags,'-lkernel32','-Wl,--dynamicbase']
                c=subprocess.run(args,capture_output=True,timeout=60);log=folder/(name+'.log');log.write_bytes(c.stdout+c.stderr)
                result['commands'].append(dict(argv=args,exit_code=c.returncode,log=fact(log)));need(c.returncode==0,'loader_fixture_compile: '+c.stderr.decode())
            for name,base,size in [('required.dll','large.dll',57647104),('ceiling.dll','large.dll',67108864),('beyond.dll','large.dll',67112960),('attach-fail.dll','fail.dll',57647104)]:
                raw=bytearray((folder/base).read_bytes());nt=struct.unpack_from('<I',raw,60)[0];before=struct.unpack_from('<I',raw,nt+24+56)[0]
                need(before<=57647104 and struct.unpack_from('<H',raw,nt+4)[0]==machine,'loader_fixture_geometry')
                struct.pack_into('<I',raw,nt+24+56,size);(folder/name).write_bytes(raw)
            for p in sorted(folder.glob('*.dll')):result['artifacts'].append(fact(p))
            result['artifacts'].append(fact(folder/'driver.exe'))
            result['roles'][role]=dict(driver=fact(folder/'driver.exe'),images={n:pe_facts(folder/n) for n in ('required.dll','ceiling.dll','beyond.dll','attach-fail.dll')})
        result['passed']=True
    finally:save(out/'fixtures.json',result)
    admit(out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.inputs,a.output)
