#!/usr/bin/env python3
"""Compile-only FEX prerequisite checks; no PE/Wine/FEX runtime execution."""
from __future__ import annotations
import argparse
import hashlib
import os
import re
from pathlib import Path
import struct
import sys
import tarfile
if __package__:
    from .common import Error, REPO, bounded_command, load_json, need, operation_output, read_relative, record, relative, sha256, write_json
    from .prepare import verify_prepared
    from .tools import verify_tools, wine_readers
else:
    from common import Error, REPO, bounded_command, load_json, need, operation_output, read_relative, record, relative, sha256, write_json
    from prepare import verify_prepared
    from tools import verify_tools, wine_readers


MACHINES={'aarch64':0xaa64,'arm64ec':0xa641}
BASE_SERIES='39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086'
BASE_SOURCE='2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7'
BASE_BUILD_SHA={'native':'f7041374d7cdc86ea2991f859c8c102e369ed2247cb69a3647f4b9ddfae2f1eb','companion':'d71d69ab5b5612d33b5fd73997d1e38f09b2a72a9625cd9c954817bbf05c77ad'}
BASE_ARTIFACT_SHA={'native':'15f6021af281269baac31437445369d0b28bd3c89e9329989db962b0edb852d9','companion':'2043ecc6a3310ed8044ba93936694330f7d16557407eac626d244fea037462a6'}
FALSE_FLAGS=('component_built','pe_execution','wine_runtime_execution','fex_dispatch','runtime_qualified','game_qualified','distribution_qualified')


def validate_ec_archive_index(entries):
    """Validate LLVM's /<ECSYMBOLS>/ index as metadata, never a COFF object.

    Reuse decision: bounded byte-format interpretation of pinned LLVM23
    ArchiveWriter.cpp writeECSymbols and Archive.cpp ec_symbols/getMember.
    Indices are 1-based into the second COFF linker member's offset table.
    """
    ec = [body for _,name,body in entries if name=='/<ECSYMBOLS>/']
    if not ec:
        return None
    symbols = [body for _,name,body in entries if name=='/']
    need(len(ec)==1 and len(symbols)==2, 'ec_index_linker_members')
    second = symbols[1]
    need(len(second)>=8, 'ec_linker_table_bounds')
    count = struct.unpack_from('<I',second)[0]
    end = 4+count*4
    need(0<count<=65535 and end+4<=len(second), 'ec_linker_table_bounds')
    offsets = struct.unpack_from('<'+'I'*count,second,4)
    regular = {offset for offset,name,_ in entries if name not in ('/','//','/SYM64/','/<ECSYMBOLS>/')}
    need(len(set(offsets))==count and all(offset in regular for offset in offsets), 'ec_linker_member_reference')
    def names_and_indices(body,start,number):
        end = start+number*2
        need(0<number<=1000000 and end<=len(body), 'ec_symbol_index_bounds')
        indices = struct.unpack_from('<'+'H'*number,body,start)
        need(all(1<=index<=count for index in indices), 'ec_symbol_member_reference')
        cursor = end; names = []
        for _ in range(number):
            nul = body.find(b'\0',cursor)
            need(nul>cursor, 'ec_symbol_string_bounds')
            names.append(body[cursor:nul]);cursor=nul+1
        need(body[cursor:] in (b'',b'\0') and names==sorted(set(names)), 'ec_symbol_string_table')
        return number
    number=struct.unpack_from('<I',second,end)[0]
    names_and_indices(second,end+4,number)
    need(len(ec[0])>=4, 'ec_symbol_index_bounds')
    ec_count=struct.unpack_from('<I',ec[0])[0]
    names_and_indices(ec[0],4,ec_count)
    return {'symbol_count':ec_count,'indexed_members':count}


def archive_machines(path):
    """Bounded COFF/import-member inventory, never an architecture name guess."""
    data=Path(path).read_bytes()
    need(len(data)<=128*1024**2 and data.startswith(b'!<arch>\n'),'invalid_static_archive')
    offset=8; result={}; count=0;entries=[]
    while offset<len(data):
        need(offset+60<=len(data) and data[offset+58:offset+60]==b'`\n','invalid_archive_header')
        header=data[offset:offset+60]
        try: size=int(header[48:58].strip())
        except ValueError: raise Error('invalid_archive_member_size') from None
        need(0<=size<=128*1024**2 and offset+60+size<=len(data),'invalid_archive_member_bounds')
        name=header[:16].decode('ascii').strip()
        blob=data[offset+60:offset+60+size]
        entries.append((offset,name,blob))
        if name.startswith('#1/'):
            length=int(name[3:]);need(0<=length<=len(blob),'invalid_bsd_archive_name');blob=blob[length:]
        if name not in ('/','//','/SYM64/','/<ECSYMBOLS>/'):
            need(len(blob)>=20,'truncated_coff_archive_member')
            machine=struct.unpack_from('<H',blob,6 if blob[:4]==b'\x00\x00\xff\xff' else 0)[0]
            need(machine in (0xaa64,0xa641,0x8664,0x14c),'unsupported_archive_object_format')
            result[str(machine)]=result.get(str(machine),0)+1;count+=1
        offset+=60+size+(size&1)
    need(offset==len(data) and count>0,'empty_or_invalid_static_archive')
    index=validate_ec_archive_index(entries)
    return {'sha256':sha256(path),'size_bytes':len(data),'coff_members':count,'machines':result,'ec_symbol_index':index}


def verify_cross(lock,tc,archive):
    spec=lock['cross_toolchain']
    need(Path(archive).stat().st_size==spec['size_bytes'] and sha256(archive)==spec['sha256'],'cross_archive_identity_mismatch')
    readers=wine_readers()
    expected=set()
    with tarfile.open(archive,'r:*') as packed:
        members,total=readers.archive_members(packed,spec['archive_root'],850000000)
        for member,rel in members:
            p=tc.joinpath(*relative(rel))
            if member.isdir():
                need(p.is_dir() and not p.is_symlink(),'cross_directory_changed');continue
            expected.add(rel)
            if member.issym():
                need(p.is_symlink() and os.readlink(p)==member.linkname,'cross_link_changed')
            else:
                with packed.extractfile(member) as stream:
                    digest=hashlib.file_digest(stream,'sha256').hexdigest()
                need(p.is_file() and not p.is_symlink() and sha256(p)==digest,'cross_payload_changed')
    observed=set()
    for directory,dirs,names in os.walk(tc,followlinks=False):
        for name in names+[n for n in dirs if (Path(directory)/n).is_symlink()]:
            observed.add((Path(directory)/name).relative_to(tc).as_posix())
    need(expected==observed,'cross_inventory_mismatch')
    selected={}
    for name in ('clang','lld-link','llvm-readobj','llvm-rc','llvm-dlltool','llvm-ar'):
        path=tc/'bin'/name
        closure=readers.inspect_closure(path,tc)
        need(all(row['selected_cpu']==readers.MACH_ARM64 for row in closure),'cross_tool_native_closure')
        selected[name]={'sha256':sha256(path.resolve()),'closure':closure}
    for name in ('aarch64-w64-mingw32-clang++','arm64ec-w64-mingw32-clang++'):
        p=tc/'bin'/name
        need(p.is_symlink() and p.resolve().is_relative_to(tc.resolve()) and p.resolve().read_bytes().startswith(b'#!/bin/sh'),'unqualified_cross_wrapper')
        selected[name]={'invocation':str(p),'resolved_sha256':sha256(p.resolve()),'execution':'arch-arm64-bin-sh'}
    return {'archive_sha256':spec['sha256'],'members':len(members),'regular_bytes':total,'tools':selected}


def verify_wine_roles(path):
    value=record(load_json(path),'fex_wine_roles')
    need(value.get('scope')=='fex_component','wrong_wine_role_scope')
    result=[]
    for name,variant in (('native','arm64'),('companion','arm64ec-build')):
        root=Path(value[name])
        need(sha256(root/'build.json')==BASE_BUILD_SHA[name],'wine_build_receipt_mismatch')
        build=record(load_json(root/'build.json'),'wine_build')
        need(build['passed'] is True and build['variant']==variant,'wrong_wine_build_role')
        need(build['source_manifest']['sha256']==BASE_SOURCE and build['patch_series_sha256']==BASE_SERIES,'wine_baseline_mismatch')
        need(sha256(root/build['source_manifest']['path'])==BASE_SOURCE,'wine_source_manifest_changed')
        manifest_path=root/build['artifacts_manifest']['path']
        need(sha256(manifest_path)==build['artifacts_manifest']['sha256']==BASE_ARTIFACT_SHA[name],'wine_artifact_manifest_changed')
        manifest=load_json(manifest_path)
        install=Path(build['install_root'])
        wanted=('bin/winebuild','lib/wine/aarch64-windows/libntdll.a','lib/wine/aarch64-windows/libwinecrt0.a','lib/wine/aarch64-windows/libdbghelp.a')
        selected=[]
        for rel in wanted:
            rows=[r for r in manifest['files'] if r['path']==rel]
            need(len(rows)==1,'missing_wine_role_artifact')
            row=rows[0];p=install.joinpath(*relative(rel))
            need(p.stat().st_size==row['size_bytes'] and sha256(p)==row['sha256'],'wine_role_artifact_changed')
            item={'role':rel,'sha256':row['sha256'],'size_bytes':row['size_bytes']}
            if p.suffix=='.a': item['archive']=archive_machines(p)
            else: item['macho']=wine_readers().inspect_macho(p)
            selected.append(item)
        result.append({'role':name,'variant':variant,'build_sha256':sha256(root/'build.json'),'artifacts_manifest_sha256':sha256(manifest_path),'selected':selected})
    return value,result


def pe_facts(path):
    data=Path(path).read_bytes()
    need(len(data)<=64*1024**2 and len(data)>=64 and data[:2]==b'MZ','invalid_capability_pe')
    pe=struct.unpack_from('<I',data,60)[0]
    need(64<=pe and pe+24<=len(data) and data[pe:pe+4]==b'PE\0\0','invalid_capability_pe')
    machine,count=struct.unpack_from('<HH',data,pe+4);opt=pe+24;size=struct.unpack_from('<H',data,pe+20)[0]
    need(1<=count<=96 and opt+size+40*count<=len(data) and size>=240 and struct.unpack_from('<H',data,opt)[0]==0x20b,'invalid_capability_pe_sections')
    sections=[]
    for i in range(count):
        at=opt+size+40*i;virtual,rva,raw_size,raw=struct.unpack_from('<IIII',data,at+8)
        need(raw+raw_size<=len(data),'capability_pe_section_bounds')
        sections.append((rva,min(virtual,raw_size),raw))
    config_rva,config_size=struct.unpack_from('<II',data,opt+112+10*8)
    pointer=0
    if config_rva:
        matches=[raw+config_rva-rva for rva,span,raw in sections if config_rva>=rva and config_rva-rva+config_size<=span]
        need(len(matches)==1 and config_size>=208,'invalid_capability_load_config')
        pointer=struct.unpack_from('<Q',data,matches[0]+200)[0]
        if pointer:
            base=struct.unpack_from('<Q',data,opt+24)[0];rva=pointer-base
            need(any(address<=rva<address+span for address,span,_ in sections),'unmapped_capability_chpe')
    return {'outer_machine':machine,'chpe_metadata_pointer':pointer,'entrypoint':struct.unpack_from('<I',data,opt+16)[0]}


# Bounded mapping/range checks reused from tools/wine/build.py;
# the default MinGW DLL CRT uses pinned mingw-w64-crt/crt/chpe.S Version 1.
# This is a capability-fixture predicate, not a universal FEX DLL predicate.
def inspect_fixture_arm64ec(path):
    """Require positive ARM64EC metadata; its AMD64 header is not native x64 proof.

    This selected default-CRT DLL link form includes ARM64EC and x64 guest thunk ranges. Neither
    those ranges nor the companion build establish guest execution support.
    """
    need(Path(path).stat().st_size <= 64 * 1024 * 1024, 'arm64ec_size_limit')
    data = Path(path).read_bytes()
    def number(fmt, at):
        size = struct.calcsize('<' + fmt)
        need(0 <= at and at + size <= len(data), 'arm64ec_structure_bounds')
        return struct.unpack_from('<' + fmt, data, at)[0]
    need(data[:2] == b'MZ', 'arm64ec_pe_header')
    pe = number('I', 60)
    count, size, opt = number('H', pe + 6), number('H', pe + 20), pe + 24
    need(pe >= 64 and data[pe:pe + 4] == b'PE\0\0' and number('H', pe + 4) == 0x8664
         and 1 <= count <= 96 and size >= 240 and number('H', opt) == 0x20B
         and number('I', opt + 108) == 16, 'arm64ec_pe_header')
    base = number('Q', opt + 24)
    image_size = number('I', opt + 56)
    need(0 < image_size <= 1024 * 1024 * 1024, 'arm64ec_image_size')
    sections = []
    for i in range(count):
        at = opt + size + 40 * i
        virtual, rva, raw_size, raw, flags = (number('I', at + n) for n in (8, 12, 16, 20, 36))
        need(raw + raw_size <= len(data) and rva + max(virtual, raw_size) <= image_size, 'arm64ec_section_bounds')
        sections.append((rva, min(virtual, raw_size), raw, flags, max(virtual, raw_size)))
    def mapped(rva, length, executable=False):
        matches = [(raw + rva - address, flags) for address, span, raw, flags, _ in sections
                   if rva >= address and length > 0 and rva - address + length <= span]
        need(len(matches) == 1 and (not executable or matches[0][1] & 0x20000000), 'arm64ec_unmapped_rva')
        return matches[0][0]
    alignment = number('I', opt + 32)
    need(4096 <= alignment <= 65536 and alignment & (alignment - 1) == 0
         and all(rva % alignment == 0 for rva, _, _, _, _ in sections), 'arm64ec_section_alignment')
    executable_intervals = sorted((rva, rva + ((span + alignment - 1) & ~(alignment - 1)))
                                  for rva, _, _, flags, span in sections if flags & 0x20000000 and span)
    need(all(end <= image_size for _, end in executable_intervals), 'arm64ec_executable_extent')
    need(all(previous[1] <= current[0] for previous, current in
             zip(executable_intervals, executable_intervals[1:])), 'arm64ec_ambiguous_code_sections')
    def executable_range(rva, length):
        need(length > 0 and rva + length <= image_size, 'arm64ec_code_range')
        cursor, end = rva, rva + length
        # LLVM's x64 thunk range can include executable section alignment padding
        # and cross into the immediately adjacent .hexpthk section. Preserve
        # the header's bounded executable page extent, not just raw bytes.
        # This byte inspection does not authorize a host executable mapping.
        for low, high in executable_intervals:
            if low <= cursor < high:
                cursor = min(high, end)
            if cursor == end:
                return
            if low > cursor:
                break
        raise Error('arm64ec_unmapped_code_range')
    config_rva = number('I', opt + 112 + 10 * 8)
    config_size = number('I', opt + 116 + 10 * 8)
    config = mapped(config_rva, config_size)
    need(config_size >= 0xE8 and 0xE8 <= number('I', config) <= config_size, 'arm64ec_load_config')
    pointer = number('Q', config + 0xC8)
    need(pointer > base and number('I', config + 0xE0) == 0 and number('H', config + 0xE4) == 0,
         'arm64ec_load_config')
    metadata = mapped(pointer - base, 80)
    version, codemap, count = (number('I', metadata + n) for n in (0, 4, 8))
    need(version == 1 and 2 <= count <= 4096, 'arm64ec_chpe_header')
    codemap_at = mapped(codemap, count * 8)
    ranges, previous_end = [], 0
    for i in range(count):
        tagged, length = number('I', codemap_at + i * 8), number('I', codemap_at + i * 8 + 4)
        kind, rva = tagged & 3, tagged & ~3
        need(kind in (1, 2) and rva >= previous_end, 'arm64ec_code_range')
        executable_range(rva, length)
        ranges.append({'rva': rva, 'size_bytes': length, 'code_kind': 'arm64ec' if kind == 1 else 'x64'})
        previous_end = rva + length
    need({row['code_kind'] for row in ranges} == {'arm64ec', 'x64'}, 'arm64ec_code_range')
    return {'pe_abi': 'arm64ec', 'chpe_version': version, 'code_ranges': ranges}

def validate_config(value, inputs_sha256):
    record(value, 'fex_build_config')
    need(value.get('scope') == 'fex_component' and value.get('host_architecture') == 'arm64', 'wrong_config_scope')
    need(value['inputs_ref'] == {'path':'runtime/fex/inputs.json', 'sha256':inputs_sha256}, 'config_source_binding_mismatch')
    need(value['runtime_options'] == {'DiskCache':False, 'ProfileStats':False, 'TSOEnabled':True}
         and value['unsupported_override_policy'] == 'reject', 'unsupported_runtime_policy')
    need(value['compile_flags'] == ['-std=c++20','-fno-exceptions','-fno-strict-aliasing']
         and value['link_flags'] == ['-static','-nostdlib','-nostartfiles','-nodefaultlibs'], 'unsupported_build_contract')
    need(value['deployment_target'] == '26.5' and value['qualification'] ==
         {'distribution':'unperformed','game':'unperformed','runtime':'unperformed'}, 'unsupported_build_contract')
    need(value['source_configuration_status'] == 'source_inspected_not_configured'
         and value['native_root_cmake_status'] == 'unsupported_pending_darwin_port', 'source_configuration_overclaim')
    need(value['cmake_options']['ENABLE_LTO'] is False and value['cmake_options']['ENABLE_CCACHE'] is False,
         'unsupported_build_contract')
    return value


def command_recipe(root, prepared, tc, lock):
    """Closed compile-only recipe shared by producer and independent receipt replay."""
    root, prepared, tc = Path(root), Path(prepared), Path(tc)
    fex = prepared/'sources/fex'
    fixtures = REPO/'tests/fex/capabilities'
    arch = ['/usr/bin/arch','-arm64']
    commands = {'cross.version': [*arch,tc/'bin/clang','--version'],
        'native.layout': [*arch,Path(lock['native_tools']['clang++']['path']),'-arch','arm64','-isysroot',
            lock['sdk']['path'],'-std=c++20','-I'+str(fex/'Source/Windows/UnixLib'),'-c',
            fixtures/'layout.cpp','-o',root/'native-layout.obj'],
        'builtins.path': [*arch,'/bin/sh',tc/'bin/arm64ec-w64-mingw32-clang++','-print-libgcc-file-name']}
    for target in MACHINES:
        out = root/target
        prefix = [*arch,'/bin/sh',tc/'bin'/f'{target}-w64-mingw32-clang++']
        cflags = ['-std=c++20','-fno-exceptions','-fno-strict-aliasing','-fno-stack-protector']
        for name in ('language','layout','declarations'):
            commands[target+'.'+name] = [*prefix,*cflags,'-I'+str(fex/'Source/Windows/UnixLib'),'-c',
                fixtures/(name+'.cpp'),'-o',out/(name+'.obj')]
        commands[target+'.runtime-object'] = [*prefix,*cflags,'-c',fixtures/'static-runtime.cpp','-o',out/'static-runtime.obj']
        commands[target+'.source-imports'] = [*arch,tc/'bin/llvm-dlltool','-m',
            'arm64ec' if target=='arm64ec' else 'arm64','-d',fex/'Source/Windows/Defs/ntdll.def','-l',out/'ntdll-ex.a']
        # Standalone prerequisites use the compiler's complete default DLL CRT. The actual
        # FEX -nostdlib/-nodefaultlibs/custom-CRT link remains a Stage 2 task.
        commands[target+'.static-link'] = [*prefix,*cflags,'-shared','-static',
            '-Wl,-Xlink=/map:'+str(out/'link.map'),out/'static-runtime.obj',out/'ntdll-ex.a',
            '-lc++abi','-lc++','-lunwind','-o',out/'pear-fex-capability.dll']
        commands[target+'.pe-inspect'] = [*arch,tc/'bin/llvm-readobj','--coff-imports','--coff-exports',
            '--coff-load-config',out/'pear-fex-capability.dll']
    return {key:[str(item) for item in argv] for key,argv in commands.items()}


def environment_contract(tc, lock, config):
    return {'PATH':str(tc/'bin')+':/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL':'C',
            'SDKROOT':lock['sdk']['path'], 'MACOSX_DEPLOYMENT_TARGET':config['deployment_target']}


def link_contributions(path):
    text = Path(path).read_text()
    need(len(text.encode()) <= 4*1024**2, 'link_map_limit')
    # Pinned MinGW -Xlink forwards /map to COFF's Lib:Object symbol map.
    # lld's ordinary -Map lists member basenames without archive provenance,
    # so it is insufficient for this library-contribution predicate.
    required = {'libc++.a':('_ZNSt3__16chrono12steady_clock3nowEv','libc++'),
                'libc++abi.a':('__cxa_guard_acquire','libc++abi'),
                'libunwind.a':('_Unwind_GetIP','libunwind'),
                'compiler-builtins':('__udivti3',None)}
    selected = {key:set() for key in required}
    for line in text.splitlines():
        match = re.fullmatch(r' +[0-9a-fA-F]{4}:[0-9a-fA-F]{8,16} +([^ ]+) +[0-9a-fA-F]{16} +([^ :]+):([^ ]+)',line)
        if not match:
            continue
        symbol,archive,member = match.groups()
        for library,(expected,owner) in required.items():
            named_archive = archive==owner if owner is not None else bool(
                re.fullmatch(r'libclang_rt\.builtins-[^/()]+',archive))
            if symbol.removeprefix('#')==expected and named_archive:
                selected[library].add(member)
    observations = {}
    for library,(symbol,_) in required.items():
        need(selected[library], 'static_library_not_linked:'+library)
        observations[library] = {'required_symbol':symbol, 'selected_members':len(selected[library])}
    return observations


def run(argv,root,ident,data,env,timeout=120):
    logs=root/'logs'/ident;logs.mkdir(parents=True)
    value=bounded_command([str(x) for x in argv],cwd=root,env=env,timeout=timeout,max_output=512*1024,output_dir=logs)
    item={'id':ident,'argv':value['argv'],'exit_code':value['returncode'],'elapsed_ms':value['elapsed_ms'],'environment':{k:env[k] for k in ('PATH','LC_ALL','SDKROOT','MACOSX_DEPLOYMENT_TARGET')},'logs':{}}
    for name in ('stdout','stderr'):
        p=logs/(name+'.bin');item['logs'][name]={'path':p.relative_to(root).as_posix(),'sha256':sha256(p),'size_bytes':p.stat().st_size}
    data['commands'].append(item)
    need(value['returncode']==0,'capability_command_failed:'+ident)
    return value


def capabilities(args):
    root=operation_output(args.output)
    data={'schema_version':1,'record_kind':'fex_stage1_capabilities','scope':'fex_component','commands':[],'checks':[],'artifacts':[],'passed':False,**dict.fromkeys(FALSE_FLAGS,False)}
    try:
        inputs=Path(args.inputs).resolve();config=Path(args.config).resolve();prepared=Path(args.prepared).resolve();tools=Path(args.tools).resolve();tc=Path(args.cross_tools).resolve();role_path=Path(args.wine_roles).resolve()
        lock_path=REPO/'runtime/fex/toolchain.json';lock=record(load_json(lock_path),'fex_toolchain')
        source=verify_prepared(prepared,expected_inputs_sha256=sha256(inputs))
        config_data=validate_config(load_json(config),sha256(inputs))
        need(not any(k.startswith('FEX_') for k in os.environ),'unsupported_fex_environment_override')
        tool_data=verify_tools(tools,lock_path)
        roles,role_evidence=verify_wine_roles(role_path)
        data['bindings']={'inputs':{'path':str(inputs),'sha256':sha256(inputs)},'config':{'path':str(config),'sha256':sha256(config)},'prepared':{'path':str(prepared),'sha256':sha256(prepared/'prepared.json')},'tools':{'path':str(tools),'sha256':sha256(tools/'prepared.json')},'toolchain':{'path':str(lock_path),'sha256':sha256(lock_path)},'wine_roles':{'path':str(role_path),'sha256':sha256(role_path)},'cross_tools':{'path':str(tc),'archive':roles['cross_archive']}}
        data['producer_sha256']={str(p.relative_to(REPO)):sha256(p) for p in sorted((REPO/'tools/fex').glob('*.py'))}
        fixture_root=REPO/'tests/fex/capabilities'
        data['fixtures']={p.name:sha256(p) for p in sorted(fixture_root.iterdir()) if p.is_file()}
        data['cross_toolchain']=verify_cross(lock,tc,Path(roles['cross_archive']))
        data['wine_roles']=role_evidence
        data['checks'].append({'id':'input-and-tool-closure','status':'passed','required':True})
        fex=prepared/'sources/fex'
        env={}
        env.update(environment_contract(tc,lock,config_data))
        recipe=command_recipe(root,prepared,tc,lock)
        data['link_probe_scope']='standalone_default_crt_static_prerequisites'
        data['fex_custom_crt_link']='unperformed'
        data['link_contributions']={}
        version=run(recipe['cross.version'],root,'cross.version',data,env)
        need(b'clang version 23.1.1' in version['stdout'],'cross_compiler_version_mismatch')
        native=Path(lock['native_tools']['clang++']['path'])
        need(sha256(native.resolve())==lock['native_tools']['clang++']['sha256'],'native_compiler_changed')
        readobj=tc/'bin/llvm-readobj';dlltool=tc/'bin/llvm-dlltool'
        native_obj=root/'native-layout.obj'
        run(recipe['native.layout'],root,'native.layout',data,env)
        need(wine_readers().inspect_macho(native_obj)['architectures']==[0x100000c],'native_layout_target_mismatch')
        data['artifacts'].append({'path':native_obj.name,'sha256':sha256(native_obj),'size_bytes':native_obj.stat().st_size,'kind':'native_layout_object'})
        for target,machine in MACHINES.items():
            out=root/target;out.mkdir()
            wrapper=tc/'bin'/f'{target}-w64-mingw32-clang++'
            prefix=['/usr/bin/arch','-arm64','/bin/sh',wrapper]
            cflags=['-std=c++20','-fno-exceptions','-fno-strict-aliasing','-fno-stack-protector']
            for name in ('language','layout','declarations'):
                obj=out/(name+'.obj')
                run(recipe[target+'.'+name],root,target+'.'+name,data,env)
                need(wine_readers().coff_machine(obj)==machine,'capability_coff_target_mismatch')
                data['artifacts'].append({'path':obj.relative_to(root).as_posix(),'sha256':sha256(obj),'size_bytes':obj.stat().st_size,'kind':'coff_object','machine':machine})
            runtime=out/'static-runtime.obj'
            run(recipe[target+'.runtime-object'],root,target+'.runtime-object',data,env)
            implib=out/'ntdll-ex.a'
            run(recipe[target+'.source-imports'],root,target+'.source-imports',data,env)
            dll=out/'pear-fex-capability.dll'
            run(recipe[target+'.static-link'],root,target+'.static-link',data,env)
            data['link_contributions'][target]=link_contributions(out/'link.map')
            data['artifacts'].append({'path':(out/'link.map').relative_to(root).as_posix(),'sha256':sha256(out/'link.map'),'size_bytes':(out/'link.map').stat().st_size,'kind':'link_map'})
            facts=pe_facts(dll)
            need(facts['outer_machine']==(0x8664 if target=='arm64ec' else 0xaa64),'capability_pe_target_mismatch')
            if target=='arm64ec':
                need(facts['chpe_metadata_pointer']>0,'missing_capability_arm64ec_metadata')
                facts['arm64ec_metadata']=inspect_fixture_arm64ec(dll)
            imports=run(recipe[target+'.pe-inspect'],root,target+'.pe-inspect',data,env)
            text=imports['stdout'].decode(errors='replace')
            need('pear_fex_static_runtime' in text and 'NtYieldExecution' in text and 'ntdll.dll' in text,'missing_capability_import_export')
            need(not any(name in text.lower() for name in ('libc++.dll','libc++abi.dll','libunwind.dll')),'dynamic_cpp_runtime_dependency')
            for p,kind in ((runtime,'static_runtime_object'),(implib,'source_import_archive'),(dll,'capability_dll')):
                data['artifacts'].append({'path':p.relative_to(root).as_posix(),'sha256':sha256(p),'size_bytes':p.stat().st_size,'kind':kind,**(facts if p==dll else {})})
            data['checks'].append({'id':target+'-cxx20-layout-static-link','status':'passed','required':True,'pe_facts':facts,'pe_execution':False})
        libraries={}
        for name in ('libc++.a','libc++abi.a','libunwind.a'):
            path=tc/'aarch64-w64-mingw32/lib'/name
            libraries[name]=archive_machines(path)
        builtins=run(recipe['builtins.path'],root,'builtins.path',data,env)
        builtin=Path(builtins['stdout'].decode().strip())
        need(builtin.resolve().is_relative_to(tc),'builtins_outside_cross_toolchain')
        libraries['builtins']=archive_machines(builtin)
        data['static_libraries']=libraries
        data['checks'].append({'id':'static-runtime-member-inventory','required':True,'status':'passed'})
        data['passed']=True
    except (Error,OSError,ValueError,KeyError,TypeError) as exc:
        data['error']=getattr(exc,'code',type(exc).__name__)
        data['checks'].append({'id':'required-capability-failure','status':'failed','required':True,'reason':data['error']})
    write_json(root/'capabilities.json',data)
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('capabilities',))
    for name in ('inputs','config','prepared','tools','cross-tools','wine-roles','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--require-empty',action='store_true',required=True)
    args=parser.parse_args()
    try:
        result=capabilities(args)
        print(('PASS' if result['passed'] else 'FAIL')+': '+('compile-only source/tool/static-runtime contract' if result['passed'] else result['error']))
        return 0 if result['passed'] else 3
    except (Error,OSError,ValueError,KeyError) as exc:
        print('FAIL: '+getattr(exc,'code',type(exc).__name__),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
