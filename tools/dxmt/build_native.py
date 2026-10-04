#!/usr/bin/env python3
"""Prepare and build isolated LLVM 15/native DXMT shader prerequisites.

Source derivation, LLVM compilation and Metal-dependent compilation are separate
operations. Every native operation requires explicit jobs and storage limits;
those limits are operational ceilings, never measurements of the build peak.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import sys
import time
from common import (REPO, MACH_ARM64, Error, clean_env, decode_json, digest, encoded, fields,
                    git, load_json, need, open_relative, output_directory, owned_directory, read_relative,
                    real_directory, relative, sha256, tree_entries, validate_bare_repo, write_new)
from prepare import validate_inputs, verify_prepared
import tools

LLVM_COMMIT='8dfdcc7b7bf66834a761bd8de445840ef68e4d1a'
SOURCE_PREFIXES=('llvm/','cmake/')
SOURCE_EXCLUDES=tuple('llvm/'+name+'/' for name in ['test','unittests','docs','examples','benchmarks'])
MAX_SOURCE=256*1024**2
MAX_OUTPUT_ENTRIES=100000
LLVM_LIBRARIES=['LLVMPasses','LLVMTarget','LLVMObjCARCOpts','LLVMCoroutines','LLVMipo','LLVMInstrumentation',
 'LLVMVectorize','LLVMLinker','LLVMIRReader','LLVMAsmParser','LLVMFrontendOpenMP','LLVMScalarOpts',
 'LLVMInstCombine','LLVMAggressiveInstCombine','LLVMTransformUtils','LLVMBitWriter','LLVMAnalysis',
 'LLVMProfileData','LLVMSymbolize','LLVMDebugInfoPDB','LLVMDebugInfoMSF','LLVMDebugInfoDWARF','LLVMObject',
 'LLVMTextAPI','LLVMMCParser','LLVMMC','LLVMDebugInfoCodeView','LLVMBitReader','LLVMCore','LLVMRemarks',
 'LLVMBitstreamReader','LLVMBinaryFormat','LLVMSupport','LLVMDemangle']
LLVM_OPTIONS={'CMAKE_BUILD_TYPE':'Release','CMAKE_OSX_ARCHITECTURES':'arm64','CMAKE_OSX_DEPLOYMENT_TARGET':'14.0',
 'LLVM_HOST_TRIPLE':'arm64-apple-darwin','LLVM_ENABLE_ASSERTIONS':'ON','LLVM_ENABLE_ZSTD':'OFF',
 'LLVM_TARGETS_TO_BUILD':'','LLVM_BUILD_TOOLS':'OFF','BUG_REPORT_URL':'https://github.com/3Shain/dxmt',
 'PACKAGE_VENDOR':'DXMT','LLVM_VERSION_PRINTER_SHOW_HOST_TARGET_INFO':'OFF',
 'LLVM_INCLUDE_TESTS':'OFF','LLVM_INCLUDE_EXAMPLES':'OFF','LLVM_INCLUDE_BENCHMARKS':'OFF',
 'LLVM_INCLUDE_DOCS':'OFF','LLVM_INCLUDE_TOOLS':'OFF','LLVM_INCLUDE_UTILS':'OFF',
 'LLVM_INCLUDE_RUNTIMES':'OFF','LLVM_BUILD_RUNTIME':'OFF','LLVM_ENABLE_PROJECTS':'','LLVM_ENABLE_RUNTIMES':'',
 'LLVM_BINDINGS_LIST':'','LLVM_ENABLE_LIBEDIT':'OFF','LLVM_ENABLE_LIBPFM':'OFF','LLVM_ENABLE_FFI':'OFF',
 'LLVM_ENABLE_CURL':'OFF','LLVM_ENABLE_Z3_SOLVER':'OFF','LLVM_ENABLE_ZLIB':'FORCE_ON',
 'LLVM_ENABLE_LIBXML2':'FORCE_ON','LLVM_ENABLE_TERMINFO':'FORCE_ON', 'BUILD_SHARED_LIBS':'OFF',
 'LLVM_BUILD_LLVM_DYLIB':'OFF','LLVM_LINK_LLVM_DYLIB':'OFF','CMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH':'FALSE',
 'CMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH':'FALSE','CMAKE_FIND_USE_PACKAGE_REGISTRY':'FALSE',
 'CMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY':'FALSE','CMAKE_IGNORE_PREFIX_PATH':'/opt/homebrew;/usr/local;/opt/anaconda3'}
NATIVE_HEADERS=['include/llvm/Config/llvm-config.h','include/llvm/Config/abi-breaking.h']


def producers(repo=REPO):
    return {name:digest(read_relative(repo,name)) for name in ['tools/dxmt/build_native.py','tools/dxmt/tools.py',
             'tools/dxmt/common.py','tools/dxmt/prepare.py','tools/dxmt/check.py','tools/wine/common.py',
             'tools/wine/toolchain.py','tools/sources/validate_inventory.py']}


def select_llvm(entries):
    selected=[row for row in entries if (row['path'].startswith(SOURCE_PREFIXES)
               and not row['path'].startswith(SOURCE_EXCLUDES)) or row['path']=='LICENSE.TXT']
    need(selected and len(selected)<=20000,'llvm_source_selection')
    for row in selected:
        relative(row['path'])
        need(row['mode'] in ['100644','100755'],'llvm_selected_source_entry')
    need(any(r['path']=='llvm/CMakeLists.txt' for r in selected) and any(r['path']=='llvm/LICENSE.TXT' for r in selected)
         and any(r['path']=='cmake/Modules/ExtendPath.cmake' for r in selected),'llvm_required_source')
    return selected


def blob_sizes(repository,entries):
    argv=['/usr/bin/git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','protocol.allow=never',
          '--git-dir='+str(repository),'cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)']
    raw=('\n'.join(row['git_object'] for row in entries)+'\n').encode()
    result=subprocess.run(argv,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=clean_env(),timeout=120)
    need(result.returncode==0 and len(result.stdout)<=4*1024**2 and len(result.stderr)<=65536,'llvm_blob_measurement')
    lines=result.stdout.decode().splitlines()
    need(len(lines)==len(entries),'llvm_blob_measurement')
    sizes=[]
    for row,line in zip(entries,lines):
        blob,kind,size=line.split()
        need(blob==row['git_object'] and kind=='blob' and size.isdecimal(),'llvm_blob_measurement')
        size=int(size);need(0<=size<=32*1024**2,'llvm_blob_measurement')
        sizes.append(size)
    need(sum(sizes)<=MAX_SOURCE,'llvm_source_size_bound')
    return sizes


def materialize(repository,entries,sizes,destination):
    destination.mkdir()
    argv=['/usr/bin/git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','protocol.allow=never',
          '--git-dir='+str(repository),'cat-file','--batch']
    rows=[]
    # Only already measured objects are requested; no checkout/filter/submodule.
    proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=clean_env(),start_new_session=True,bufsize=0)
    started=time.monotonic();pending=bytearray();selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
    def exact(count):
        while len(pending)<count:
            need(time.monotonic()-started<600,'llvm_source_timeout')
            if not selector.select(0.1):continue
            block=os.read(proc.stdout.fileno(),min(65536,max(1,count-len(pending))))
            need(block,'llvm_source_truncated');pending.extend(block)
        result=bytes(pending[:count]);del pending[:count];return result
    def line():
        value=bytearray()
        for _ in range(128):
            value.extend(exact(1))
            if value[-1]==10:return value.decode().strip()
        raise Error('llvm_source_header_bound')
    try:
        for entry,size in zip(entries,sizes):
            need(time.monotonic()-started<600,'llvm_source_timeout')
            proc.stdin.write((entry['git_object']+'\n').encode());proc.stdin.flush()
            header=line()
            need(header==entry['git_object']+' blob '+str(size),'llvm_blob_header')
            content=exact(size)
            need(len(content)==size and exact(1)==b'\n'
                 and hashlib.sha1(f'blob {size}\0'.encode()+content).hexdigest()==entry['git_object'],'llvm_blob_identity')
            target=destination.joinpath(*relative(entry['path']));target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(content)
            mode=0o755 if entry['mode']=='100755' else 0o644;target.chmod(mode)
            rows.append({'path':entry['path'],'sha256':digest(content),'size_bytes':size,'mode':mode,'git_blob':entry['git_object']})
        proc.stdin.close();need(proc.wait(timeout=5)==0,'llvm_source_batch_failed')
    finally:
        if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)
        selector.close();proc.stdout.close()
        if not proc.stdin.closed:proc.stdin.close()
    return rows


def verify_source(root,repo=REPO):
    root=owned_directory(root,repo);value=load_json(root/'prepared.json')
    fields(value,['schema_version','record_kind','scope','inputs_ref','prepared_ref','producers','source','selection',
                  'manifest_ref','measured_source_bytes','materialized','runtime_eligible'],'dxmt_native_source_prepared')
    need(value['scope']=='dxmt_component' and value['materialized'] is True and value['runtime_eligible'] is False,'native_source_scope')
    need(value['producers']==producers(repo),'native_source_producer_changed')
    inp=read_relative(repo,value['inputs_ref']['path']);need(digest(inp)==value['inputs_ref']['sha256'],'native_source_inputs_changed')
    inputs=validate_inputs(decode_json(inp),repo)
    prepared=verify_prepared(value['prepared_ref']['path'],repo)
    need(sha256(Path(value['prepared_ref']['path'])/'prepared.json')==value['prepared_ref']['sha256']
         and prepared['inputs_ref']==value['inputs_ref'],'native_source_prepared_changed')
    component=next(c for c in inputs['components'] if c['id']=='llvm-dxmt')
    expected_repo=real_directory(prepared['source_cache']).joinpath(*relative(component['cache_path']))
    source,entries=tools.source_identity(expected_repo,LLVM_COMMIT)
    need(source==value['source'] and source['tree']==component['tree'],'native_source_identity')
    need(value['selection']=={'prefixes':list(SOURCE_PREFIXES),'excluded_prefixes':list(SOURCE_EXCLUDES),'root_notice':'LICENSE.TXT',
          'symlinks':'refused_in_selected_build_source','literal_names':'strict_materialized_paths_only'},'native_source_selection')
    entries=select_llvm(entries)
    manifest_raw=read_relative(root,value['manifest_ref']['path']);need(value['manifest_ref']['path']=='source-files.json'
         and digest(manifest_raw)==value['manifest_ref']['sha256'],'native_source_manifest_changed')
    manifest=decode_json(manifest_raw);fields(manifest,['schema_version','record_kind','files'],'dxmt_native_source_files')
    need(len(manifest['files'])==len(entries) and {r['path'] for r in manifest['files']}=={r['path'] for r in entries},'native_source_closure')
    by_path={r['path']:r for r in entries}
    actual=tools.files(root/'source')
    need(actual==[{k:r[k] for k in ['path','sha256','size_bytes','mode']} for r in manifest['files']],'native_source_bytes_changed')
    for row in manifest['files']:
        entry=by_path[row['path']]
        need(row['git_blob']==entry['git_object'] and row['mode']==(0o755 if entry['mode']=='100755' else 0o644),'native_source_mode')
        content=read_relative(root/'source',row['path'],32*1024**2)
        need(hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()==row['git_blob'],'native_source_blob')
    need(sum(r['size_bytes'] for r in manifest['files'])==value['measured_source_bytes'] and value['measured_source_bytes']<=MAX_SOURCE,'native_source_measurement')
    return value


def prepare_source(inputs_path,prepared_path,source_cache,output,repo=REPO):
    raw=read_relative(repo,inputs_path);inputs=validate_inputs(decode_json(raw),repo)
    prepared=verify_prepared(prepared_path,repo)
    cache=real_directory(source_cache)
    need(cache==real_directory(prepared['source_cache']),'native_source_cache')
    component=next(c for c in inputs['components'] if c['id']=='llvm-dxmt')
    need(component['commit']==LLVM_COMMIT,'native_llvm_pin')
    repository=cache.joinpath(*relative(component['cache_path']))
    source,entries=tools.source_identity(repository,LLVM_COMMIT)
    need(source['tree']==component['tree'] and source['listing_sha256']==component['listing']['value'],'native_llvm_tree')
    selected=select_llvm(entries);sizes=blob_sizes(repository,selected)
    root=output_directory(output,repo)
    need(shutil.disk_usage(root).free>=sum(sizes)+512*1024**2,'native_source_space')
    rows=materialize(repository,selected,sizes,root/'source')
    rows=sorted(rows,key=lambda r:r['path'])
    manifest={'schema_version':1,'record_kind':'dxmt_native_source_files','files':rows};write_new(root/'source-files.json',manifest)
    value={'schema_version':1,'record_kind':'dxmt_native_source_prepared','scope':'dxmt_component',
           'inputs_ref':{'path':inputs_path,'sha256':digest(raw)},
           'prepared_ref':{'path':str(owned_directory(prepared_path,repo)),'sha256':sha256(Path(prepared_path)/'prepared.json')},
           'producers':producers(repo),'source':source,
           'selection':{'prefixes':list(SOURCE_PREFIXES),'excluded_prefixes':list(SOURCE_EXCLUDES),'root_notice':'LICENSE.TXT',
                        'symlinks':'refused_in_selected_build_source','literal_names':'strict_materialized_paths_only'},
           'manifest_ref':{'path':'source-files.json','sha256':digest(encoded(manifest))},
           'measured_source_bytes':sum(sizes),'materialized':True,'runtime_eligible':False}
    write_new(root/'prepared.json',value);verify_source(root,repo)
    return value


def storage_policy(jobs,cap,reserve):
    need(type(jobs)is int and 1<=jobs<=4 and type(cap)is int and 2*1024**3<=cap<=32*1024**3
         and type(reserve)is int and 2*1024**3<=reserve<=16*1024**3,'native_build_admission')
    return {'jobs':jobs,'growth_ceiling_bytes':cap,'reserve_free_bytes':reserve,'measured_build_peak_bytes':None,
            'ceiling_is_peak_measurement':False,'check_interval_ms':1000}


def directory_usage(root):
    """Observe allocated bytes without following entries in a live build tree.

    Compiler temporary files may disappear after scandir. Only that absence is
    tolerated: existing links/special entries and other I/O errors still refuse
    admission. An lstat snapshot avoids classifying a vanished regular file as
    a special output or following a replacement link during size observation.
    """
    total,count=0,0
    def walk_error(error):
        if not isinstance(error,FileNotFoundError):raise error
    for directory,dirs,names in os.walk(root,followlinks=False,onerror=walk_error):
        try:current=Path(directory).lstat()
        except FileNotFoundError:
            dirs[:]=[];continue
        need(stat.S_ISDIR(current.st_mode),'native_build_directory_link')
        retained=[]
        for name in dirs:
            try:entry=(Path(directory)/name).lstat()
            except FileNotFoundError:continue
            need(stat.S_ISDIR(entry.st_mode),'native_build_directory_link')
            retained.append(name)
        dirs[:]=retained
        for name in names:
            try:entry=(Path(directory)/name).lstat()
            except FileNotFoundError:continue
            need(stat.S_ISREG(entry.st_mode),'native_build_special_output')
            count+=1;need(count<=MAX_OUTPUT_ENTRIES,'native_build_output_limit')
            total+=entry.st_blocks*512
    return total


def native_environment(root,tools_root,tool_record):
    env=clean_env()
    if 'HOME' in os.environ: env['HOME']=os.environ['HOME']
    env.update(TMPDIR=str(root/'tmp'),SDKROOT=tool_record['sdk']['path'],
               PATH=str(tools_root/'cmake/CMake.app/Contents/bin')+':'+str(tools_root/'ninja-source')+':/usr/bin:/bin:/usr/sbin:/sbin',
               PYTHONDONTWRITEBYTECODE='1')
    return env


def monitored_command(root,ident,argv,env,policy,commands,cwd=None,timeout=14400):
    """Own process group; stop on bounds and always preserve failed evidence."""
    logs=root/'logs'/ident;logs.mkdir(parents=True)
    start=time.monotonic()
    row={'id':ident,'argv':[str(v) for v in argv],'cwd':str(cwd or root),'environment':dict(env),'exit_code':None,
         'elapsed_ms':None,'stop_reason':None,'growth_bytes_observed':0,'logs':{}}
    failure=None;proc=None
    def observe_usage():
        try:used=directory_usage(root)
        except (Error,OSError) as error:
            if row['stop_reason'] is None:
                row['stop_reason']='inventory_error:'+(error.code if isinstance(error,Error) else type(error).__name__)
            raise
        row['growth_bytes_observed']=max(row['growth_bytes_observed'],used)
        return used
    def stop_process():
        if proc is not None and proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        if proc is not None:row['exit_code']=proc.wait(timeout=10)
    with (logs/'stdout').open('xb') as out,(logs/'stderr').open('xb') as err:
        try:
            observe_usage()
            proc=subprocess.Popen(row['argv'],cwd=cwd or root,env=env,stdout=out,stderr=err,start_new_session=True)
            while proc.poll() is None:
                used=observe_usage()
                reason=('growth_ceiling' if used>policy['growth_ceiling_bytes'] else 'free_reserve'
                        if shutil.disk_usage(root).free<policy['reserve_free_bytes'] else 'timeout'
                        if time.monotonic()-start>timeout else 'log_limit'
                        if (logs/'stdout').stat().st_size+(logs/'stderr').stat().st_size>32*1024**2 else None)
                if reason:
                    row['stop_reason']=reason;break
                time.sleep(1)
        except (Error,OSError,ValueError,subprocess.SubprocessError) as error:
            failure=error
            if row['stop_reason'] is None:row['stop_reason']='monitor_error:'+type(error).__name__
        finally:
            try:stop_process()
            except (OSError,subprocess.SubprocessError) as error:
                if failure is None:
                    failure=error;row['stop_reason']='cleanup_error:'+type(error).__name__
    try:
        final_used=observe_usage()
        if row['stop_reason'] is None:
            if final_used>policy['growth_ceiling_bytes']:row['stop_reason']='growth_ceiling'
            elif shutil.disk_usage(root).free<policy['reserve_free_bytes']:row['stop_reason']='free_reserve'
            elif (logs/'stdout').stat().st_size+(logs/'stderr').stat().st_size>32*1024**2:row['stop_reason']='log_limit'
    except (Error,OSError) as error:
        if failure is None:failure=error
        if row['stop_reason'] is None:row['stop_reason']='monitor_error:'+type(error).__name__
    row['elapsed_ms']=int((time.monotonic()-start)*1000)
    try:
        for stream in ['stdout','stderr']:
            path=logs/stream;row['logs'][stream]={'path':path.relative_to(root).as_posix(),'sha256':sha256(path),'size_bytes':path.stat().st_size}
    except (Error,OSError) as error:
        row['log_collection_error']=error.code if isinstance(error,Error) else type(error).__name__
        if failure is None:failure=error
        if row['stop_reason'] is None:row['stop_reason']='log_collection_error:'+row['log_collection_error']
    finally:commands.append(row)
    if failure is not None:raise failure
    need(row['stop_reason'] is None and row['exit_code']==0,'native_command_failed:'+ident)
    return row


def llvm_recipe(root,source_root,tools_root,tool_record,jobs):
    native=tool_record['native_tools'];sdk=tool_record['sdk']['path'];cmake=tools_root/'cmake/CMake.app/Contents/bin/cmake'
    options=dict(LLVM_OPTIONS)
    options.update(CMAKE_INSTALL_PREFIX=str(root/'install'),CMAKE_OSX_SYSROOT=sdk,CMAKE_C_COMPILER=native['clang']['path'],
      CMAKE_CXX_COMPILER=native['clang++']['path'],CMAKE_MAKE_PROGRAM=str(tools_root/'ninja-source/ninja'),
      Python3_EXECUTABLE=native['python']['path'],ZLIB_INCLUDE_DIR=sdk+'/usr/include',ZLIB_LIBRARY=sdk+'/usr/lib/libz.tbd',
      LIBXML2_INCLUDE_DIR=sdk+'/usr/include/libxml2',LIBXML2_LIBRARY=sdk+'/usr/lib/libxml2.tbd',
      Terminfo_LIBRARIES=sdk+'/usr/lib/libncurses.tbd')
    configure=['/usr/bin/arch','-arm64',str(cmake),'-S',str(source_root/'source/llvm'),'-B',str(root/'objects'),'-G','Ninja']
    configure+=['-D'+k+'='+v for k,v in options.items()]
    return {'llvm.configure':configure,
            'llvm.build':['/usr/bin/arch','-arm64',str(cmake),'--build',str(root/'objects'),'--parallel',str(jobs)],
            'llvm.install':['/usr/bin/arch','-arm64',str(cmake),'--install',str(root/'objects')]},options


def inspect_native_archive(path, *, root=None):
    """Inspect real regular Darwin archive members without executing libtool."""
    path=Path(path)
    # A dependent output can additionally bind every parent to its owned tree.
    data=read_relative(path.parent if root is None else root,
                       path.name if root is None else path.relative_to(root).as_posix(),128*1024**2)
    need(data.startswith(b'!<arch>\n'),'native_library_archive')
    at=8;cpus=[];count=0;members=[];metadata=[];names=set()
    while at<len(data):
        need(at+60<=len(data) and data[at+58:at+60]==b'`\n','native_archive_header')
        name=data[at:at+16].decode('ascii').strip();rawsize=data[at+48:at+58].strip()
        need(rawsize.isdigit(),'native_archive_size');size=int(rawsize);start=at+60;end=start+size
        need(end<=len(data),'native_archive_bounds');payload=data[start:end]
        if name.startswith('#1/'):
            n=int(name[3:]);need(0<n<=4096 and n<=len(payload),'native_archive_name')
            name=payload[:n].rstrip(b'\0').decode();payload=payload[n:]
        need(name not in names,'native_archive_duplicate_member');names.add(name)
        if name in ['__.SYMDEF','__.SYMDEF SORTED','__.SYMDEF_64','__.SYMDEF_64 SORTED']:
            metadata.append({'name':name,'sha256':digest(payload),'size_bytes':len(payload)})
        else:
            need(len(payload)>=32 and payload[:4]==b'\xcf\xfa\xed\xfe','native_archive_object')
            cpu,subtype,filetype=struct.unpack_from('<III',payload,4)
            need(cpu==MACH_ARM64 and filetype==1,'native_archive_requires_rosetta')
            cpus.append(cpu);count+=1;members.append({'name':name,'sha256':digest(payload),'size_bytes':len(payload),
                'cpu':cpu,'subtype':subtype,'filetype':filetype})
        at=end+(size&1)
    need(at==len(data) and count>0,'native_archive_empty')
    return {'sha256':digest(data),'size_bytes':len(data),'object_count':count,'architectures':sorted(set(cpus)),
            'members':members,'symbol_metadata':metadata,'symbol_link_compatibility':'established_only_by_actual_dependent_link'}


def inspect_llvm(root):
    install=root/'install'
    header=read_relative(install,'include/llvm/Config/llvm-config.h',1024*1024).decode()
    need(re.search(r'^#define LLVM_VERSION_MAJOR 15$',header,re.M) and re.search(r'^#define LLVM_VERSION_MINOR 0$',header,re.M)
         and re.search(r'^#define LLVM_VERSION_PATCH 7$',header,re.M),'native_llvm_version')
    need(not list((install/'lib').glob('*.dylib')),'unexpected_dynamic_llvm')
    inventory=tools.files(install)
    need(inventory and all('symlink' not in row for row in inventory),'native_installed_manifest_special_entry')
    library_paths=[row['path'] for row in inventory if row['path'].endswith('.a')]
    need(library_paths and all(path.startswith('lib/') for path in library_paths),'native_installed_library_location')
    libs={path:inspect_native_archive(install/path) for path in library_paths}
    need(all('lib/lib'+name+'.a' in libs for name in LLVM_LIBRARIES),'native_required_libraries_missing')
    tblgen=root/'objects/bin/llvm-tblgen'
    need(tblgen.is_file() and not tblgen.is_symlink() and tblgen.stat().st_mode&0o111,'native_tablegen_missing')
    built=read_relative(root,'objects/bin/llvm-tblgen',128*1024**2)
    reader=tools.readers();info=reader.inspect_macho(tblgen)
    need(info['architectures']==[MACH_ARM64] and info['filetype']==2 and all(d.startswith(('/usr/lib/','/System/Library/')) for d in info['dependencies']), 'tablegen_native_closure')
    installed=next((row for row in inventory if row['path']=='bin/llvm-tblgen'),None)
    need(installed is not None and installed['mode']&0o111,'installed_tablegen_missing')
    installed_bytes=read_relative(install,'bin/llvm-tblgen',128*1024**2)
    need(installed_bytes==built and installed['sha256']==digest(built),'installed_tablegen_origin_changed')
    installed_info=reader.inspect_macho(install/'bin/llvm-tblgen')
    need(installed_info==info,'installed_tablegen_native_closure')
    native_magic=[b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xfe\xed\xfa\xce',
                  b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf',b'\xbe\xba\xfe\xca',b'\xbf\xba\xfe\xca']
    for row in inventory:
        # LLVM15 add_tablegen installs this exact built utility independently of
        # LLVM_BUILD_TOOLS. No other native binary or shared library is admitted.
        with (install/row['path']).open('rb') as stream:magic=stream.read(4)
        need(magic not in native_magic or row['path']=='bin/llvm-tblgen','unexpected_installed_native_binary')
    headers=[{'path':name,'sha256':sha256(install/name),'size_bytes':(install/name).stat().st_size} for name in NATIVE_HEADERS]
    return {'installed_files':inventory,'libraries':libs,'headers':headers,'tablegen':{'path':'objects/bin/llvm-tblgen','sha256':digest(built),**info},
            'installed_tablegen':{'path':'bin/llvm-tblgen','sha256':digest(installed_bytes),'size_bytes':len(installed_bytes),
               'mode':installed['mode'],'built_origin':'objects/bin/llvm-tblgen',**installed_info},
            'llvm_version':'15.0.7','static_native_prerequisites':True}


def build_llvm(source_path,tools_path,output,jobs,cap,reserve,repo=REPO):
    source_root=owned_directory(source_path,repo);source=verify_source(source_root,repo)
    tools_root=owned_directory(tools_path,repo);tool_record=tools.verify_tools(tools_root,repo)
    policy=storage_policy(jobs,cap,reserve)
    need(shutil.disk_usage(source_root).free>=cap+reserve,'native_start_space_below_ceiling_and_reserve')
    root=output_directory(output,repo);(root/'tmp').mkdir();env=native_environment(root,tools_root,tool_record)
    recipe,options=llvm_recipe(root,source_root,tools_root,tool_record,jobs)
    value={'schema_version':1,'record_kind':'dxmt_llvm_native_build','scope':'dxmt_component','producers':producers(repo),
      'source_ref':{'path':str(source_root),'sha256':sha256(source_root/'prepared.json')},
      'tools_ref':{'path':str(tools_root),'sha256':sha256(tools_root/'prepared.json')},'policy':policy,'environment':env,
      'options':options,'commands':[],'outputs':None,'passed':False,'shader_compilation_performed':False,'gpu_or_guest_execution_performed':False,'runtime_eligible':False}
    try:
        for ident,argv in recipe.items():monitored_command(root,ident,argv,env,policy,value['commands'])
        value['outputs']=inspect_llvm(root);value['passed']=True;write_new(root/'build.json',value)
        return value
    except (Error,OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        value['passed']=False
        value['error']=error.code if isinstance(error,Error) else 'native_build_failed';write_new(root/'failed.json',value);raise


def verify_llvm(root,repo=REPO):
    root=owned_directory(root,repo);need(not(root/'failed.json').exists(),'failed_native_build')
    value=load_json(root/'build.json')
    fields(value,['schema_version','record_kind','scope','producers','source_ref','tools_ref','policy','environment','options','commands',
                  'outputs','passed','shader_compilation_performed','gpu_or_guest_execution_performed','runtime_eligible'],'dxmt_llvm_native_build')
    need(value['scope']=='dxmt_component' and value['passed'] is True and value['shader_compilation_performed'] is False
         and value['gpu_or_guest_execution_performed'] is False and value['runtime_eligible'] is False,'llvm_build_scope')
    need(value['producers']==producers(repo),'native_build_producer_changed')
    source_root=owned_directory(value['source_ref']['path'],repo);source=verify_source(source_root,repo)
    tools_root=owned_directory(value['tools_ref']['path'],repo);tool_record=tools.verify_tools(tools_root,repo)
    need(sha256(source_root/'prepared.json')==value['source_ref']['sha256'] and sha256(tools_root/'prepared.json')==value['tools_ref']['sha256'],'native_build_input_changed')
    policy=value['policy'];need(policy==storage_policy(policy['jobs'],policy['growth_ceiling_bytes'],policy['reserve_free_bytes']),'native_build_policy')
    recipe,options=llvm_recipe(root,source_root,tools_root,tool_record,policy['jobs'])
    need(value['options']==options,'native_options_changed')
    env=native_environment(root,tools_root,tool_record)
    need(value['environment']==env,'native_environment_changed')
    verify_native_commands(root,value['commands'],recipe,env,policy)
    need(value['outputs']==inspect_llvm(root),'native_llvm_outputs_changed')
    return value


def verify_native_commands(root,commands,recipe,env,policy):
    need(len(commands)==len(recipe) and [r.get('id') for r in commands]==list(recipe),'native_command_set')
    for row in commands:
        fields(row,['id','argv','cwd','environment','exit_code','elapsed_ms','stop_reason','growth_bytes_observed','logs'])
        need(row['argv']==recipe[row['id']] and row['cwd']==str(root) and row['environment']==env and type(row['exit_code']) is int and row['exit_code']==0
             and row['stop_reason'] is None and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0
             and type(row['growth_bytes_observed']) is int and 0<=row['growth_bytes_observed']<=policy['growth_ceiling_bytes'],'native_command_recipe')
        fields(row['logs'],['stdout','stderr'])
        for stream,ref in row['logs'].items():
            fields(ref,['path','sha256','size_bytes']);need(ref['path']=='logs/'+row['id']+'/'+stream,'native_log_path')
            raw=read_relative(root,ref['path'],32*1024**2)
            need(digest(raw)==ref['sha256'] and len(raw)==ref['size_bytes'],'native_log_changed')




def copy_dxmt(prepared,root):
    record=verify_prepared(prepared)
    source=Path(prepared)/'source/dxmt'
    shutil.copytree(source,root/'source')
    need(tools.files(source)==tools.files(root/'source'),'shader_source_copy_changed')
    return record


def xcrun_wrapper(selected):
    import shlex
    return ('#!/bin/sh\nset -eu\n'
      'test "$#" -ge 3 || exit 64\n'
      'test "$1" = "-sdk" && test "$2" = "macosx" || exit 64\n'
      'shift 2\ncase "$1" in\n'
      'metal) shift; exec /usr/bin/arch -arm64 '+shlex.quote(selected['metal']['path'])+' "$@";;\n'
      'metallib) shift; exec /usr/bin/arch -arm64 '+shlex.quote(selected['metallib']['path'])+' "$@";;\n'
      '*) exit 64;;\nesac\n').encode()


def meson_native_file(tool_record):
    native=tool_record['native_tools'];sdk=tool_record['sdk']['path']
    text='[binaries]\n'
    for name,key in [('c','clang'),('cpp','clang++')]:
        text+=name+' = '+repr(['/usr/bin/arch','-arm64',native[key]['path']])+'\n'
    text+='pkg-config = \'/usr/bin/false\'\n\n[built-in options]\n'
    for name in ['c_args','cpp_args','c_link_args','cpp_link_args']:
        text+=name+' = '+repr(['-arch','arm64','-isysroot',sdk,'-mmacosx-version-min=14.0'])+'\n'
    return text.encode()


def shader_build_recipe(root,tools_root,tool_record,llvm_root,capabilities,jobs):
    meson=['/usr/bin/arch','-arm64',tool_record['native_tools']['python']['path'],'-B',str(tools_root/'meson-source/meson.py')]
    selected=capabilities['selected']
    return {'airconv.configure':[*meson,'setup',str(root/'objects'),str(root/'source'),'--native-file',str(root/'native.ini'),
              '--buildtype','release','--backend','ninja','--wrap-mode','nodownload','-Dnative_llvm_path='+str(llvm_root/'install'),
              '-Dbuild_airconv_for_windows=false','-Denable_tests=false','-Denable_nvapi=false','-Denable_nvngx=false','-Denable_d3d12=false'],
            'airconv.compile':[*meson,'compile','-C',str(root/'objects'),'airconv:executable','airconv:static_library','--jobs',str(jobs)],
            'builtin.metal':['/usr/bin/arch','-arm64',selected['metal']['path'],'-o',str(root/'shaders/dxmt_command.air'),'-c',str(root/'source/src/dxmt/dxmt_command.metal')],
            'builtin.metallib':['/usr/bin/arch','-arm64',selected['metallib']['path'],'-o',str(root/'shaders/dxmt_command.metallib'),str(root/'shaders/dxmt_command.air')],
            'builtin.header':['/usr/bin/arch','-arm64',tool_record['native_tools']['xxd']['path'],'-n','dxmt_command','-i',str(root/'shaders/dxmt_command.metallib'),str(root/'shaders/dxmt_command.h')]}




def verify_embedded_header(content,payload,name):
    """Bind xxd-generated bytes and declared length to the actual AIR/metallib."""
    need(len(content)<=16*1024**2,'embedded_header_bound')
    match=re.fullmatch(rb'\s*unsigned char '+name.encode()+rb'\[\] = \{(.*?)\};\s*unsigned int '+name.encode()+rb'_len = ([0-9]+);\s*',content,re.S)
    need(match is not None,'embedded_header_shape')
    body=match[1];tokens=re.findall(rb'0x([0-9a-fA-F]{2})',body)
    residue=re.sub(rb'0x[0-9a-fA-F]{2}|[\s,]',b'',body)
    need(not residue and bytes(int(v,16) for v in tokens)==payload and int(match[2])==len(payload),'embedded_header_payload')

def inspect_rooted_macho(root,path):
    """Parse and hash one owned regular descriptor, without following aliases."""
    fd=open_relative(root,path.relative_to(root).as_posix())
    try:
        before=os.fstat(fd)
        need(before.st_size<=128*1024**2,'native_artifact_size')
        # The retained reader only reads this descriptor's stat/bytes. Keeping it
        # open avoids reopening a mutable original parent chain during parsing.
        info=tools.readers().inspect_macho(Path('/dev/fd')/str(fd))
        with os.fdopen(os.dup(fd),'rb') as stream:
            stream.seek(0);content=stream.read(128*1024**2+1)
        after=os.fstat(fd)
        identity=lambda fact:(fact.st_dev,fact.st_ino,fact.st_mode,fact.st_size,fact.st_mtime_ns,fact.st_ctime_ns)
        need(len(content)==before.st_size and identity(before)==identity(after),'native_artifact_changed')
        return {'sha256':digest(content),**info}
    finally:os.close(fd)


def shader_failure_observation(root,commands):
    """Distinguish invoked parent recipes from observed Metal compilation."""
    attempted=[{'id':row['id'],'exit_code':row['exit_code'],'stop_reason':row['stop_reason']}
               for row in commands if row['id'] in ['airconv.compile','builtin.metal']]
    outputs=[]
    # A successful Meson invocation does not itself prove which child ran. Only
    # a successful direct Metal compile with bounded AIR bytes establishes this
    # observation on a failed pipeline; complete builds have full output proof.
    if any(row['id']=='builtin.metal' and type(row['exit_code']) is int and row['exit_code']==0 and row['stop_reason'] is None for row in attempted):
        try:
            content=read_relative(root,'shaders/dxmt_command.air',16*1024**2)
            if len(content)>32 and content[:4] in [b'BC\xc0\xde',b'\xde\xc0\x17\x0b']:
                outputs.append({'path':'shaders/dxmt_command.air','sha256':digest(content),'size_bytes':len(content),'kind':'air'})
        except (Error,OSError):pass
    status='observed' if outputs else 'attempted_unverified' if attempted else 'unperformed'
    return {'status':status,'parent_commands_attempted':attempted,'observed_air_outputs':outputs}


def inspect_shader_build(root):
    from check import shader_output
    outputs=[]
    for name in ['air_msad','air_samplepos','air_tessellation']:
        candidates=list((root/'objects').rglob(name+'.air'))
        need(len(candidates)==2,'airconv_shader_output_closure')
        # Executable and static library generators are separate upstream targets.
        for path in sorted(candidates):
            fact=shader_output(path,'air');fact['path']=path.relative_to(root).as_posix();outputs.append(fact)
            header=path.with_suffix('.h');content=read_relative(root,header.relative_to(root).as_posix(),16*1024**2)
            verify_embedded_header(content,read_relative(root,path.relative_to(root).as_posix(),16*1024**2),name)
            outputs.append({'path':header.relative_to(root).as_posix(),'sha256':digest(content),'size_bytes':len(content),'kind':'embedded_header'})
    for name,kind in [('dxmt_command.air','air'),('dxmt_command.metallib','metallib')]:
        fact=shader_output(root/'shaders'/name,kind);fact['path']='shaders/'+name;outputs.append(fact)
    header=root/'shaders/dxmt_command.h';content=read_relative(root,'shaders/dxmt_command.h',16*1024**2)
    verify_embedded_header(content,read_relative(root,'shaders/dxmt_command.metallib',16*1024**2),'dxmt_command')
    outputs.append({'path':'shaders/dxmt_command.h','sha256':digest(content),'size_bytes':len(content),'kind':'embedded_header'})
    exe=root/'objects/src/airconv/darwin/airconv';lib=root/'objects/src/airconv/darwin/libairconv.a'
    parser=root/'objects/libs/DXBCParser/libDXBCParserNative.a'
    need(exe.is_file() and lib.is_file(),'airconv_artifacts_missing')
    need(parser.is_file() and not parser.is_symlink(),'airconv_native_parser_missing')
    # The pinned native airconv targets both link this separate upstream archive.
    # Its members must remain bound even when the executable has absorbed them.
    parser_info=inspect_native_archive(parser,root=root)
    info=inspect_rooted_macho(root,exe)
    need(info['architectures']==[MACH_ARM64] and info['filetype']==2 and all(d.startswith(('/usr/lib/','/System/Library/')) for d in info['dependencies']),'airconv_native_dependencies')
    return {'airconv_executable':{'path':exe.relative_to(root).as_posix(),**info},
            'airconv_static_library':{'path':lib.relative_to(root).as_posix(),**inspect_native_archive(lib,root=root)},
            'dxbc_parser_native_library':{'path':parser.relative_to(root).as_posix(),**parser_info},
            'shader_outputs':outputs,'airconv_execution':'unperformed','gpu_execution':'unperformed'}


def build_shaders(llvm_path,prepared_path,tools_path,capabilities_path,output,jobs,cap,reserve,repo=REPO):
    from check import verify_shader_capabilities
    llvm_root=owned_directory(llvm_path,repo);llvm=verify_llvm(llvm_root,repo)
    tools_root=owned_directory(tools_path,repo);tool_record=tools.verify_tools(tools_root,repo)
    cap_root=owned_directory(capabilities_path,repo);capability=verify_shader_capabilities(cap_root,repo)
    need(capability['shader_build_ready'] is True,'shader_tools_unavailable')
    need(llvm['tools_ref']==capability['tools_ref']=={'path':str(tools_root),'sha256':sha256(tools_root/'prepared.json')},'shader_tools_pairing')
    prepared_root=owned_directory(prepared_path,repo);prepared=verify_prepared(prepared_root,repo)
    source=verify_source(llvm['source_ref']['path'],repo)
    need(source['prepared_ref']=={'path':str(prepared_root),'sha256':sha256(prepared_root/'prepared.json')},'shader_source_pairing')
    policy=storage_policy(jobs,cap,reserve);need(shutil.disk_usage(llvm_root).free>=cap+reserve,'shader_start_space_below_ceiling_and_reserve')
    root=output_directory(output,repo)
    env=native_environment(root,tools_root,tool_record);env['PATH']=str(root/'bin')+':'+env['PATH']
    value={'schema_version':1,'record_kind':'dxmt_native_shader_build','scope':'dxmt_component','producers':producers(repo),
           'llvm_ref':{'path':str(llvm_root),'sha256':sha256(llvm_root/'build.json')},'prepared_ref':source['prepared_ref'],
           'tools_ref':capability['tools_ref'],'capabilities_ref':{'path':str(cap_root),'sha256':sha256(cap_root/'capabilities.json')},
           'policy':policy,'environment':env,'commands':[],'generated_inputs':[],
           'outputs':None,'passed':False,'shader_compilation_performed':False,'stage2_complete':False,
           'gpu_or_guest_execution_performed':False,'runtime_eligible':False}
    try:
        copy_dxmt(prepared_root,root)
        (root/'tmp').mkdir();(root/'bin').mkdir()
        (root/'bin/xcrun').write_bytes(xcrun_wrapper(capability['selected']));(root/'bin/xcrun').chmod(0o755)
        (root/'native.ini').write_bytes(meson_native_file(tool_record));(root/'shaders').mkdir()
        value['generated_inputs']=[{'path':'native.ini','sha256':sha256(root/'native.ini'),'mode':0o644},
                                   {'path':'bin/xcrun','sha256':sha256(root/'bin/xcrun'),'mode':0o755}]
        recipe=shader_build_recipe(root,tools_root,tool_record,llvm_root,capability,jobs)
        for ident,argv in recipe.items():monitored_command(root,ident,argv,env,policy,value['commands'])
        value['outputs']=inspect_shader_build(root);value['passed']=True;value['stage2_complete']=True
        value['shader_compilation_performed']=True
        write_new(root/'build.json',value);return value
    except (Error,OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        value['passed']=False;value['stage2_complete']=False
        observation=shader_failure_observation(root,value['commands'])
        value['shader_compilation_observation']=observation
        value['shader_compilation_performed']={'unperformed':False,'attempted_unverified':None,'observed':True}[observation['status']]
        value['error']=error.code if isinstance(error,Error) else 'shader_build_failed';write_new(root/'failed.json',value);raise


def verify_shader_build(root,repo=REPO):
    from check import verify_shader_capabilities
    root=owned_directory(root,repo);need(not(root/'failed.json').exists(),'failed_shader_build')
    value=load_json(root/'build.json')
    fields(value,['schema_version','record_kind','scope','producers','llvm_ref','prepared_ref','tools_ref','capabilities_ref','policy','environment',
                 'commands','generated_inputs','outputs','passed','shader_compilation_performed','stage2_complete','gpu_or_guest_execution_performed','runtime_eligible'],'dxmt_native_shader_build')
    need(value['scope']=='dxmt_component' and value['passed'] is True and value['shader_compilation_performed'] is True
         and value['stage2_complete'] is True and value['gpu_or_guest_execution_performed'] is False and value['runtime_eligible'] is False,'native_shader_scope')
    need(value['producers']==producers(repo),'native_shader_producer_changed')
    llvm_root=owned_directory(value['llvm_ref']['path'],repo);llvm=verify_llvm(llvm_root,repo)
    tools_root=owned_directory(value['tools_ref']['path'],repo);tool_record=tools.verify_tools(tools_root,repo)
    cap_root=owned_directory(value['capabilities_ref']['path'],repo);capability=verify_shader_capabilities(cap_root,repo)
    need(capability['shader_build_ready'] is True and llvm['tools_ref']==capability['tools_ref']==value['tools_ref'],'native_shader_tools_pairing')
    need(sha256(llvm_root/'build.json')==value['llvm_ref']['sha256'] and sha256(tools_root/'prepared.json')==value['tools_ref']['sha256']
         and sha256(cap_root/'capabilities.json')==value['capabilities_ref']['sha256'],'native_shader_reference_changed')
    prepared=verify_prepared(value['prepared_ref']['path'],repo);need(sha256(Path(value['prepared_ref']['path'])/'prepared.json')==value['prepared_ref']['sha256'],'native_shader_source_changed')
    need(verify_source(llvm['source_ref']['path'],repo)['prepared_ref']==value['prepared_ref'],'native_shader_source_pairing')
    need(tools.files(Path(value['prepared_ref']['path'])/'source/dxmt')==tools.files(root/'source'),'native_shader_source_copy_changed')
    policy=value['policy'];need(policy==storage_policy(policy['jobs'],policy['growth_ceiling_bytes'],policy['reserve_free_bytes']),'native_shader_policy')
    expected={'native.ini':meson_native_file(tool_record),'bin/xcrun':xcrun_wrapper(capability['selected'])}
    need(len(value['generated_inputs'])==2 and {r.get('path') for r in value['generated_inputs']}==set(expected),'native_generated_closure')
    for row in value['generated_inputs']:
        fields(row,['path','sha256','mode']);content=read_relative(root,row['path'])
        need(content==expected[row['path']] and digest(content)==row['sha256'] and row['mode']==(0o755 if row['path']=='bin/xcrun' else 0o644)
             and (root/row['path']).stat().st_mode&0o777==row['mode'],'native_generated_changed')
    env=native_environment(root,tools_root,tool_record);env['PATH']=str(root/'bin')+':'+env['PATH']
    need(value['environment']==env,'native_shader_environment')
    recipe=shader_build_recipe(root,tools_root,tool_record,llvm_root,capability,policy['jobs'])
    verify_native_commands(root,value['commands'],recipe,env,policy)
    need(value['outputs']==inspect_shader_build(root),'native_shader_outputs_changed')
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='operation',required=True)
    prepare=sub.add_parser('prepare')
    for key in ['inputs','prepared','source-cache','output']:prepare.add_argument('--'+key,required=True)
    prepare.add_argument('--require-empty',action='store_true',required=True)
    llvm=sub.add_parser('llvm')
    for key in ['source','tools','output']:llvm.add_argument('--'+key,required=True)
    for key in ['jobs','max-growth-bytes','reserve-free-bytes']:llvm.add_argument('--'+key,required=True,type=int)
    llvm.add_argument('--require-empty',action='store_true',required=True)
    verify=sub.add_parser('verify-llvm');verify.add_argument('--root',required=True)
    shader=sub.add_parser('shaders')
    for key in ['llvm','prepared','tools','capabilities','output']:shader.add_argument('--'+key,required=True)
    for key in ['jobs','max-growth-bytes','reserve-free-bytes']:shader.add_argument('--'+key,required=True,type=int)
    shader.add_argument('--require-empty',action='store_true',required=True)
    verify_shader=sub.add_parser('verify-shaders');verify_shader.add_argument('--root',required=True)
    args=parser.parse_args()
    try:
        if args.operation=='prepare':
            value=prepare_source(args.inputs,args.prepared,args.source_cache,args.output)
            result={'source_prepared':True,'selected_source_bytes':value['measured_source_bytes'],'compilation_performed':False,'runtime_eligible':False}
        elif args.operation in ['shaders','verify-shaders']:
            value=build_shaders(args.llvm,args.prepared,args.tools,args.capabilities,args.output,args.jobs,args.max_growth_bytes,args.reserve_free_bytes) if args.operation=='shaders' else verify_shader_build(args.root)
            result={'llvm_native_prerequisites':True,'shader_compilation_performed':True,'stage2_complete':value['stage2_complete'],'runtime_eligible':False}
        else:
            value=build_llvm(args.source,args.tools,args.output,args.jobs,args.max_growth_bytes,args.reserve_free_bytes) if args.operation=='llvm' else verify_llvm(args.root)
            result={'llvm_native_prerequisites':value['passed'],'shader_compilation_performed':False,'runtime_eligible':False}
        print(encoded(result).decode(),end='');return 0
    except (Error,OSError,ValueError,KeyError,UnicodeError,subprocess.SubprocessError) as error:
        print(encoded({'passed':False,'error':error.code if isinstance(error,Error) else 'native_operation_failed','runtime_eligible':False}).decode(),end='');return 1

if __name__=='__main__':sys.exit(main())
