#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build redistributable CPU PEs, binding tools and every generated input."""
from pathlib import Path
import argparse
import json
import platform
import subprocess
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.cpu.generate import generate, REPO
from tools.cpu.corpus import digest
from tools.wine.common import need, encoded, load_json


def abi_assembly(seh=False):
    regs='rbx rbp rsi rdi r12 r13 r14 r15'.split()
    a=['; SPDX-License-Identifier: MIT', '; Original Pear ABI state probe.',
       'BITS 64','DEFAULT REL','section .text code align=16',
       'extern pear_before, pear_after, pear_alignment, pear_callback_alignment',
       'extern pear_native_outer, pear_native_inner, pear_callback_body',
       'global pear_callback', 'pear_callback:',
       '    mov rax, rsp', '    and eax, 15', '    mov [rel pear_callback_alignment], rax',
       '    jmp pear_callback_body']
    if seh:
        a=['; SPDX-License-Identifier: MIT', 'BITS 64', 'DEFAULT REL',
           'section .text code align=16', 'extern pear_before, pear_after, pear_alignment',
           'extern pear_native_outer']
    for slot, name in enumerate(('outer',) if seh else ('outer','inner')):
        a += [f'global pear_abi_{name}',f'pear_abi_{name}:',
              '    mov rax, rsp', '    and eax, 15', f'    mov [rel pear_alignment + {slot*8}], rax']
        # 8 pushes leave the entry alignment unchanged. 200 local bytes include
        # 32 shadow bytes, ten XMM slots, and 8 bytes alignment padding.
        a += [f'    push {r}' for r in regs]
        a += ['    sub rsp, 200']
        a += [f'    movdqu [rsp + {32+i*16}], xmm{i+6}' for i in range(10)]
        a += [f'    mov {r}, {0x1020304050607080+i}' for i,r in enumerate(regs)]
        a += [f'    movdqu xmm{i+6}, [rel pear_patterns + {i*16}]' for i in range(10)]
        for side in ('before','after'):
            a += [f'    mov [rel pear_{side} + {slot*224+i*8}], {r}' for i,r in enumerate(regs)]
            a += [f'    movdqu [rel pear_{side} + {slot*224+64+i*16}], xmm{i+6}' for i in range(10)]
            if side=='before': a += [f'    call pear_native_{name}']
        a += [f'    movdqu xmm{i+6}, [rsp + {32+i*16}]' for i in range(10)]
        a += ['    add rsp, 200']+[f'    pop {r}' for r in reversed(regs)]+['    ret']
    a += ['section .rdata data align=16','pear_patterns:']
    a += [f'    dq {0x1122334455667700+i}, {0x8877665544332200+i}' for i in range(10)]
    return '\n'.join(a)+'\n'


def build(source, output, nasm, clang):
    need(not output.exists(), 'output_exists')
    output.mkdir(parents=True)
    generated=generate(source,output/'sources')
    manifest=load_json(REPO/'tests/cpu/corpus.json')
    log=output/'commands';log.mkdir()
    rows=[];commands=[]
    prefix=['/usr/bin/arch','-arm64'] if sys.platform=='darwin' else []
    def run(argv):
        result=subprocess.run(prefix+[str(x) for x in argv],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        index=len(commands); data=result.stdout
        need(len(data)<=1024*1024, 'build_output_bound')
        (log/f'{index:02}.log').write_bytes(data)
        commands.append(dict(argv=[str(x) for x in prefix+argv],exit_code=result.returncode,log_sha256=digest(data)))
        need(result.returncode==0, 'build_command_failed_'+str(index))
        return data.decode('utf-8',errors='replace').strip()
    try:
        versions=dict(nasm=run([str(nasm),'-v']),clang=run([str(clang),'--version']))
        def compile_case(ident, c, assembly=None, include=None):
            target=output/(ident+'.exe');obj=None
            if assembly:
                obj=output/(ident+'.obj');run([str(nasm),'-f','win64',str(assembly),'-o',str(obj)])
            argv=[str(clang),'--target=x86_64-w64-windows-gnu','-O2','-ffreestanding','-fno-builtin',
                  '-fno-stack-protector','-fms-extensions','-std=c11','-nostdlib',
                  '-Wl,--entry,pear_first_dispatch','-Wl,--subsystem,console','-Wl,--no-insert-timestamp',
                  str(c)]
            if include: argv+=['-I',str(include)]
            if obj: argv+=[str(obj)]
            argv+=['-lkernel32','-lntdll','-o',str(target)]
            run(argv)
            rows.append(dict(id=ident,path=target.name,sha256=digest(target.read_bytes()),
                             source_sha256=digest(c.read_bytes()),
                             asm_sha256=digest(assembly.read_bytes()) if assembly else None,
                             expected_exit=42,kind='asm' if include else 'boundary'))
        for case in manifest['cases']:
            folder=output/'sources'/case['id']
            compile_case(case['id'],REPO/'tests/cpu/runner.c',folder/'case.asm',folder)
        for boundary in manifest['boundaries']:
            if boundary['stage']==2 and boundary['source']:
                compile_case(boundary['id'],REPO/boundary['source']['path'])
        abi=output/'sources/abi.asm';abi.write_text(abi_assembly())
        compile_case('abi-state',REPO/'tests/cpu/abi.c',abi)
        seh=output/'sources/seh.asm';seh.write_text(abi_assembly(seh=True))
        compile_case('seh-unwind',REPO/'tests/cpu/seh.c',seh)
        corresponding=output/'corresponding-source';corresponding.mkdir()
        paths=['tools/cpu/build.py','tools/cpu/generate.py','tools/cpu/corpus.py','tools/wine/common.py',
               'tests/cpu/runner.c','tests/cpu/abi.c','tests/cpu/seh.c','tests/cpu/corpus.json','tests/cpu/sources.json']
        paths += [b['source']['path'] for b in manifest['boundaries'] if b['stage']==2 and b['source']]
        for path in paths:
            target=corresponding/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((REPO/path).read_bytes())
        result=dict(version=1,scope='cpu_pe_build',passed=True,guest_execution=False,cpu_qualified=False,
                    manifest_sha256=generated['manifest_sha256'],generated_sha256=digest(encoded(generated)),
                    build_script_sha256=digest(Path(__file__).read_bytes()),
                    tools={k:dict(sha256=digest(p.read_bytes()),version=versions[k]) for k,p in [('nasm',nasm),('clang',clang)]},
                    build_host=dict(system=platform.system(),machine=platform.machine()),
                    commands=commands,cases=rows)
        (output/'build.json').write_bytes(encoded(result))
        print(json.dumps(dict(passed=True,cases=len(rows),guest_execution=False)))
        return result
    finally:
        (output/'commands.json').write_bytes(encoded(commands))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','output','nasm','clang'): p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    build(a.source,a.output.absolute(),a.nasm.resolve(strict=True),a.clang.resolve(strict=True))
