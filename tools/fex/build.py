#!/usr/bin/env python3
"""Construct source-bound FEX components; no PE, engine or JIT execution."""
from __future__ import annotations
import argparse
import hashlib
import os
import struct
from pathlib import Path
import re
import shlex
import shutil
import sys
import time
if __package__:
    from .common import Error, REPO, bounded_command, decode_json, load_json, need, operation_output, read_relative, record, relative, sha256, write_json
    from .prepare import verify_prepared
    from .tools import verify_tools, files, wine_readers
    from .check import validate_config, verify_cross, verify_wine_roles, archive_machines, inspect_fixture_arm64ec
else:
    from common import Error, REPO, bounded_command, decode_json, load_json, need, operation_output, read_relative, record, relative, sha256, write_json
    from prepare import verify_prepared
    from tools import verify_tools, files, wine_readers
    from check import validate_config, verify_cross, verify_wine_roles, archive_machines, inspect_fixture_arm64ec

PATCH_ROOT=REPO/'runtime/fex/patches'
FIXTURE=REPO/'tests/fex/services/native_services.cpp'
PRODUCERS=('tools/fex/build.py','tools/fex/common.py','tools/fex/prepare.py','tools/fex/tools.py','tools/fex/check.py','tools/fex/byte_readers.py','tools/wine/common.py','tools/sources/validate_inventory.py')
FALSE_FLAGS=('fex_initialization','jit_execution','pe_execution','guest_execution','runtime_qualified','distribution_qualified')
NATIVE_ARTIFACTS={'install/libarm64ecfex.so':'arm64ec_native_unixlib','install/libwow64fex.so':'wow64_native_unixlib','fixtures/pear-fex-services':'native_service_fixture'}
BASE_COMMIT='59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa'
BASE_TREE='7509ab443d32692ac72ee51c0697ccf86d0a66af'
WINE_BASE='39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086'


def exact(value, fields, code):
    need(isinstance(value,dict) and set(value)==set(fields),code)


def host_metadata(path):
    data=record(load_json(path),'fex_stage2_host_metadata')
    exact(data,('schema_version','record_kind','scope','commands','fex_initialization','guest_execution'),'host_metadata_fields')
    need(data['scope']=='fex_component' and data['fex_initialization'] is False and data['guest_execution'] is False,'host_metadata_scope')
    specs={'cache-line':['/usr/bin/arch','-arm64','/usr/sbin/sysctl','-n','hw.cachelinesize'],
           'memory':['/usr/bin/arch','-arm64','/usr/sbin/sysctl','-n','hw.memsize'],
           'os-build':['/usr/bin/arch','-arm64','/usr/bin/sw_vers','-buildVersion']}
    need(isinstance(data['commands'],list) and all(isinstance(r,dict) for r in data['commands']), 'host_metadata_commands')
    need(len(data['commands'])==len(specs) and {r['id'] for r in data['commands']}==set(specs),'host_metadata_command_closure')
    stdout={}
    for row in data['commands']:
        exact(row,('id','argv','returncode','elapsed_ms','status','logs'),'host_metadata_command_fields')
        ident=row['id']
        need(type(row['returncode']) is int and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0,'host_metadata_command_types')
        need(row['argv']==specs[ident] and row['returncode']==0 and row['status']=='completed','host_metadata_failed')
        need(set(row['logs'])=={'stdout','stderr'},'host_metadata_log_closure')
        for stream,ref in row['logs'].items():
            exact(ref,('path','sha256','size_bytes'),'host_metadata_log_fields')
            need(ref['path']==ident+'/'+stream+'.bin' and type(ref['size_bytes']) is int and 0<=ref['size_bytes']<=65536,'host_metadata_log_path')
            raw=read_relative(Path(path).parent,ref['path'],65536)
            need(len(raw)==ref['size_bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'host_metadata_log_changed')
            if stream=='stdout':stdout[ident]=raw.decode().strip()
    try:cache=int(stdout['cache-line']);memory=int(stdout['memory'])
    except ValueError:raise Error('host_metadata_integer') from None
    need(re.fullmatch(r'[A-Za-z0-9]{4,32}',stdout['os-build']) is not None,'host_os_build')
    need(16<=cache<=1024 and cache & (cache-1)==0 and memory>0,'host_cache_geometry')
    return {'cache_line_bytes':cache,'dcache_line_log2':cache.bit_length()-3,'memory_bytes':memory,'os_build':stdout['os-build'],
            'optional_isa_features':'disabled_conservative_policy','id_registers':'unavailable','midr':'unavailable',
            'processor_count_provider':'PE_GetSystemInfo_unperformed','hardware_tso':'unsupported','software_tso_required':True}


def patch_set():
    series=record(load_json(PATCH_ROOT/'series.json'),'fex_patch_series')
    exact(series,('schema_version','record_kind','scope','base_commit','base_tree','wine_baseline_series_sha256','patches','component_built','fex_initialization','guest_execution','runtime_qualified'),'patch_series_fields')
    need(series['scope']=='fex_component' and series['base_commit']==BASE_COMMIT and series['base_tree']==BASE_TREE
         and series['wine_baseline_series_sha256']==WINE_BASE,'patch_base_mismatch')
    need(all(series[key] is False for key in ('component_built','fex_initialization','guest_execution','runtime_qualified')),'patch_runtime_overclaim')
    expected=('0002a-darwin-unixlib-services.patch','0002b-darwin-conservative-features.patch','0002c-explicit-static-abi-link.patch','0002d-enforced-darwin-config-policy.patch','0002e-source-bound-generator-interpreter.patch')
    need(tuple(row['path'] for row in series['patches'])==expected,'patch_order_mismatch')
    for row in series['patches']:
        exact(row,('path','sha256','rationale','license','provenance','changes'),'patch_row_fields')
        need(isinstance(row['changes'],list) and row['changes'] and len(row['changes'])<=64,'patch_change_count')
        for change in row['changes']:
            exact(change,('path','before_sha256','after_sha256'),'patch_change_fields');relative(change['path'])
            need(change['before_sha256'] is None or isinstance(change['before_sha256'],str) and re.fullmatch(r'[0-9a-f]{64}',change['before_sha256']), 'patch_preimage_digest')
            need(isinstance(change['after_sha256'],str) and re.fullmatch(r'[0-9a-f]{64}',change['after_sha256']), 'patch_postimage_digest')
        need(sha256(PATCH_ROOT.joinpath(*relative(row['path'])))==row['sha256'],'patch_bytes_changed')
        need(row['license'].startswith('MIT') and row['provenance'] and row['changes'],'patch_attribution_missing')
    return series


def patch_sections(raw):
    need(isinstance(raw,bytes) and len(raw)<=2*1024**2,'patch_size_limit')
    text=raw.decode().splitlines(True)
    sections={};current=None
    for line in text:
        if line.startswith('diff --git '):
            match=re.fullmatch(r'diff --git a/(\S+) b/(\S+)\n',line)
            need(match and match[1]==match[2],'patch_header')
            relative(match[1]);current=match[1]
            need(current not in sections,'patch_duplicate_path');sections[current]=[]
        else:
            need(current is not None,'patch_header');sections[current].append(line)
    return sections


def apply_hunks(before,lines,path):
    need(lines[:2]==['--- '+('a/'+path if before is not None else '/dev/null')+'\n','+++ b/'+path+'\n'],'patch_file_header')
    original=(before or b'').decode().splitlines(True)
    output=[];cursor=0;i=2
    while i<len(lines):
        match=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',lines[i])
        need(match,'patch_hunk_header')
        start,old_count=int(match[1]),int(match[2] or 1)
        new_start,new_count=int(match[3]),int(match[4] or 1)
        offset=start-1 if start else 0
        need(cursor<=offset<=len(original),'patch_hunk_order')
        output.extend(original[cursor:offset]);cursor=offset;i+=1
        need(len(output)==(new_start-1 if new_start else 0),'patch_new_hunk_offset')
        removed=added=0
        while i<len(lines) and not lines[i].startswith('@@ '):
            line=lines[i];need(line and line[0] in ' +-','patch_hunk_line')
            if line[0] in ' -':
                need(cursor<len(original) and original[cursor]==line[1:],'patch_context_mismatch')
                cursor+=1;removed+=1
            if line[0] in ' +':output.append(line[1:]);added+=1
            i+=1
        need(removed==old_count and added==new_count,'patch_hunk_counts')
    output.extend(original[cursor:])
    return ''.join(output).encode()


def derive_source(prepared,series):
    source=Path(prepared)/'sources/fex'
    manifest=load_json(Path(prepared)/'source-manifest.json')
    rows={row['path']:{'path':row['path'],'sha256':row['sha256'],'size_bytes':row['size_bytes'],
                       'mode':0o755 if row['mode']=='100755' else 0o644} for row in manifest['files']}
    changes={}
    for patch in series['patches']:
        sections=patch_sections(read_relative(PATCH_ROOT,patch['path'],2*1024**2))
        need(set(sections)=={row['path'] for row in patch['changes']},'patch_change_closure')
        for row in patch['changes']:
            path=row['path'];relative(path)
            before=changes.get(path)
            if before is None and path in rows:before=read_relative(source,path,4*1024**2)
            need((hashlib.sha256(before).hexdigest() if before is not None else None)==row['before_sha256'],'patch_preimage_mismatch')
            after=apply_hunks(before,sections[path],path)
            need(hashlib.sha256(after).hexdigest()==row['after_sha256'],'patch_postimage_mismatch')
            changes[path]=after
            rows[path]={'path':path,'sha256':row['after_sha256'],'size_bytes':len(after),'mode':rows.get(path,{}).get('mode',0o644)}
    return sorted(rows.values(),key=lambda r:r['path']),changes


def source_files(root):
    rows=files(root)
    need(all('symlink' not in row for row in rows),'materialized_source_link')
    return rows


def environment(lock):
    return {'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LC_ALL':'C','SDKROOT':lock['sdk']['path'],
            'MACOSX_DEPLOYMENT_TARGET':lock['sdk']['version']}


def native_recipe(root,tools,lock,features):
    cmake=Path(tools)/'cmake/CMake.app/Contents/bin/cmake';ninja=Path(tools)/'ninja-source/ninja'
    source=Path(root)/'source';native=Path(root)/'native'
    arch=['/usr/bin/arch','-arm64']
    return {
      'native.configure':[ *arch,str(cmake),'-S',str(source/'Source/Windows/UnixLib'),'-B',str(native),'-G','Ninja',
           '-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_CXX_COMPILER='+lock['native_tools']['clang++']['path'],
           '-DCMAKE_OSX_ARCHITECTURES=arm64','-DCMAKE_OSX_SYSROOT='+lock['sdk']['path'],
           '-DCMAKE_OSX_DEPLOYMENT_TARGET='+lock['sdk']['version'],'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
           '-DCMAKE_CXX_FLAGS=-fno-exceptions -fno-strict-aliasing'],
      'native.build':[ *arch,str(cmake),'--build',str(native),'--target','arm64ecfex_unixlib','wow64fex_unixlib','--parallel','1'],
      'native.fixture':[ *arch,lock['native_tools']['clang++']['path'],'-arch','arm64','-isysroot',lock['sdk']['path'],
           '-mmacosx-version-min='+lock['sdk']['version'],'-std=c++20','-fno-exceptions','-fno-strict-aliasing',
           '-DPEAR_FEX_DARWIN_DCACHE_LINE_BYTES='+str(features['cache_line_bytes']),'-I'+str(source/'Source/Windows/UnixLib'),'-I'+str(source/'Source/Windows/Common'),
           str(FIXTURE),'-o',str(Path(root)/'fixtures/pear-fex-services')],
    }


def run_command(root,ident,argv,env,commands,timeout=600):
    directory=Path(root)/'logs'/ident;directory.mkdir(parents=True)
    started=time.monotonic()
    row={'id':ident,'argv':argv,'cwd':str(root),'environment':env,'exit_code':None,'elapsed_ms':0,'status':'unperformed','logs':{}}
    try:
        result=bounded_command(argv,cwd=root,output_dir=directory,timeout=timeout,max_output=4*1024**2,env=env)
        row.update(exit_code=result['returncode'],elapsed_ms=result['elapsed_ms'],status=result['status'])
    except (Error,OSError) as error:
        row.update(elapsed_ms=int((time.monotonic()-started)*1000),status='failed',error=getattr(error,'code',type(error).__name__))
        raise
    finally:
        for stream in ('stdout','stderr'):
            path=directory/(stream+'.bin')
            if path.exists():row['logs'][stream]={'path':path.relative_to(root).as_posix(),'size_bytes':path.stat().st_size,'sha256':sha256(path)}
        commands.append(row)
    need(result['returncode']==0,'build_command_failed:'+ident)
    return result


def inspect_native(root):
    artifacts=[];reader=wine_readers()
    for path,role in NATIVE_ARTIFACTS.items():
        actual=Path(root)/path
        info=reader.inspect_macho(actual)
        need(info['architectures']==[reader.MACH_ARM64] and info['filetype']==(2 if role=='native_service_fixture' else 6),'native_artifact_format')
        closure=reader.inspect_closure(actual,Path(root)/('fixtures' if role=='native_service_fixture' else 'install'))
        need(all(row['selected_cpu']==reader.MACH_ARM64 for row in closure),'native_dependency_architecture')
        artifacts.append({'path':path,'role':role,'sha256':sha256(actual),'size_bytes':actual.stat().st_size,'macho':info,'native_closure':closure})
    return artifacts


def cross_inputs(tc,roles_path,lock,tool_receipt):
    roles,evidence=verify_wine_roles(roles_path)
    archive=Path(roles['cross_archive'])
    observed=verify_cross(lock,tc,archive)
    python=tool_receipt['native_build']['python']
    tools={}
    for name,path in {'python':python['path'],'gzip':'/usr/bin/gzip','dd':'/bin/dd','sh':'/bin/sh','arch':'/usr/bin/arch'}.items():
        actual=Path(path).resolve(strict=True)
        info=wine_readers().inspect_macho(actual)
        need(info['selected_cpu']==wine_readers().MACH_ARM64 and info['filetype']==2,'full_build_tool_not_native')
        tools[name]={'path':path,'sha256':sha256(actual),'macho':info}
    need(tools['python']['sha256']==python['sha256'],'full_generator_interpreter_changed')
    for name in ('libc++.a','libc++abi.a','libunwind.a'):
        path=tc/'aarch64-w64-mingw32/lib'/name
        tools[name]={'path':str(path),'sha256':sha256(path),'archive':archive_machines(path)}
    return {'cross_tools':str(tc),'archive':str(archive),'wine_roles':{'path':str(roles_path),'sha256':sha256(roles_path)},
            'wine_role_evidence':evidence,'cross_observation':observed,'build_auxiliary_tools':tools}


def complete_environment(lock,cross):
    result=environment(lock);result['PATH']=str(Path(cross['cross_tools'])/'bin')+':'+result['PATH'];return result


def complete_recipe(root,tools,lock,features,config,cross):
    commands=native_recipe(root,tools,lock,features)
    cmake=Path(tools)/'cmake/CMake.app/Contents/bin/cmake';ninja=Path(tools)/'ninja-source/ninja'
    source=Path(root)/'source';tc=Path(cross['cross_tools']);arch=['/usr/bin/arch','-arm64']
    for target,triple,module in (('arm64ec','arm64ec-w64-mingw32','arm64ecfex'),('wow64','aarch64-w64-mingw32','wow64fex')):
        out=Path(root)/'pe'/target
        flags='-std=c++20 -fno-exceptions -fno-strict-aliasing -fno-stack-protector -DPEAR_FEX_DARWIN=1 -DPEAR_FEX_DARWIN_DCACHE_LOG2='+str(features['dcache_line_log2'])
        commands[target+'.configure']=[*arch,str(cmake),'-S',str(source),'-B',str(out),'-G','Ninja',
            '-DCMAKE_MAKE_PROGRAM='+str(ninja),'-DCMAKE_TOOLCHAIN_FILE='+str(source/'Data/CMake/toolchain_mingw.cmake'),
            '-DMINGW_TRIPLE='+triple,'-DCMAKE_ASM_COMPILER='+str(tc/'bin'/(triple+'-clang')),
            '-DCMAKE_CXX_FLAGS='+flags,'-DCMAKE_C_FLAGS=-DPEAR_FEX_DARWIN=1',
            '-DCMAKE_SHARED_LINKER_FLAGS=-static -Wl,--file-alignment=4096,/mllvm:-align-loops=1 -Wl,-Xlink=/map:link.map',
            '-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY',
            '-DPython_EXECUTABLE='+cross['build_auxiliary_tools']['python']['path'],
            '-DCMAKE_DISABLE_FIND_PACKAGE_unordered_dense=TRUE','-DCMAKE_DISABLE_FIND_PACKAGE_range-v3=TRUE',
            '-DOVERRIDE_VERSION=Pear-pinned-FEX','-DOVERRIDE_HASH='+BASE_COMMIT,
            *['-D'+key+'='+('ON' if value is True else 'OFF' if value is False else str(value)) for key,value in sorted(config['cmake_options'].items())]]
        commands[target+'.build']=[*arch,str(cmake),'--build',str(out),'--target',module,'--parallel','1','--verbose']
        commands[target+'.inspect']=[*arch,str(tc/'bin/llvm-readobj'),'--coff-imports','--coff-exports','--coff-load-config',str(out/'Bin'/('lib'+module+'.dll'))]
    return commands


class PE:
    """Bounded PE data reader for source-defined full-module exports/imports."""
    def __init__(self,path):
        self.data=read_relative(Path(path).parent,Path(path).name,64*1024**2)
        need(len(self.data)>=64 and self.data[:2]==b'MZ','full_module_pe_header')
        self.pe=self.number('I',60);self.opt=self.pe+24
        need(self.pe>=64 and self.data[self.pe:self.pe+4]==b'PE\0\0','full_module_pe_header')
        self.machine=self.number('H',self.pe+4);count=self.number('H',self.pe+6);size=self.number('H',self.pe+20)
        need(1<=count<=96 and size>=240 and self.number('H',self.opt)==0x20b and self.number('I',self.opt+108)==16,'full_module_pe_optional')
        need(self.number('H',self.pe+22)&0x2000,'full_module_not_dll')
        self.sections=[]
        for i in range(count):
            at=self.opt+size+40*i;virtual,rva,raw_size,raw,flags=[self.number('I',at+n) for n in (8,12,16,20,36)]
            need(raw+raw_size<=len(self.data),'full_module_pe_section')
            self.sections.append((rva,min(virtual,raw_size),raw,flags))
    def number(self,fmt,at):
        need(0<=at and at+struct.calcsize('<'+fmt)<=len(self.data),'full_module_pe_bounds')
        return struct.unpack_from('<'+fmt,self.data,at)[0]
    def mapped(self,rva,size):
        matches=[raw+rva-base for base,span,raw,_ in self.sections if size>0 and rva>=base and rva-base+size<=span]
        need(len(matches)==1,'full_module_unmapped_rva');return matches[0]
    def string(self,rva):
        at=self.mapped(rva,1);end=self.data.find(b'\0',at,min(at+4096,len(self.data)))
        need(end>at,'full_module_pe_string');self.mapped(rva,end-at+1)
        value=self.data[at:end].decode('ascii');need(all(32<=ord(c)<127 for c in value),'full_module_pe_string');return value
    def directory(self,index):
        return self.number('I',self.opt+112+index*8),self.number('I',self.opt+116+index*8)
    def exports(self):
        rva,size=self.directory(0);at=self.mapped(rva,size);need(size>=40,'full_module_export_directory')
        functions,names=self.number('I',at+20),self.number('I',at+24)
        need(0<names<=functions<=4096,'full_module_export_count')
        table=self.mapped(self.number('I',at+32),names*4);ordinals=self.mapped(self.number('I',at+36),names*2)
        entries=self.mapped(self.number('I',at+28),functions*4);result={};named_ordinals=set()
        for i in range(names):
            name=self.string(self.number('I',table+4*i));ordinal=self.number('H',ordinals+2*i)
            need(name not in result and ordinal<functions and ordinal not in named_ordinals,'full_module_export_duplicate');named_ordinals.add(ordinal)
            target=self.number('I',entries+4*ordinal);need(not(rva<=target<rva+size),'full_module_forwarded_export')
            self.mapped(target,1);result[name]=target
        need(all(not self.number('I',entries+4*i) or i in named_ordinals for i in range(functions)),'full_module_ordinal_export')
        return result
    def imports(self):
        rva,size=self.directory(1);need(rva and size>=20 and size<=1024*1024,'full_module_import_directory')
        at=self.mapped(rva,size);result=[];terminated=False
        for offset in range(0,size-19,20):
            parts=struct.unpack_from('<5I',self.data,at+offset)
            if not any(parts):terminated=True;break
            name=self.string(parts[3]).lower();need(name not in result,'full_module_import_duplicate');result.append(name)
        need(terminated,'full_module_import_terminator');return sorted(result)


def module_exports(source,target):
    path=source/'Source/Windows'/('ARM64EC' if target=='arm64ec' else 'WOW64')/('libarm64ecfex.def' if target=='arm64ec' else 'libwow64fex.def')
    lines=read_relative(path.parent,path.name,65536).decode().splitlines();names={}
    exporting=False
    for line in lines:
        line=line.split(';',1)[0].strip()
        if not line:continue
        if line=='EXPORTS':exporting=True;continue
        if not exporting:need(line.startswith('LIBRARY '),'full_source_def_header');continue
        parts=line.split();need(len(parts) in (1,2) and (len(parts)==1 or parts[1]=='DATA'),'full_source_def_entry')
        need(parts[0] not in names,'full_source_def_duplicate');names[parts[0]]=len(parts)==2
    need(len(names)==(20 if target=='arm64ec' else 23),'full_source_def_count');return names


def module_facts(path,source,target):
    pe=PE(path);need(pe.directory(13)==(0,0),'full_module_delay_import');exports=pe.exports();expected=module_exports(source,target)
    need(set(exports)==set(expected),'full_module_export_set')
    imports=pe.imports();allowed={'ntdll.dll'}|({'wow64.dll'} if target=='wow64' else set())
    need(imports and set(imports)<=allowed and 'ntdll.dll' in imports,'unexpected_full_module_dependency')
    builtin=read_relative(source,'Source/Windows/wine_builtin.bin',32)
    need(pe.data[64:96]==builtin,'full_module_wine_builtin_marker')
    facts={'outer_machine':pe.machine,'exports':[{'name':name,'rva':exports[name],'source_data_export':expected[name]} for name in sorted(exports)],
           'imports':imports,'wine_builtin_marker_sha256':hashlib.sha256(builtin).hexdigest(),'pe_execution':False,'source_custom_crt':True}
    if target=='arm64ec':
        # The source-defined FEX LoadConfig.S emits the same Version 1 bounded
        # range format. Reuse its byte algorithm, then add actual full-module
        # source/link/exports/CRT proof; this is not the default-CRT fixture gate.
        raw=read_relative(source,'Source/Windows/Common/LoadConfig.S',65536)
        need(b'.4byte 1 /* Version */' in raw,'full_module_chpe_source_contract')
        facts['arm64ec_metadata']=inspect_fixture_arm64ec(path)
    else:need(pe.machine==0xaa64,'full_wow64_not_arm64_pe')
    return facts


def compile_database(output):
    """Read CMake's array artifact through the owner's strict bounded decoder.

    The shared owner intentionally admits only object-root records. A closed
    envelope preserves its duplicate-key, node, depth and string validation
    without broadening that record contract for this generated array format.
    """
    limit=4*1024**2
    raw=read_relative(output,'compile_commands.json',limit)
    envelope=decode_json(b'{"commands":'+raw+b'}',max_bytes=limit+32)
    exact(envelope,('commands',),'full_compile_database_envelope')
    rows=envelope['commands']
    need(isinstance(rows,list) and 0<len(rows)<=25000,'full_compile_database')
    for row in rows:
        exact(row,('directory','command','file','output'),'full_compile_database_fields')
        need(all(isinstance(value,str) and value for value in row.values()),'full_compile_database_types')
    return rows


def compile_command_proof(row,output,source,tc,triple,features):
    need(isinstance(row,dict) and set(row)=={'directory','command','file','output'},'full_compile_database_fields')
    need(all(isinstance(value,str) and value for value in row.values()),'full_compile_database_types')
    need(Path(row['directory'])==output,'full_compile_directory')
    relative(row['output']);object_path=output.joinpath(*relative(row['output']))
    source_path=Path(row['file']);need(source_path.is_absolute() and '..' not in source_path.parts and source_path.is_relative_to(source),'full_compile_source_binding')
    arguments=shlex.split(row['command'])
    suffix='-clang++' if source_path.suffix in ('.cpp','.cc','.cxx') else '-clang'
    need(arguments and arguments[0]==str(tc/'bin'/(triple+suffix)),'full_compile_triple_compiler')
    need(arguments.count('-c')==1 and arguments.count('-o')==1 and arguments.index('-c')+1<len(arguments) and arguments.index('-o')+1<len(arguments),'full_compile_operand_count')
    compile_input=Path(arguments[arguments.index('-c')+1]);compile_output=Path(arguments[arguments.index('-o')+1])
    need(compile_input==source_path and '..' not in compile_output.parts,'full_compile_operands')
    if not compile_output.is_absolute():compile_output=output/compile_output
    need(compile_output==object_path,'full_compile_operands')
    need(not any(arg.startswith(('--target','-target')) for arg in arguments[1:]),'full_compile_unreviewed_target_override')
    responses=[arg[1:] for arg in arguments[1:] if arg.startswith('@')]
    need(len(responses)<=1 and all(name==row['output']+'.modmap' for name in responses),'full_compile_unreviewed_response')
    for name in responses:need(read_relative(output,name,65536)==b'','full_compile_nonempty_module_map')
    need(not any(arg.startswith('-o') and arg!='-o' for arg in arguments[1:]),'full_compile_unreviewed_output_override')
    need(not any(arg in ('-Xclang','-Xpreprocessor') or arg.startswith('-Wp,') for arg in arguments[1:]),'full_compile_unreviewed_preprocessor_override')
    defines={};undefines=set();i=1
    while i<len(arguments):
        argument=arguments[i]
        if argument in ('-D','-U'):
            need(i+1<len(arguments),'full_compile_macro_operand');value=arguments[i+1];kind=argument;i+=2
        elif argument.startswith(('-D','-U')):
            value=argument[2:];kind=argument[:2];i+=1
        else:i+=1;continue
        name,_,value_=value.partition('=')
        if kind=='-U':undefines.add(name)
        else:defines.setdefault(name,[]).append(value_ or '1')
    if source_path.suffix!='.S':
        need(defines.get('PEAR_FEX_DARWIN')==['1'] and 'PEAR_FEX_DARWIN' not in undefines,'full_compile_policy_define')
    if suffix=='-clang++':
        need(defines.get('PEAR_FEX_DARWIN_DCACHE_LOG2')==[str(features['dcache_line_log2'])] and 'PEAR_FEX_DARWIN_DCACHE_LOG2' not in undefines,'full_compile_cache_define')
        for disabled,enabled in (('-fno-exceptions','-fexceptions'),('-fno-strict-aliasing','-fstrict-aliasing')):
            choices=[arg for arg in arguments if arg in (disabled,enabled)]
            need(choices and choices[-1]==disabled,'full_compile_language_policy')
    return object_path


def ninja_tokens(text):
    """Read escaped Ninja paths; never evaluate variables or execute recipes."""
    result=[];word=[];i=0
    while i<len(text):
        char=text[i]
        if char=='$':
            need(i+1<len(text) and text[i+1] in '$ :','full_ninja_unreviewed_variable')
            word.append(text[i+1]);i+=2;continue
        if char.isspace():
            if word:result.append(''.join(word));word=[]
        else:word.append(char)
        i+=1
    if word:result.append(''.join(word))
    return result


def full_link_edge(text,output,source,module,object_paths,tc):
    blocks=[];lines=text.splitlines()
    for index,line in enumerate(lines):
        if not line.startswith('build '):continue
        match=re.fullmatch(r'build (.*): ([^ ]+) ?(.*)',line)
        if not match or 'Bin/'+module not in match[1]:continue
        outputs=ninja_tokens(match[1])
        if 'Bin/'+module not in outputs:continue
        variables={};cursor=index+1
        while cursor<len(lines) and lines[cursor].startswith('  '):
            entry=re.fullmatch(r'  ([A-Z_]+) = (.*)',lines[cursor]);need(entry and entry[1] not in variables,'full_link_edge_fields')
            variables[entry[1]]=entry[2];cursor+=1
        blocks.append((match[2],ninja_tokens(match[3]),variables))
    need(len(blocks)==1,'full_module_link_edge')
    rule,dependencies,variables=blocks[0]
    need(rule.startswith('CXX_SHARED_LIBRARY_LINKER__') and variables.get('TARGET_FILE')=='Bin/'+module,'full_module_link_edge')
    explicit=dependencies[:dependencies.index('|')] if '|' in dependencies else dependencies[:dependencies.index('||')] if '||' in dependencies else dependencies
    actual_objects=[]
    for name in explicit:
        relative(name);path=output.joinpath(*relative(name));need(path.as_posix() in object_paths,'full_link_object_not_built');actual_objects.append(path.as_posix())
    need(actual_objects and len(set(actual_objects))==len(actual_objects),'full_link_object_closure')
    target='ARM64EC' if module=='libarm64ecfex.dll' else 'WOW64'
    expected_flags=['-static','-Wl,--file-alignment=4096,/mllvm:-align-loops=1','-Wl,-Xlink=/map:link.map',
                    '-static','-nostdlib','-nostartfiles','-nodefaultlibs','-lc++abi','-lc++','-lunwind',
                    str(source/'Source/Windows'/target/(module.removesuffix('.dll')+'.def'))]
    need(shlex.split(variables.get('LINK_FLAGS',''))==expected_flags,'full_link_flags')
    libraries=[];declared_archives=set()
    for name in shlex.split(variables.get('LINK_LIBRARIES','')):
        if name.startswith('-l'):
            need(name in ('-lsynchronization','-lmincore','-lntdll'),'full_link_unreviewed_library')
            path=tc/'aarch64-w64-mingw32/lib'/('lib'+name[2:]+'.a')
        else:
            path=Path(name)
            if not path.is_absolute():relative(name);path=output.joinpath(*relative(name))
        need('..' not in path.parts and (path.is_relative_to(output) or path.is_relative_to(tc)) and path.suffix=='.a','full_link_archive_scope')
        if not name.startswith('-l'):declared_archives.add(str(path))
        libraries.append({'path':str(path),'sha256':sha256(path),'size_bytes':path.stat().st_size,'archive':archive_machines(path)})
    implicit=dependencies[dependencies.index('|')+1:dependencies.index('||') if '||' in dependencies else len(dependencies)] if '|' in dependencies else []
    implicit_archives=set()
    for name in implicit:
        path=Path(name)
        if not path.is_absolute():relative(name);path=output.joinpath(*relative(name))
        if path.suffix=='.a':implicit_archives.add(str(path))
        else:need(path==source/'Source/Windows'/target/(module.removesuffix('.dll')+'.def'),'full_link_unreviewed_dependency')
    need(declared_archives==implicit_archives,'full_link_archive_edge_closure')
    required=[output/'Source/Windows/Common/libCommonWindowsRuntime.a',output/'Source/Windows/Common/libCommonWindows.a',output/'Source/Windows/libntdll_ex.a']
    need(all(str(path) in {row['path'] for row in libraries} for path in required),'full_link_required_archive')
    # The relative /map token is valid only for this source-defined target cwd;
    # the recorded CMake --build target and exact target edge are replayed too.
    return {'target':'Bin/'+module,'working_directory':str(output),'flags':expected_flags,'objects':actual_objects,'linked_archives':libraries}


def source_map_proof(text):
    symbols={};selected={}
    for line in text.splitlines():
        match=re.fullmatch(r' +[0-9a-fA-F]{4}:[0-9a-fA-F]{8,16} +([^ ]+) +[0-9a-fA-F]{16} +([^ :]+):([^ ]+)',line)
        if not match:continue
        symbol,archive,member=match.groups();symbol=symbol.removeprefix('#')
        symbols.setdefault(symbol,set()).add((archive,member));selected.setdefault(archive,set()).add(member)
    required={'DllMainCRTStartup':('libCommonWindowsRuntime','CRT.cpp.obj'),
        '_ZN3FEX7Windows12DarwinPolicy5ApplyEv':('libCommonWindows','DarwinConfigPolicy.cpp.obj'),
        'GetSystemInfo':('libCommonWindowsRuntime','Misc.cpp.obj'),
        'NtQuerySystemInformation':('libntdll_ex','ntdll.dll')}
    aliases={name:symbols[name] for name in ('__imp_GetSystemInfo','__imp_aux_GetSystemInfo') if name in symbols}
    need(all(owner=={('libCommonWindowsRuntime','Misc.cpp.obj')} for owner in aliases.values()),'full_source_map_provider_alias')
    required.update({name:('libCommonWindowsRuntime','Misc.cpp.obj') for name in aliases})
    for symbol,owner in required.items():need(symbols.get(symbol)=={owner},'full_source_map_owner:'+symbol)
    return {'required_symbols':{symbol:{'archive':owner[0],'member':owner[1]} for symbol,owner in required.items()},
            'provider_aliases':{name:('selected_source_owner' if name in aliases else 'unselected') for name in ('__imp_GetSystemInfo','__imp_aux_GetSystemInfo')},
            'selected_archive_members':{name:sorted(members) for name,members in sorted(selected.items())}}


def cache_values(raw):
    values={}
    for line in raw.decode().splitlines():
        if not line or line.startswith(('#','//')):continue
        match=re.fullmatch(r'([^:=]+):([^=]+)=(.*)',line)
        need(match and match[1] not in values,'full_cache_fields')
        values[match[1]]=match[3]
    return values


def inspect_complete(root,cross,features,config):
    artifacts=inspect_native(root);source=Path(root)/'source';reader=wine_readers()
    proofs={}
    for target,module,machine in (('arm64ec','libarm64ecfex.dll',0xa641),('wow64','libwow64fex.dll',0xaa64)):
        output=Path(root)/'pe'/target;relative_output='pe/'+target
        names={'CMakeCache.txt':'cmake_cache','build.ninja':'ninja_recipe','compile_commands.json':'compile_database','link.map':'full_module_link_map',
               **{'CMakeFiles/3.31.8/CMake'+kind+'Compiler.cmake':'compiler_data' for kind in ('C','CXX','ASM')},
               'Source/Windows/Common/libCommonWindowsRuntime.a':'source_custom_crt_archive',
               'Source/Windows/libntdll_ex.a':'source_ntdll_import_archive',
               'Bin/'+module:'full_fex_module'}
        if target=='wow64':names['Source/Windows/libwow64_ex.a']='source_wow64_import_archive'
        object_rows=[]
        for directory,directories,files_ in os.walk(output):
            directories.sort()
            for name in sorted(files_):
                p=Path(directory)/name
                if p.name.endswith('.obj.modmap'):
                    need(not p.is_symlink() and p.stat().st_size==0,'full_compile_nonempty_module_map')
                    artifacts.append({'path':p.relative_to(root).as_posix(),'role':'empty_compiler_module_map','sha256':sha256(p),'size_bytes':0})
                    continue
                if p.suffix not in ('.obj','.o'):continue
                if 'CMakeFiles/3.31.8/' in str(p):continue
                need(not p.is_symlink() and reader.coff_machine(p)==machine,'full_source_object_machine')
                object_rows.append({'path':p.relative_to(root).as_posix(),'sha256':sha256(p),'size_bytes':p.stat().st_size,'machine':machine})
        object_rows.sort(key=lambda row:row['path'])
        need(len(object_rows)>0 and any('/CRT/' in r['path'] for r in object_rows) and any('CPUFeatures.cpp' in r['path'] for r in object_rows)
             and any('DarwinConfigPolicy.cpp' in r['path'] for r in object_rows),'full_source_object_closure')
        for rel,role in names.items():
            path=output/rel;row={'path':relative_output+'/'+rel,'role':role,'sha256':sha256(path),'size_bytes':path.stat().st_size}
            if role=='full_fex_module':row['pe']=module_facts(path,source,target)
            elif role.endswith('_archive'):row['archive']=archive_machines(path)
            artifacts.append(row)
        ninja=read_relative(output,'build.ninja',16*1024**2).decode()
        link_edge=full_link_edge(ninja,output,source,module,{str(Path(root)/row['path']) for row in object_rows},Path(cross['cross_tools']))
        cache=cache_values(read_relative(output,'CMakeCache.txt',4*1024**2))
        tc=Path(cross['cross_tools']);triple='arm64ec-w64-mingw32' if target=='arm64ec' else 'aarch64-w64-mingw32'
        expected={'CMAKE_BUILD_TYPE':'RelWithDebInfo','MINGW_TRIPLE':triple,
             'CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_TRY_COMPILE_TARGET_TYPE':'STATIC_LIBRARY',
             'CMAKE_DISABLE_FIND_PACKAGE_unordered_dense':'TRUE','CMAKE_DISABLE_FIND_PACKAGE_range-v3':'TRUE',
             'Python_EXECUTABLE':cross['build_auxiliary_tools']['python']['path'],
             'CMAKE_CXX_FLAGS':'-std=c++20 -fno-exceptions -fno-strict-aliasing -fno-stack-protector -DPEAR_FEX_DARWIN=1 -DPEAR_FEX_DARWIN_DCACHE_LOG2='+str(features['dcache_line_log2']),
             'CMAKE_C_FLAGS':'-DPEAR_FEX_DARWIN=1','OVERRIDE_HASH':BASE_COMMIT,'OVERRIDE_VERSION':'Pear-pinned-FEX'}
        expected.update({key:'ON' if value is True else 'OFF' if value is False else str(value) for key,value in config['cmake_options'].items()})
        need(all(cache.get(key)==value for key,value in expected.items()),'full_source_configuration')
        for kind,suffix in (('C','-clang'),('CXX','-clang++'),('ASM','-clang')):
            text=read_relative(output,'CMakeFiles/3.31.8/CMake'+kind+'Compiler.cmake',1024*1024).decode()
            definitions=re.findall(r'^set\(CMAKE_'+kind+r'_COMPILER "([^"\r\n]+)"\)$',text,re.M)
            need(len(definitions)==1,'full_target_compiler_data')
            selected=Path(definitions[0])
            need(selected==tc/'bin'/(triple+suffix) and selected.resolve(strict=True).is_relative_to(tc.resolve(strict=True)),'full_target_compiler_changed')
        database=compile_database(output)
        need(isinstance(database,list) and database,'full_compile_database')
        actual_outputs={row['path'] for row in object_rows}
        described_outputs=set()
        for row in database:
            need(isinstance(row,dict) and set(row)=={'directory','command','file','output'},'full_compile_database_fields')
            relative(row['output']);output_path=Path(row['directory']).joinpath(*relative(row['output']))
            if not output_path.is_relative_to(root):raise Error('full_compile_output_scope')
            if output_path.relative_to(root).as_posix() not in actual_outputs:continue
            path=compile_command_proof(row,output,source,tc,triple,features)
            rel=path.relative_to(root).as_posix();need(rel not in described_outputs,'full_compile_duplicate_output');described_outputs.add(rel)
        need(described_outputs==actual_outputs,'full_compile_object_database_closure')
        link_map=read_relative(output,'link.map',16*1024**2).decode()
        map_proof=source_map_proof(link_map)
        proofs[target]={'objects':object_rows,'custom_crt_link':True,'link_edge':link_edge,'map_proof':map_proof,
                        'runtime_policy_source_enforced':True,'processor_count_execution':'unperformed','guest_execution':False}
    return artifacts,proofs


def verify_build(root):
    """Replay closed source, native build, command and current artifact identities."""
    root=operation_output(root,require_empty=False,create=False)
    need(not (root/'build-failed.json').exists(),'failed_component_build')
    data=record(load_json(root/'build.json'),'fex_modules_build')
    exact(data,('schema_version','record_kind','scope','phase','bindings','producer_sha256','fixture_sha256',
          'patch_series_sha256','materialized_source','host_features','commands','artifacts','native_built','component_built',
          'full_custom_crt_modules','cross','module_proofs','admission','passed',*FALSE_FLAGS),'build_record_fields')
    need(data['scope']=='fex_component' and data['passed'] is True and data['phase'] in ('native','complete')
         and data['native_built'] is True and data['component_built'] is (data['phase']=='complete')
         and data['full_custom_crt_modules']==('built_not_executed' if data['phase']=='complete' else 'unperformed') and all(data[key] is False for key in FALSE_FLAGS),'build_scope_overclaim')
    bindings=data['bindings'];exact(bindings,('inputs','config','toolchain','prepared','tools','host_metadata'),'build_binding_closure')
    for name in ('inputs','config','toolchain','host_metadata'):
        ref=bindings[name];need(sha256(Path(ref['path']))==ref['sha256'],'build_input_changed')
    prepared=Path(bindings['prepared']['path']);tools=Path(bindings['tools']['path'])
    need(sha256(prepared/'prepared.json')==bindings['prepared']['sha256'] and sha256(tools/'prepared.json')==bindings['tools']['sha256'],'build_prerequisite_changed')
    verify_prepared(prepared,expected_inputs_sha256=bindings['inputs']['sha256'])
    tool_receipt=verify_tools(tools,Path(bindings['toolchain']['path']))
    lock=record(load_json(bindings['toolchain']['path']),'fex_toolchain')
    config=validate_config(load_json(bindings['config']['path']),bindings['inputs']['sha256'])
    need(data['producer_sha256']=={path:sha256(REPO/path) for path in PRODUCERS} and data['fixture_sha256']==sha256(FIXTURE),'build_producer_changed')
    series=patch_set();need(data['patch_series_sha256']==sha256(PATCH_ROOT/'series.json'),'patch_series_changed')
    expected,_=derive_source(prepared,series)
    source_ref=data['materialized_source']
    need(source_ref['path']=='materialized-source.json' and sha256(root/source_ref['path'])==source_ref['sha256'],'materialized_manifest_changed')
    source_record=record(load_json(root/source_ref['path']),'fex_materialized_source')
    need(source_record=={'schema_version':1,'record_kind':'fex_materialized_source','scope':'fex_component','files':expected}
         and source_files(root/'source')==expected,'materialized_source_changed')
    features=host_metadata(Path(bindings['host_metadata']['path']))
    need(features==data['host_features'],'host_feature_receipt_changed')
    if data['phase']=='complete':
        cross=data['cross'];need(isinstance(cross,dict),'full_build_cross_inputs')
        expected_cross=cross_inputs(Path(cross['cross_tools']),Path(cross['wine_roles']['path']),lock,tool_receipt)
        need(expected_cross==cross,'full_build_cross_changed')
        recipe=complete_recipe(root,tools,lock,features,config,cross)
    else:
        need(data['cross'] is None and data['module_proofs']=={},'native_build_module_overclaim')
        recipe=native_recipe(root,tools,lock,features)
    seen=set()
    need(isinstance(data['commands'],list) and len(data['commands'])==len(recipe),'build_command_closure')
    for row in data['commands']:
        exact(row,('id','argv','cwd','environment','exit_code','elapsed_ms','status','logs'),'build_command_fields')
        ident=row['id'];need(ident in recipe and ident not in seen,'build_command_closure');seen.add(ident)
        need(row['argv']==recipe[ident] and row['cwd']==str(root) and row['environment']==(complete_environment(lock,data['cross']) if data['phase']=='complete' else environment(lock))
             and type(row['exit_code']) is int and row['exit_code']==0 and row['status']=='completed' and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0,'build_command_recipe_changed')
        need(set(row['logs'])=={'stdout','stderr'},'build_command_log_closure')
        for stream,ref in row['logs'].items():
            exact(ref,('path','size_bytes','sha256'),'build_log_fields')
            need(ref['path']==f'logs/{ident}/{stream}.bin' and type(ref['size_bytes']) is int and 0<=ref['size_bytes']<=4*1024**2,'build_log_path')
            raw=read_relative(root,ref['path'],4*1024**2)
            need(len(raw)==ref['size_bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'build_log_changed')
    need(seen==set(recipe),'build_command_closure')
    if data['phase']=='complete':
        artifacts,proofs=inspect_complete(root,data['cross'],features,config)
        need(artifacts==data['artifacts'] and proofs==data['module_proofs'],'full_module_artifact_changed')
    else:need(inspect_native(root)==data['artifacts'],'native_artifact_changed')
    exact(data['admission'],('free_before_bytes','parallel_jobs','full_build_peak'),'build_admission_fields')
    need(data['admission']['full_build_peak']=='unknown','build_peak_overclaim')
    need(type(data['admission']['free_before_bytes']) is int and data['admission']['free_before_bytes']>=(8 if data['phase']=='complete' else 2)*1024**3
         and data['admission']['parallel_jobs']==1,'build_admission_changed')
    return data


def modules(args):
    root=operation_output(args.output)
    data={'schema_version':1,'record_kind':'fex_modules_build','scope':'fex_component','phase':args.phase,
          'native_built':False,'component_built':False,'full_custom_crt_modules':'unperformed','cross':None,'module_proofs':{},'commands':[],**dict.fromkeys(FALSE_FLAGS,False)}
    try:
        # Initial native admission is deliberately incomplete for the full module gate.
        need(args.phase in ('native','complete'),'unsupported_build_phase')
        inputs=Path(args.inputs).resolve();config=Path(args.config).resolve();prepared=Path(args.prepared).resolve();tools=Path(args.tools).resolve();metadata=Path(args.host_metadata).resolve()
        lock_path=REPO/'runtime/fex/toolchain.json';lock=record(load_json(lock_path),'fex_toolchain')
        config_data=validate_config(load_json(config),sha256(inputs));verify_prepared(prepared,expected_inputs_sha256=sha256(inputs));tool_receipt=verify_tools(tools,lock_path)
        features=host_metadata(metadata);series=patch_set()
        data['bindings']={name:{'path':str(path),'sha256':sha256(path)} for name,path in (('inputs',inputs),('config',config),('toolchain',lock_path),('host_metadata',metadata))}
        data['bindings'].update(prepared={'path':str(prepared),'sha256':sha256(prepared/'prepared.json')},tools={'path':str(tools),'sha256':sha256(tools/'prepared.json')})
        data['producer_sha256']={path:sha256(REPO/path) for path in PRODUCERS};data['fixture_sha256']=sha256(FIXTURE)
        data['patch_series_sha256']=sha256(PATCH_ROOT/'series.json');data['host_features']=features
        if args.phase=='complete':
            need(args.cross_tools and args.wine_roles,'full_build_missing_cross_inputs')
            data['cross']=cross_inputs(Path(args.cross_tools).resolve(),Path(args.wine_roles).resolve(),lock,tool_receipt)
        free=shutil.disk_usage(root).free;need(free>=(8 if args.phase=='complete' else 2)*1024**3,'component_build_disk_admission')
        data['admission']={'free_before_bytes':free,'parallel_jobs':1,'full_build_peak':'unknown'}
        expected,changes=derive_source(prepared,series)
        shutil.copytree(prepared/'sources/fex',root/'source')
        for path,content in changes.items():
            destination=root/'source'/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
            destination.chmod(next(row['mode'] for row in expected if row['path']==path))
        need(source_files(root/'source')==expected,'source_copy_identity')
        data['materialized_source']=write_json(root/'materialized-source.json',{'schema_version':1,'record_kind':'fex_materialized_source','scope':'fex_component','files':expected})
        (root/'fixtures').mkdir();(root/'install').mkdir()
        recipe=complete_recipe(root,tools,lock,features,config_data,data['cross']) if args.phase=='complete' else native_recipe(root,tools,lock,features)
        env=complete_environment(lock,data['cross']) if args.phase=='complete' else environment(lock)
        for ident,argv in recipe.items():run_command(root,ident,argv,env,data['commands'])
        for name in ('libarm64ecfex.so','libwow64fex.so'):
            original=root/'native'/name;destination=root/'install'/name
            shutil.copyfile(original,destination);destination.chmod(original.stat().st_mode & 0o777)
            need(sha256(destination)==sha256(original),'native_install_copy_changed')
        if args.phase=='complete':
            data['artifacts'],data['module_proofs']=inspect_complete(root,data['cross'],features,config_data)
            data.update(component_built=True,full_custom_crt_modules='built_not_executed')
        else:data['artifacts']=inspect_native(root)
        data['native_built']=True;data['passed']=True
        write_json(root/'build.json',data);verify_build(root)
        return data
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError) as exc:
        data.update(passed=False,error=getattr(exc,'code',type(exc).__name__))
        write_json(root/'build-failed.json',data);raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('modules',))
    parser.add_argument('--phase',choices=('native','complete'),default='complete')
    for name in ('inputs','config','prepared','tools','host-metadata','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--cross-tools');parser.add_argument('--wine-roles')
    parser.add_argument('--require-empty',action='store_true',required=True)
    args=parser.parse_args()
    try:
        data=modules(args)
        print('PASS: '+('native UnixLib and full custom-CRT PE modules built' if data['component_built'] else 'native UnixLib built; full PE modules unperformed')+'; FEX/PE/JIT/guest execution unperformed')
        return 0
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError) as exc:
        print('FAIL: '+getattr(exc,'code',type(exc).__name__),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
