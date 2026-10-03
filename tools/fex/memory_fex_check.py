"""Private independent full-FEX build replay proposal; never initializes FEX.

Original Pear layer over unchanged pinned source/build/PE/archive readers. This
private draft is not installed, distribution-qualified or a Stage 3 completion.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import os
from pathlib import Path
import re
import shlex
import stat
import struct
import sys
import types

if __package__:
    from . import build as original, memory_wine_build as wine_owner, prepare, byte_readers, check
    from .common import Error, REPO, need, read_relative, relative, open_relative, decode_json, load_json, sha256, encoded, operation_output
else:
    # The sibling tools.py is a module, so remove this executable directory
    # before importing the repository's top-level tools namespace.
    script_directory=Path(__file__).resolve().parent
    sys.path[:]=[entry for entry in sys.path if Path(entry or os.getcwd()).resolve()!=script_directory]
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from tools.fex import build as original, memory_wine_build as wine_owner, prepare, byte_readers, check
    from tools.fex.common import Error, REPO, need, read_relative, relative, open_relative, decode_json, load_json, sha256, encoded, operation_output

BASE_BUILD_SHA='0a2c854c0c42484ace9c077b8fb69a73b6e8a323d0b2a8b5e7c8cead90fb21ed'
BASE_SOURCE_SHA='d7cf7fa57fe69b1f59d808a385d5900d2ffe565d6fda472f1a6264c3751dadff'
GRAPH_SHA='6fe637dcd7f952836bbb3653b128f2016c8df26c942fc3a30b4440cd1c1cdcf1'
MAX_FILES=12000
MAX_SOURCE_BYTES=128*1024**2
MAX_SOURCE_FILE=8*1024**2
H=lambda raw:hashlib.sha256(raw).hexdigest()


def exact(value,keys,code):
    need(type(value) is dict and set(value)==set(keys),code)


def regular_bytes(root,path,limit,*,system_git=False):
    """FD-anchored current bytes, exact mode and hardlink/size identity."""
    with os.fdopen(open_relative(root,path),'rb') as stream:
        before=os.fstat(stream.fileno())
        need((not system_git or Path(root)==Path('/usr/bin') and path=='git') and
             stat.S_ISREG(before.st_mode) and (before.st_nlink==1 or system_git) and before.st_size<=limit,
             'fex_memory_source_file_kind')
        raw=stream.read(limit+1);after=os.fstat(stream.fileno())
        need(len(raw)==before.st_size and len(raw)<=limit and
             (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
             (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),
             'fex_memory_source_file_changed')
        return raw,stat.S_IMODE(before.st_mode)


def source_inventory(root):
    root=Path(root).absolute();need(root.resolve(strict=True)==root and root.is_dir(),
                                  'fex_memory_source_root_alias')
    device=root.stat().st_dev;rows=[];total=0;directories=0;cases=set()
    for directory,dirs,names in os.walk(root,followlinks=False):
        directories+=1;need(directories<=MAX_FILES,'fex_memory_source_directory_limit')
        dirs.sort();names.sort()
        for name in dirs+names:
            child=Path(directory)/name;info=child.lstat()
            entry=child.relative_to(root).as_posix();relative(entry)
            need(entry.casefold() not in cases,'fex_memory_source_case_alias');cases.add(entry.casefold())
            need(info.st_dev==device and not stat.S_ISLNK(info.st_mode),
                 'fex_memory_source_mount_or_link')
            need(stat.S_ISDIR(info.st_mode) if name in dirs else stat.S_ISREG(info.st_mode),
                 'fex_memory_source_special_file')
        for name in names:
            child=Path(directory)/name;path=child.relative_to(root).as_posix();relative(path)
            raw,mode=regular_bytes(root,path,MAX_SOURCE_FILE)
            need(mode in (0o644,0o755),'fex_memory_source_file_mode')
            total+=len(raw);need(total<=MAX_SOURCE_BYTES and len(rows)<MAX_FILES,'fex_memory_source_limit')
            rows.append({'path':path,'sha256':H(raw),'size_bytes':len(raw),'mode':mode})
    return sorted(rows,key=lambda row:row['path'])


def change_rows(rows):
    need(type(rows) is list and 0<len(rows)<=64,'fex_memory_change_rows')
    seen=set()
    for row in rows:
        exact(row,('path','preimage_sha256','postimage_sha256','postimage_bytes'),
              'fex_memory_change_fields')
        path=row['path'];relative(path);need(path not in seen,'fex_memory_duplicate_change');seen.add(path)
        need(row['preimage_sha256'] is None or type(row['preimage_sha256']) is str and
             re.fullmatch('[0-9a-f]{64}',row['preimage_sha256']),'fex_memory_preimage_digest')
        need(type(row['postimage_sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['postimage_sha256'])
             and type(row['postimage_bytes']) is int and 0<row['postimage_bytes']<=MAX_SOURCE_FILE,
             'fex_memory_postimage_fields')
    return {row['path']:row for row in rows}


def render_declared_git(strict,rows):
    """Exact additive metadata only; no permissive metadata deletion."""
    need(type(strict) is bytes and len(strict)<=2*1024**2,'fex_memory_strict_patch_size')
    by_path=change_rows(rows);sections=original.patch_sections(strict)
    need(set(sections)==set(by_path),'fex_memory_patch_path_closure')
    restored=bytearray();git=bytearray()
    for path,lines in sections.items():
        need(lines[:2]==['--- '+('/dev/null' if by_path[path]['preimage_sha256'] is None else 'a/'+path)+'\n',
                        '+++ b/'+path+'\n'],'fex_memory_patch_headers')
        header=('diff --git a/'+path+' b/'+path+'\n').encode();body=''.join(lines).encode()
        restored.extend(header+body);git.extend(header)
        if by_path[path]['preimage_sha256'] is None:git.extend(b'new file mode 100644\n')
        git.extend(body)
    need(bytes(restored)==strict,'fex_memory_strict_patch_roundtrip')
    return bytes(git)


def graph_input(root,reference,limit):
    """Read one exact root-relative graph artifact; never load Python code."""
    exact(reference,('path','sha256','size_bytes'),'fex_memory_graph_reference_fields')
    parts=relative(reference['path'])
    need(type(reference['sha256']) is str and re.fullmatch('[0-9a-f]{64}',reference['sha256'])
         and type(reference['size_bytes']) is int and 0<reference['size_bytes']<=limit,
         'fex_memory_graph_reference')
    root=Path(root)
    need(root.is_absolute() and root.resolve(strict=True)==root,'fex_memory_graph_root_alias')
    raw,mode=regular_bytes(root,'/'.join(parts),limit)
    need(mode==0o644 and len(raw)==reference['size_bytes'] and H(raw)==reference['sha256'],
         'fex_memory_graph_reference_changed')
    return raw


def graph_path(root,reference,limit):
    graph_input(root,reference,limit)
    return Path(root).joinpath(*relative(reference['path']))


def publication_series_gate(derivatives,graph):
    raw=graph_input(derivatives,graph['publication_series'],2*1024**2)
    series=decode_json(raw,max_bytes=2*1024**2)
    exact(series,('schema_version','component','runtime_execution','baseline','authoritative_header',
          'patches','preserved_abi','source_gates','source_graph'),'fex_memory_publication_series_fields')
    exact(series['source_gates'],('paired_module_identity','fex_initialization','guest_execution','raw_signal_handoff',
          'source_entry_reservation','general_source_lifetime','atomic_core_resume','aggregate_metadata','stage3_complete'),
          'fex_memory_publication_series_gate_fields')
    need(series['schema_version']==1 and series['component']=='fex-memory-source-supplements'
         and series['runtime_execution'] is False and series['baseline']['qualified_source_files_sha256']==BASE_SOURCE_SHA
         and series['authoritative_header']=={'path':'include/wine/pear_fex_memory.h','sha256':WIRE_SHA,
             'build_relative_path':'wine/pear_fex_memory.h','source_component':'wine-fex-memory'}
         and series['preserved_abi']=={'fex_unixlib_services':8,'wire_record_bytes':128,'ntdll_unix_index':10,'wire_version':2}
         and all(value is False for value in series['source_gates'].values()),'fex_memory_publication_series_scope')
    expected=[]
    for layer in graph['layers']:
        expected.append({'file':'memory/source-graph/'+layer['strict_patch']['path'],'sha256':layer['strict_patch']['sha256'],
            'git_file':'memory/source-graph/'+layer['git_derivative']['path'],'git_sha256':layer['git_derivative']['sha256'],
            'order':layer['order'],'name':layer['name'],'license':'MIT (FEX source and original Pear additions); existing notices retained',
            'provenance_manifest':'memory/source-graph/'+layer['source_manifest']['path'],
            'provenance_sha256':layer['source_manifest']['sha256'],'sources':layer['changes']})
    need(series['patches']==expected and series['source_graph']=={'file':'memory/source-graph/derivatives.json',
         'layer_count':14,'reference_scope':'derivatives_root_relative_v1'},'fex_memory_publication_series_graph')
    return series


def selected_projection(baseline,derivatives):
    """Pure current-byte closure; caller separately admits old full build proof."""
    baseline=Path(baseline);derivatives=Path(derivatives)
    build_raw,_=regular_bytes(baseline,'build.json',8*1024**2)
    manifest_raw,_=regular_bytes(baseline,'materialized-source.json',8*1024**2)
    need(H(build_raw)==BASE_BUILD_SHA and H(manifest_raw)==BASE_SOURCE_SHA,'fex_memory_baseline_identity')
    source_record=decode_json(manifest_raw,max_bytes=8*1024**2)
    exact(source_record,('schema_version','record_kind','scope','files'),'fex_memory_baseline_source_fields')
    need(source_record['record_kind']=='fex_materialized_source' and source_record['scope']=='fex_component'
         and type(source_record['schema_version']) is int and source_record['schema_version']==1,
         'fex_memory_baseline_source_scope')
    original_rows=source_inventory(baseline/'source')
    need(original_rows==source_record['files'],'fex_memory_baseline_source_changed')
    raw,_=regular_bytes(derivatives,'derivatives.json',8*1024**2)
    need(H(raw)==GRAPH_SHA,'fex_memory_selected_graph_changed')
    graph=decode_json(raw,max_bytes=8*1024**2)
    need(len(graph['layers'])==14 and graph['reference_scope']=='derivatives_root_relative_v1' and graph['wire_version']==2
         and all(graph[key] is False for key in
         ('git_execution_performed','compilation_performed','module_initialization_performed',
          'owner_execution_performed','stage3_complete')),'fex_memory_graph_scope')
    publication_series_gate(derivatives,graph)
    rows={row['path']:dict(row) for row in original_rows};changed={};retained=[]
    for order,layer in enumerate(graph['layers'],1):
        need(type(layer['order']) is int and layer['order']==order,'fex_memory_layer_order')
        rows_by_path=change_rows(layer['changes'])
        strict=graph_input(derivatives,layer['strict_patch'],2*1024**2)
        metadata=graph_input(derivatives,layer['source_manifest'],2*1024**2)
        record=decode_json(metadata,max_bytes=2*1024**2)
        need(record['record_kind']=='fex_memory_source_layer' and record['scope']=='source_only'
             and record['order']==order and record['name']==layer['name'] and record['files']==layer['changes']
             and record['historical_strict_patch_sha256']==layer['strict_patch']['sha256']
             and all(record[key] is False for key in ('compilation_performed','native_runtime_execution','fex_initialization','stage3_complete')),
             'fex_memory_public_source_layer')
        git=graph_input(derivatives,layer['git_derivative'],2*1024**2)
        need(layer['metadata_normalization']=='exact_declared_null_preimage_new_file_mode_100644_v1'
             and git==render_declared_git(strict,layer['changes']),'fex_memory_git_derivative_changed')
        sections=original.patch_sections(strict)
        for path,row in rows_by_path.items():
            prior=rows.get(path)
            before=changed[path] if path in changed else regular_bytes(baseline/'source',path,MAX_SOURCE_FILE)[0] if prior else None
            need((H(before) if before is not None else None)==row['preimage_sha256'],'fex_memory_patch_preimage')
            after=original.apply_hunks(before,sections[path],path)
            need(H(after)==row['postimage_sha256'] and len(after)==row['postimage_bytes'],'fex_memory_patch_postimage')
            changed[path]=after;rows[path]={'path':path,'sha256':H(after),'size_bytes':len(after),'mode':prior['mode'] if prior else 0o644}
        for item in graph['retained_source_observations']:
            if item['layer']!=order:continue
            path=item['path'];current=changed[path] if path in changed else regular_bytes(baseline/'source',path,MAX_SOURCE_FILE)[0]
            need(H(current)==item['sha256'],'fex_memory_layer_retained_source');retained.append(item)
    final=sorted(rows.values(),key=lambda row:row['path'])
    need(len(final)<=MAX_FILES and sum(row['size_bytes'] for row in final)<=MAX_SOURCE_BYTES,'fex_memory_final_source_bounds')
    need([{**rows[path]} for path in sorted(changed)]==graph['final_changed_source_rows'],'fex_memory_final_changed_rows')
    return {'scope':'source_only','source_files':final,'changed_bytes':changed,'layer_count':14,
        'retained_layer_rows':retained,'graph_sha256':H(raw),'source_initialization':False,'stage3_complete':False}


PROJECTION_MANIFEST_SHA='abd8987ac5027540dcdc4c04059f9394b248224deb61abc89d6318d310081495'
SOURCE_HELPER_SHA='be606e51e6031298cfa35b9eb5588c45233eff8aa481d5fa1842ad20d34a785e'
WIRE_SHA='bee4d7f58bb796f7b86f85e5bf3d3dc9100a9df51789f0522762c6846d9ad1cf'
FALSE_FLAGS=('source_runtime_qualified','metadata_qualified','fex_initialization','jit_execution',
             'module_loading','pe_execution','owner_execution','arm64ec_role_qualified',
             'raw_signal_handoff_qualified','guest_execution','runtime_qualified',
             'game_qualified','distribution_qualified','stage3_complete')
MAX_LOG=64*1024**2
QUALIFICATION={'source_runtime':'unperformed','aggregate_metadata':'unperformed',
               'active_thread_bridge':'unperformed','atomic_resume':'unperformed',
               'delivered_exception':'unperformed','paired_arm64ec_identity':'unperformed'}
LOCAL_PRODUCERS=('tools/fex/memory_fex_build.py','tools/fex/memory_fex_check.py',
                 'tools/fex/memory_wine_build.py','tools/fex/prepare.py','tools/fex/tools.py',
                 'tools/fex/build.py','tools/fex/check.py','tools/fex/common.py','tools/fex/byte_readers.py',
                 'tools/wine/common.py','tools/wine/toolchain.py','tools/wine/build.py','tools/wine/prepare.py',
                 'tools/sources/validate_inventory.py')


def record_bytes(root,path,limit=8*1024**2):
    raw,_=regular_bytes(root,path,limit)
    return decode_json(raw,max_bytes=limit),raw


def source_helper_reference(value):
    """Read the pinned proposal helper as data only, through owned descriptors.

    The required input may move without changing its historical byte identity.
    It is never imported, interpreted or executed by this component builder.
    """
    raw_path=os.fspath(value)
    need(type(raw_path) is str and raw_path.startswith('/') and not raw_path.startswith('//'),
         'fex_memory_source_helper_absolute')
    relative(raw_path[1:])
    path=Path(raw_path)
    need(str(path)==raw_path and path.resolve(strict=True)==path,
         'fex_memory_source_helper_path_alias')
    raw,mode=regular_bytes(Path('/'),raw_path[1:],1024**2)
    need(H(raw)==SOURCE_HELPER_SHA and mode==0o644,'fex_memory_source_helper_changed')
    return {'path':raw_path,'sha256':H(raw),'size_bytes':len(raw),'mode':mode}


def bound_source_helper(reference):
    """Recover the required replay input from its exact receipt reference."""
    exact(reference,('path','sha256','size_bytes','mode'),'fex_memory_source_helper_fields')
    need(type(reference['path']) is str and reference['sha256']==SOURCE_HELPER_SHA
         and type(reference['size_bytes']) is int and 0<reference['size_bytes']<=1024**2
         and type(reference['mode']) is int and reference['mode']==0o644,
         'fex_memory_source_helper_reference')
    need(source_helper_reference(reference['path'])==reference,'fex_memory_source_helper_binding')
    return Path(reference['path'])


def projection_gate(projection,baseline,derivatives,*,source_helper,expected_control_sha256=None):
    """Admit current genuine Git evidence, or replay one immutably bound record."""
    projection=Path(projection);derived=selected_projection(baseline,derivatives)
    value,control_raw=record_bytes(projection,'control.json')
    control_sha256=H(control_raw)
    if expected_control_sha256 is not None:
        need(type(expected_control_sha256) is str and re.fullmatch('[0-9a-f]{64}',expected_control_sha256)
             and control_sha256==expected_control_sha256,'fex_memory_projection_control_changed')
    exact(value,('schema_version','record_kind','scope','passed','git_execution_performed',
          'compilation_performed','module_initialization_performed','owner_execution_performed',
          'guest_execution_performed','stage3_complete','layers','changed_paths','new_files',
          'inputs','git','commands','baseline_unchanged_observed','materialized_source_sha256',
          'source_files','source_bytes'),'fex_memory_projection_control_fields')
    exact(value['inputs'],('baseline_manifest_sha256','derivatives_sha256','expected_manifest_sha256',
          'source_helper_sha256'),'fex_memory_projection_input_fields')
    exact(value['git'],('path','sha256','size_bytes'),'fex_memory_projection_git_fields')
    need(type(value['schema_version']) is int and value['schema_version']==1
         and value['record_kind']=='fex_source_git_application_control' and value['scope']=='source_only'
         and type(value['layers']) is int and type(value['changed_paths']) is int and type(value['new_files']) is int
         and type(value['source_files']) is int and value['source_files']==len(derived['source_files'])
         and type(value['source_bytes']) is int
         and value['source_bytes']==sum(row['size_bytes'] for row in derived['source_files'])
         and value['passed'] is True and value['baseline_unchanged_observed'] is True
         and value['git_execution_performed'] is True and value['layers']==14
         and value['changed_paths']==36 and value['new_files']==12
         and value['inputs']['derivatives_sha256']==GRAPH_SHA
         and value['inputs']['baseline_manifest_sha256']==BASE_SOURCE_SHA,
         'fex_memory_projection_scope')
    need(all(value[name] is False for name in ('compilation_performed','module_initialization_performed',
         'owner_execution_performed','guest_execution_performed','stage3_complete')),
         'fex_memory_projection_overclaim')
    graph,_=record_bytes(derivatives,'derivatives.json')
    helper_ref=source_helper_reference(source_helper)
    normalization=graph_input(derivatives,graph['normalization_helper'],1024**2)
    proposal,proposal_raw=record_bytes(derivatives,'final-source-proposal.json')
    need(helper_ref['sha256']==SOURCE_HELPER_SHA==value['inputs']['source_helper_sha256']
         and H(normalization)==graph['normalization_helper']['sha256']
         and H(proposal_raw)==value['inputs']['expected_manifest_sha256']
         and proposal=={'schema_version':1,'record_kind':'fex_memory_source_proposal','scope':'source_only',
             'baseline_manifest_sha256':BASE_SOURCE_SHA,'derivatives_manifest_sha256':GRAPH_SHA,
             'files':derived['source_files'],'materialization_performed':False,'compilation_performed':False},
         'fex_memory_projection_helper_manifest_changed')
    need(type(value['commands']) is list and len(value['commands'])==28,'fex_memory_git_command_count')
    for index,row in enumerate(value['commands']):
        exact(row,('action','layer','argv','cwd','attempted','exit_code','elapsed_ms',
              'stdout','stdout_bytes','stdout_sha256','stderr','stderr_bytes','stderr_sha256'),
              'fex_memory_git_command_fields')
        action='check' if index%2==0 else 'apply';order=index//2+1
        path=Path(derivatives)/graph['layers'][order-1]['git_derivative']['path']
        expected=['/usr/bin/git','apply',*(['--check'] if action=='check' else []),str(path)]
        need(row['action']==action and type(row['layer']) is int and row['layer']==order
             and row['argv']==expected and row['cwd']==str(projection/'source')
             and row['attempted'] is True and type(row['exit_code']) is int and row['exit_code']==0
             and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0,'fex_memory_git_command')
        for channel in ('stdout','stderr'):
            path=f'{order:02d}-{action}.{channel}'
            need(row[channel]==path and type(row[channel+'_bytes']) is int
                 and 0<=row[channel+'_bytes']<=1024**2,'fex_memory_git_log_path')
            observed,_=regular_bytes(projection,path,1024**2)
            need(len(observed)==row[channel+'_bytes'] and H(observed)==row[channel+'_sha256'],
                 'fex_memory_git_log_changed')
    need(type(value['git']['path']) is str and value['git']['path']=='/usr/bin/git'
         and type(value['git']['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['git']['sha256'])
         and type(value['git']['size_bytes']) is int and 0<value['git']['size_bytes']<=32*1024**2,
         'fex_memory_projection_git_reference')
    path=Path(value['git']['path']);git,_=regular_bytes(path.parent,path.name,32*1024**2,system_git=True)
    need(str(path)=='/usr/bin/git' and len(git)==value['git']['size_bytes']
         and H(git)==value['git']['sha256'],'fex_memory_git_bytes')
    manifest,raw=record_bytes(projection,'materialized-source.json')
    need(H(raw)==PROJECTION_MANIFEST_SHA==value['materialized_source_sha256'],
         'fex_memory_projection_manifest_identity')
    need(manifest=={'schema_version':1,'record_kind':'fex_materialized_source',
         'scope':'fex_component','files':derived['source_files']}
         and source_inventory(projection/'source')==derived['source_files'],
         'fex_memory_projection_source_changed')
    return derived,{'root':str(projection),'control_sha256':control_sha256,
                    'source_manifest_sha256':PROJECTION_MANIFEST_SHA,'source_helper':helper_ref}


def wire_gate(wine_build):
    """Fresh selected build proof; never hardcode a future successful receipt."""
    root=Path(wine_build);value=wine_owner.verify_build(root)
    raw,mode=regular_bytes(root,'source/include/wine/pear_fex_memory.h',65536)
    need(H(raw)==WIRE_SHA and mode==0o644,'fex_memory_authoritative_wire')
    return raw,{'root':str(root),'build_sha256':sha256(root/'build.json'),
                'source_sha256':value['source_manifest_sha256'],
                'path':'source/include/wine/pear_fex_memory.h','sha256':H(raw),'size_bytes':len(raw)}


def recipe(root,tools,lock,features,config,cross):
    result={name:list(argv) for name,argv in original.complete_recipe(
            Path(root),Path(tools),lock,features,config,cross).items()}
    for target in ('arm64ec','wow64'):
        result[target+'.configure'] += ['-DPEAR_FEX_MEMORY_OWNER=ON',
                                        '-DPEAR_FEX_MEMORY_INCLUDE_ROOT='+str(Path(root)/'wire')]
    for target in ('arm64ec','wow64'):
        result[target+'.build'] += ['--','-d','keepdepfile']
    need(len(result)==9,'fex_memory_recipe_count')
    return result


def macro_values(arguments):
    """Reject effective trailing undef/redefine, while admitting same=1 repeats."""
    defines={};undefined=set();i=1
    while i<len(arguments):
        item=arguments[i]
        if item in ('-D','-U'):
            need(i+1<len(arguments),'fex_memory_macro_operand');kind=item;value=arguments[i+1];i+=2
        elif item.startswith(('-D','-U')):kind=item[:2];value=item[2:];i+=1
        else:i+=1;continue
        name,_,setting=value.partition('=')
        if kind=='-U':undefined.add(name)
        else:defines.setdefault(name,[]).append(setting or '1')
    return defines,undefined



FORBIDDEN_HEADER_OPTIONS=('-include','-imacros','-isystem','-iquote','-idirafter','-iprefix',
    '-iwithprefix','-isysroot','--sysroot','-resource-dir','-fmodule-file','-fmodule-map-file',
    '-fprebuilt-module-path','-iframework','-F','-nostdinc')


def include_arguments(arguments):
    result=[];i=1
    while i<len(arguments):
        arg=arguments[i]
        need(not arg.startswith(FORBIDDEN_HEADER_OPTIONS),'fex_memory_unapproved_header_option')
        if arg=='-I':
            need(i+1<len(arguments),'fex_memory_include_operand');result.append(arguments[i+1]);i+=2
        elif arg.startswith('-I'):result.append(arg[2:]);i+=1
        else:i+=1
    need(all(value and Path(value).is_absolute() for value in result),'fex_memory_include_absolute')
    return result


def compile_target(name):
    relative(name);need(name.count('.dir/')==1,'fex_memory_compile_target')
    return name.split('.dir/',1)[0]+'.dir'


def include_policy(baseline,output,source):
    """Source-reviewed existing CMake-target search order plus one wire root."""
    previous=Path(baseline)/'pe'/output.name;policy={}
    for row in original.compile_database(previous):
        roots=include_arguments(shlex.split(row['command']))
        rebased=[]
        for root in roots:
            if root.startswith(str(Path(baseline)/'source')+'/'):
                value=str(source)+root[len(str(Path(baseline)/'source')):]
            elif root.startswith(str(previous)+'/'):
                value=str(output)+root[len(str(previous)):]
            else:raise Error('fex_memory_baseline_foreign_include')
            rebased.append(value)
        policy.setdefault(compile_target(row['output']),set()).add(tuple(rebased))
    return policy


def selected_include_proof(row,source,policy):
    roots=include_arguments(shlex.split(row['command']));wire=str(source.parent/'wire')
    need(roots.count(wire)<=1,'fex_memory_duplicate_wire_include')
    need(tuple(value for value in roots if value!=wire) in policy.get(compile_target(row['output']),set()),
         'fex_memory_include_source_order')
    return roots



def ninja_object_proof(row,output):
    """Bind actual Ninja compile edge and depfile command to the exported argv."""
    build_raw,_=regular_bytes(output,'build.ninja',16*1024**2)
    rules_raw,_=regular_bytes(output,'CMakeFiles/rules.ninja',4*1024**2)
    lines=build_raw.decode().splitlines();blocks=[]
    for index,line in enumerate(lines):
        match=re.fullmatch(r'build (.*): ([^ ]+) ?(.*)',line)
        if not match or row['output'] not in match[1]:continue
        if original.ninja_tokens(match[1])!=[row['output']]:continue
        dependencies=original.ninja_tokens(match[3]);values={};cursor=index+1
        while cursor<len(lines) and lines[cursor].startswith('  '):
            field=re.fullmatch(r'  ([A-Za-z_]+) = (.*)',lines[cursor])
            need(field and field[1] not in values,'fex_memory_compile_edge_field')
            values[field[1]]=field[2];cursor+=1
        blocks.append((match[2],dependencies,values))
    need(len(blocks)==1,'fex_memory_compile_edge_count');rule,inputs,values=blocks[0]
    need(inputs and inputs[0]==row['file'] and rule.startswith(('C_COMPILER__','CXX_COMPILER__','ASM_COMPILER__')),
         'fex_memory_compile_edge_source')
    need(values.get('DEP_FILE')==row['output']+'.d','fex_memory_compile_edge_depfile')
    fields={};found=0;lines=rules_raw.decode().splitlines()
    for index,line in enumerate(lines):
        if line!='rule '+rule:continue
        found+=1;cursor=index+1
        while cursor<len(lines) and lines[cursor].startswith('  '):
            field=re.fullmatch(r'  ([A-Za-z_]+) = (.*)',lines[cursor])
            need(field and field[1] not in fields,'fex_memory_compile_rule_field')
            fields[field[1]]=field[2];cursor+=1
    need(found==1 and set(fields)=={'depfile','deps','command','description'} and
         fields['depfile']=='$DEP_FILE' and fields['deps']=='gcc','fex_memory_compile_rule')
    for text in (build_raw.decode(),rules_raw.decode()):
        need(not re.search(r'^ *(LAUNCHER|CODE_CHECK) = .+',text,re.M),'fex_memory_compile_launcher')
    args=shlex.split(row['command']);compiler=args[0]
    module=values.get('DYNDEP_MODULE_MAP_FILE')
    expected='${LAUNCHER}${CODE_CHECK}"'+compiler+'" $DEFINES $INCLUDES $FLAGS -MD -MT $out -MF $DEP_FILE'
    if module:expected+=' @$DYNDEP_MODULE_MAP_FILE'
    expected+=' -o $out -c $in'
    need(fields['command']==expected,'fex_memory_compile_actual_rule_command')
    actual=[compiler]+shlex.split(' '.join(values.get(key,'') for key in ('DEFINES','INCLUDES','FLAGS')))
    if module:actual+=['@'+module]
    actual+=['-o',row['output'],'-c',row['file']]
    need(actual==args,'fex_memory_compile_actual_argv')
    return {'rule':rule,'source':row['file'],'object':row['output'],'depfile':values['DEP_FILE'],
            'actual_argv_matches_database':True,'depfile_recipe':'-MD -MT $out -MF $DEP_FILE'}


def make_dependencies(raw):
    """Bounded compiler Make-depfile grammar, never shell or Make execution."""
    need(type(raw) is bytes and 0<len(raw)<=8*1024**2,'fex_memory_depfile_size')
    text=raw.decode('utf-8');need('\0' not in text and '\r' not in text,'fex_memory_depfile_text')
    text=text.replace('\\\n','');words=[];word=[];colon=False;i=0
    while i<len(text):
        char=text[i]
        if char=='\\':
            need(i+1<len(text) and text[i+1] in ' \t\\#:','fex_memory_depfile_escape')
            word.append(text[i+1]);i+=2;continue
        if char=='$':
            need(i+1<len(text) and text[i+1]=='$','fex_memory_depfile_variable');word.append('$');i+=2;continue
        if char==':':
            need(not colon and word and not words,'fex_memory_depfile_target')
            target=''.join(word);word=[];colon=True;i+=1;continue
        need(char!='#','fex_memory_depfile_comment')
        if char.isspace():
            if word:words.append(''.join(word));word=[]
        else:word.append(char)
        i+=1
    if word:words.append(''.join(word))
    need(colon and words and len(words)<=8192 and len(set(words))==len(words),
         'fex_memory_depfile_dependencies')
    return target,words


WIRE_REQUIRED_SOURCES={
    'Source/Windows/Common/PearFEXMemory.cpp','Source/Windows/Common/InvalidationTracker.cpp',
    'Source/Windows/ARM64EC/Module.cpp','Source/Windows/WOW64/Module.cpp',
    'FEXCore/Source/Interface/Core/Core.cpp','FEXCore/Source/Interface/Core/CPUBackend.cpp',
    'FEXCore/Source/Interface/Core/SharedCodeBufferManager.cpp',
    'FEXCore/Source/Interface/Core/JIT/JIT.cpp','FEXCore/Source/Interface/Core/Dispatcher/Dispatcher.cpp',
    'FEXCore/Source/Interface/Core/LookupCache.cpp','FEXCore/Source/Interface/Core/PearJITLinks.cpp',
    'FEXCore/Source/Utils/PearFEXRetirement.cpp','FEXCore/Source/Utils/ArchHelpers/Arm64.cpp'}


def dependency_proof(row,output,source,tc,header_cache):
    name=row['output']+'.d';raw,_=regular_bytes(output,name,8*1024**2)
    target,names=make_dependencies(raw)
    need(target==row['output'],'fex_memory_depfile_object_target')
    paths=[];wire=source.parent/'wire/wine/pear_fex_memory.h'
    for item in names:
        candidate=Path(item)
        if not candidate.is_absolute():candidate=output/candidate
        current=candidate.resolve(strict=True)
        if current.is_relative_to(source):scope='selected_source';base=source
        elif current.is_relative_to(source.parent/'wire'):scope='curated_wire';base=source.parent/'wire'
        elif current.is_relative_to(output):scope='generated_build_data';base=output
        elif current.is_relative_to(tc):scope='qualified_tool_headers';base=tc
        else:raise Error('fex_memory_dependency_outside_inputs')
        normalized=Path(os.path.normpath(str(candidate)))
        need(normalized.is_relative_to(base),'fex_memory_dependency_lexical_scope')
        if scope!='qualified_tool_headers':
            need(current==normalized,'fex_memory_dependency_external_alias')
            # Owned source/generated/wire trees cannot use symlink redirection.
            need(not candidate.is_symlink() and all(not parent.is_symlink() for parent in candidate.parents
                 if parent.is_relative_to(base)),'fex_memory_dependency_alias')
        if scope=='generated_build_data':
            need(current.suffix in ('.h','.hpp','.inl','.inc','.def'),
                 'fex_memory_unreviewed_generated_dependency_kind')
        if current.name=='pear_fex_memory.h':need(current==wire,'fex_memory_selected_wire_shadow')
        if str(current) not in header_cache:
            need(len(header_cache)<20000,'fex_memory_selected_dependency_limit')
            data,mode=regular_bytes(base,current.relative_to(base).as_posix(),8*1024**2)
            need(sum(value['size_bytes'] for value in header_cache.values())+len(data)<=256*1024**2,
                 'fex_memory_selected_dependency_bytes_limit')
            header_cache[str(current)]={'path':str(current),'scope':scope,'sha256':H(data),
                                       'size_bytes':len(data),'mode':mode,
                'content_qualification':'generated_bytes_only' if scope=='generated_build_data' else 'current_bound_input_bytes'}
        paths.append(str(current))
    need(str(Path(row['file'])) in paths,'fex_memory_depfile_source_missing')
    if Path(row['file']).relative_to(source).as_posix() in WIRE_REQUIRED_SOURCES:
        need(str(wire) in paths,'fex_memory_depfile_required_wire_missing')
    return {'path':output.relative_to(source.parent).as_posix()+'/'+name,'sha256':H(raw),
            'size_bytes':len(raw),'object':row['output'],'dependencies':paths,
            'selected_header_semantics':'unperformed','compiler_execution':'unperformed_in_pure_replay'}


def owner_compile_proof(row,output,source,tc,triple,features,policy):
    path=original.compile_command_proof(row,output,source,tc,triple,features)
    selected_include_proof(row,source,policy)
    arguments=shlex.split(row['command']);defines,undefined=macro_values(arguments)
    rel=Path(row['file']).relative_to(source).as_posix()
    if Path(row['file']).suffix!='.S' and rel.startswith(('FEXCore/','Source/Windows/')):
        need(defines.get('PEAR_FEX_MEMORY_OWNER') and
             set(defines['PEAR_FEX_MEMORY_OWNER'])=={'1'} and 'PEAR_FEX_MEMORY_OWNER' not in undefined,
             'fex_memory_owner_macro')
        roots=[]
        for i,arg in enumerate(arguments):
            if arg=='-I':need(i+1<len(arguments),'fex_memory_include_operand');roots.append(arguments[i+1])
            elif arg.startswith('-I'):roots.append(arg[2:])
        need(str(source.parent/'wire') in roots,'fex_memory_curated_wire_include')
    return path


def archive_bytes(raw):
    """Adapt unchanged archive_machines algorithm to the exact owned FD bytes.

    Reuse the original EC symbol-index reader. No path/global monkeypatch and no
    archive extraction, linkage or initialization occurs in this byte adapter.
    """
    need(type(raw) is bytes and len(raw)<=128*1024**2 and raw.startswith(b'!<arch>\n'),
         'fex_memory_archive_bytes')
    offset=8;machines=Counter();entries=[]
    while offset<len(raw):
        need(offset+60<=len(raw) and raw[offset+58:offset+60]==b'`\n','invalid_archive_header')
        try:size=int(raw[offset+48:offset+58].strip());name=raw[offset:offset+16].decode('ascii').strip()
        except (ValueError,UnicodeError):raise Error('invalid_archive_member_size') from None
        need(0<=size<=128*1024**2 and offset+60+size<=len(raw),'invalid_archive_member_bounds')
        blob=raw[offset+60:offset+60+size];entries.append((offset,name,blob))
        if name.startswith('#1/'):
            try:length=int(name[3:])
            except ValueError:raise Error('invalid_bsd_archive_name') from None
            need(0<=length<=len(blob),'invalid_bsd_archive_name');blob=blob[length:]
        if name not in ('/','//','/SYM64/','/<ECSYMBOLS>/'):
            need(len(blob)>=20,'truncated_coff_archive_member')
            machine=struct.unpack_from('<H',blob,6 if blob[:4]==b'\0\0\xff\xff' else 0)[0]
            need(machine in (0xaa64,0xa641,0x8664,0x14c),'unsupported_archive_object_format');machines[str(machine)]+=1
        offset+=60+size+(size&1)
    need(offset==len(raw) and sum(machines.values())>0,'empty_or_invalid_static_archive')
    return {'sha256':H(raw),'size_bytes':len(raw),'coff_members':sum(machines.values()),
            'machines':dict(machines),'ec_symbol_index':check.validate_ec_archive_index(entries)}


class ImmutableFileBytes:
    """A private byte-path argument for the unchanged CHPE reader only."""
    def __init__(self,raw):self.raw=raw
    def stat(self):return types.SimpleNamespace(st_size=len(self.raw))
    def read_bytes(self):return self.raw


class BytesPE(original.PE):
    """Use original bounded PE methods on exact owned FD bytes."""
    def __init__(self,raw):
        need(type(raw) is bytes and len(raw)<=64*1024**2,'fex_memory_module_bytes')
        # Capture the unchanged initialization body in a private namespace. The
        # read helper can supply only this already-admitted image, never reopen
        # or redirect a path. Original module globals remain untouched.
        namespace=dict(original.PE.__init__.__globals__)
        namespace['read_relative']=lambda root,name,limit:raw
        types.FunctionType(original.PE.__init__.__code__,namespace)(self,Path('owned-image.dll'))
        self.image_size=self.number('I',self.opt+56)
        need(0<self.image_size<=1024**3 and all(base+span<=self.image_size
             for base,span,_,_ in self.sections),'fex_memory_module_image_bounds')


def module_bytes(raw,source,target):
    """Execute unchanged metadata algorithms against bytes, never a PE image."""
    namespace=dict(original.module_facts.__globals__)
    namespace['PE']=lambda path:BytesPE(raw)
    chpe_namespace=dict(check.inspect_fixture_arm64ec.__globals__)
    chpe_namespace['Path']=lambda path:ImmutableFileBytes(raw)
    chpe=types.FunctionType(check.inspect_fixture_arm64ec.__code__,chpe_namespace)
    namespace['inspect_fixture_arm64ec']=chpe
    return types.FunctionType(original.module_facts.__code__,namespace)(Path('owned-image.dll'),source,target)


def canonical_macho_path(name,code,*,rpath=False):
    """Validate raw load-command components before Path can normalize them."""
    need(type(name) is str and name and '\\' not in name and '\0' not in name
         and not name.startswith('//'),code)
    parts=name[1:].split('/') if name.startswith('/') else name.split('/')
    need(not any(part in ('','.','..') for part in parts),code)
    if not name.startswith('/'):
        need(parts[0] in ('@loader_path','@executable_path') or
             (not rpath and parts[0]=='@rpath'),code)
    return name


def rooted_native_closure(root,path,bundle):
    """Original load-name resolution with each parser anchored to owned bytes."""
    root=Path(root);bundle=Path(bundle);executable=root.joinpath(*relative(path))
    need(executable.is_relative_to(bundle),'fex_memory_native_bundle_scope')
    found={};pending=[(executable,[])]
    while pending:
        current,inherited=pending.pop()
        if str(current) in found:continue
        need(current.is_relative_to(bundle) and len(found)<128,'fex_memory_native_dependency_scope')
        rel=current.relative_to(root).as_posix();raw,info=wine_owner.inspect_rooted_macho(root,rel)
        # A rooted plain file, not the /dev/fd alias used only during parsing.
        anchored,_=regular_bytes(root,rel,64*1024**2)
        need(raw==anchored and info['architectures']==[byte_readers.MACH_ARM64],
             'fex_memory_native_dependency_changed')
        paths=[canonical_macho_path(item,'fex_memory_noncanonical_rpath',rpath=True).replace(
               '@loader_path',str(current.parent)).replace('@executable_path',str(executable.parent))
               for item in info['rpaths']]+inherited
        resolved=[]
        for name in info['dependencies']:
            canonical_macho_path(name,'fex_memory_noncanonical_load_name')
            if name.startswith(('/usr/lib/','/System/Library/')):
                resolved.append({'name':name,'kind':'macos_system_dependency'});continue
            replaced=name.replace('@loader_path',str(current.parent)).replace(
                     '@executable_path',str(executable.parent))
            candidates=[Path(base)/replaced[7:] for base in paths] if replaced.startswith('@rpath/') else [Path(replaced)]
            hits=set()
            for candidate in candidates:
                need(candidate.is_absolute() and '..' not in candidate.parts,
                     'fex_memory_native_dependency_path')
                if candidate.exists():
                    need(candidate.resolve(strict=True)==candidate and candidate.is_relative_to(bundle),
                         'fex_memory_native_dependency_alias')
                    hits.add(candidate)
            need(len(hits)==1,'unresolved_or_ambiguous_dependency');target=hits.pop()
            resolved.append({'name':name,'kind':'bundled','path':str(target)});pending.append((target,paths))
        found[str(current)]={'path':str(current),'sha256':H(raw),**info,'resolved_dependencies':resolved}
    return list(found.values())


def native_artifacts(root):
    result=[]
    for path,role in original.NATIVE_ARTIFACTS.items():
        raw,info=wine_owner.inspect_rooted_macho(root,path)
        need(info['architectures']==[byte_readers.MACH_ARM64] and
             info['filetype']==(2 if role=='native_service_fixture' else 6),'fex_memory_native_format')
        if role!='native_service_fixture':
            linked='native/'+Path(path).name;origin,mode=regular_bytes(root,linked,64*1024**2)
            installed,installed_mode=regular_bytes(root,path,64*1024**2)
            need(origin==installed==raw and mode==installed_mode,'fex_memory_native_install_copy')
        closure=rooted_native_closure(root,path,Path(root)/('fixtures' if role=='native_service_fixture' else 'install'))
        result.append({'path':path,'role':role,'sha256':H(raw),'size_bytes':len(raw),
                       'macho':info,'native_closure':closure,
                       'copy_origin':None if role=='native_service_fixture' else {
                           'path':linked,'sha256':H(origin),'size_bytes':len(origin),'mode':mode}})
    return result


def source_symbol_proof(text):
    """Map real selected Common and direct-object symbols, without forcing aliases."""
    old=original.source_map_proof(text);owners={}
    for line in text.splitlines():
        match=re.fullmatch(r' +[0-9a-fA-F]{4}:[0-9a-fA-F]{8,16} +([^ ]+) +[0-9a-fA-F]{16} +([^ ]+)',line)
        if not match:continue
        symbol=match[1].removeprefix('#');owner=match[2]
        if ':' in owner:
            archive,member=owner.split(':',1);key=(archive,member)
        else:key=(None,owner)
        owners.setdefault(symbol,set()).add(key)
    base='_ZN7FEXCore5Utils13PearFEXMemory'
    groups={
      'adapter':(base,('libCommonWindows','PearFEXMemory.cpp.obj'),
                 ('Init','Reserve','RegisterExecutor','Enter','Exit','Handoff','Poll','AttachAllocatedThread')),
      'retirement':(base+'10Retirement',(None,'PearFEXRetirement.cpp.obj'),
                    ('AdmissionOpen','PoisonSourceAdmission','EnqueueDetached','DrainAtNativeGate')),
      'links':(base+'5Links',(None,'PearJITLinks.cpp.obj'),('EntryAdmissionOpen',))}
    selected={}
    for group,(prefix,owner,names) in groups.items():
        matches={}
        for name in names:
            actual={s:v for s,v in owners.items() if s.startswith(prefix+str(len(name))+name)
                    and '$' not in s}
            need(actual and all(values=={owner} for values in actual.values()),
                 'fex_memory_selected_symbol_owner:'+group+':'+name)
            matches.update(actual)
        selected[group]=[{'symbol':name,'archive':owner[0],'member':owner[1]} for name in sorted(matches)]
    direct={
        'InitPearCore':('_ZN7FEXCore7Context11ContextImpl12InitPearCoreE',
                       'RNS_5Utils13PearFEXMemory6ResultE','Core.cpp.obj'),
        'CreatePearThread':('_ZN7FEXCore7Context11ContextImpl16CreatePearThreadE',
                           'PKNS_4Core8CPUStateERNS_5Utils13PearFEXMemory6ResultEPS8_Pb','Core.cpp.obj'),
        'FindPearRetainedTarget':('_ZNK7FEXCore3CPU10CPUBackend22FindPearRetainedTargetE',
                                 'y','CPUBackend.cpp.obj')}
    for name,(prefix,args,member) in direct.items():
        expected=prefix+args
        matches={sym:owner for sym,owner in owners.items() if sym.startswith(prefix) and '$' not in sym}
        need(set(matches)=={expected} and matches[expected]=={(None,member)},
             'fex_memory_selected_direct_symbol:'+name)
        selected[name]=[expected]
    return {'baseline_crt_policy_provider':old,'owner_symbols':selected,
            'initializer_execution':'unperformed','selected_symbol_bytes_only':True}


def inspect_modules(root,cross,features,config,baseline):
    """Owner-specific inspector, not the Stage 2 top-level complete inspector."""
    root=Path(root);source=root/'source';artifacts=native_artifacts(root);proofs={}
    required_sources={
        'FEXCore/Source/Interface/Core/Core.cpp','FEXCore/Source/Interface/Core/CPUBackend.cpp',
        'FEXCore/Source/Interface/Core/Dispatcher/Dispatcher.cpp','FEXCore/Source/Interface/Core/JIT/JIT.cpp',
        'FEXCore/Source/Interface/Core/LookupCache.cpp','FEXCore/Source/Interface/Core/PearJITLinks.cpp',
        'FEXCore/Source/Utils/PearFEXRetirement.cpp','FEXCore/Source/Utils/ArchHelpers/Arm64.cpp',
        'Source/Windows/Common/PearFEXMemory.cpp','Source/Windows/Common/DarwinConfigPolicy.cpp',
        'Source/Windows/Common/CPUFeatures.cpp','Source/Windows/Common/InvalidationTracker.cpp'}
    for target,module,machine,triple in [('arm64ec','libarm64ecfex.dll',0xa641,'arm64ec-w64-mingw32'),
                                        ('wow64','libwow64fex.dll',0xaa64,'aarch64-w64-mingw32')]:
        output=root/'pe'/target;tc=Path(cross['cross_tools']);objects=[];modmaps=[]
        policy=include_policy(baseline,output,source);dependencies=[];header_cache={}
        need(output.resolve(strict=True)==output,'fex_memory_pe_output_alias')
        for directory,dirs,names in os.walk(output,followlinks=False):
            dirs.sort();names.sort()
            for name in dirs+names:
                p=Path(directory)/name;info=p.lstat()
                need(not stat.S_ISLNK(info.st_mode) and
                     (stat.S_ISDIR(info.st_mode) if name in dirs else stat.S_ISREG(info.st_mode)),
                     'fex_memory_pe_output_file_kind')
            for name in names:
                path=Path(directory)/name;rel=path.relative_to(root).as_posix()
                if name.endswith('.obj.modmap'):
                    raw,_=regular_bytes(root,rel,65536);need(raw==b'','full_compile_nonempty_module_map')
                    modmaps.append({'path':rel,'role':'empty_compiler_module_map','sha256':H(raw),'size_bytes':0})
                elif path.suffix in ('.obj','.o') and 'CMakeFiles/3.31.8/' not in rel:
                    raw,_=regular_bytes(root,rel,64*1024**2)
                    need(len(raw)>=20 and struct.unpack_from('<H',raw)[0]==machine,
                         'fex_memory_source_object_machine')
                    objects.append({'path':rel,'sha256':H(raw),'size_bytes':len(raw),'machine':machine})
        objects.sort(key=lambda row:row['path']);artifacts.extend(sorted(modmaps,key=lambda row:row['path']))
        need(objects and len(objects)<=25000,'fex_memory_source_object_count')
        cache_raw,_=regular_bytes(output,'CMakeCache.txt',4*1024**2);cache=original.cache_values(cache_raw)
        expected={'CMAKE_BUILD_TYPE':'RelWithDebInfo','MINGW_TRIPLE':triple,
            'CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_TRY_COMPILE_TARGET_TYPE':'STATIC_LIBRARY',
            'CMAKE_DISABLE_FIND_PACKAGE_unordered_dense':'TRUE','CMAKE_DISABLE_FIND_PACKAGE_range-v3':'TRUE',
            'Python_EXECUTABLE':cross['build_auxiliary_tools']['python']['path'],
            'PEAR_FEX_MEMORY_OWNER':'ON','PEAR_FEX_MEMORY_INCLUDE_ROOT':str(root/'wire'),
            'CMAKE_CXX_FLAGS':'-std=c++20 -fno-exceptions -fno-strict-aliasing -fno-stack-protector -DPEAR_FEX_DARWIN=1 -DPEAR_FEX_DARWIN_DCACHE_LOG2='+str(features['dcache_line_log2']),
            'CMAKE_C_FLAGS':'-DPEAR_FEX_DARWIN=1','OVERRIDE_HASH':original.BASE_COMMIT,
            'OVERRIDE_VERSION':'Pear-pinned-FEX'}
        expected.update({key:'ON' if value is True else 'OFF' if value is False else str(value)
                         for key,value in config['cmake_options'].items()})
        need(all(cache.get(key)==value for key,value in expected.items()),'fex_memory_owner_cache_configuration')
        compiler_rows=[]
        for kind,suffix in (('C','-clang'),('CXX','-clang++'),('ASM','-clang')):
            rel='CMakeFiles/3.31.8/CMake'+kind+'Compiler.cmake';raw,_=regular_bytes(output,rel,1024**2)
            names=re.findall(r'^set\(CMAKE_'+kind+r'_COMPILER "([^"\r\n]+)"\)$',raw.decode(),re.M)
            selected=tc/'bin'/(triple+suffix)
            need(names==[str(selected)] and selected.resolve(strict=True).is_relative_to(tc.resolve(strict=True)),
                 'fex_memory_selected_target_compiler')
            compiler_rows.append({'path':rel,'sha256':H(raw),'size_bytes':len(raw)})
        database=original.compile_database(output);actual={row['path'] for row in objects};seen=set();compiled_sources=set()
        for row in database:
            relative(row['output']);need(Path(row['directory'])==output,'fex_memory_compile_directory')
            path=output.joinpath(*relative(row['output']));rel=path.relative_to(root).as_posix()
            if rel not in actual:continue
            proof=owner_compile_proof(row,output,source,tc,triple,features,policy)
            selected_edge=ninja_object_proof(row,output)
            dependency=dependency_proof(row,output,source,tc,header_cache)
            dependency['ninja_compile_edge']=selected_edge;dependencies.append(dependency)
            need(rel not in seen and proof==path,'fex_memory_compile_object_duplicate');seen.add(rel)
            compiled_sources.add(Path(row['file']).relative_to(source).as_posix())
        need(seen==actual,'fex_memory_compile_object_database_closure')
        module_source='Source/Windows/'+('ARM64EC' if target=='arm64ec' else 'WOW64')+'/Module.cpp'
        need(required_sources|{module_source}<=compiled_sources,'fex_memory_missing_owner_source_object')
        ninja_raw,_=regular_bytes(output,'build.ninja',16*1024**2)
        link=original.full_link_edge(ninja_raw.decode(),output,source,module,{str(root/row['path']) for row in objects},tc)
        # Old path archive readers are byte-bound independently below. Their
        # returned machine/index facts must match the original algorithm on the
        # same admitted current bytes rather than trust the library pathname.
        for library in link['linked_archives']:
            path=Path(library['path']);base=output if path.is_relative_to(output) else tc
            raw,_=regular_bytes(base,path.relative_to(base).as_posix(),128*1024**2)
            need(archive_bytes(raw)==library['archive'],'fex_memory_link_archive_byte_closure')
        selected_link=set(link['objects'])
        for row in database:
            source_name=Path(row['file']).relative_to(source).as_posix()
            if source_name.startswith('FEXCore/Source/') and source_name in required_sources:
                need(str(output.joinpath(*relative(row['output']))) in selected_link,
                     'fex_memory_owner_object_not_selected')
        map_raw,_=regular_bytes(output,'link.map',16*1024**2);symbols=source_symbol_proof(map_raw.decode())
        names={'CMakeCache.txt':'cmake_cache','build.ninja':'ninja_recipe','CMakeFiles/rules.ninja':'ninja_rules',
               'compile_commands.json':'compile_database',
               'link.map':'full_module_link_map','Source/Windows/Common/libCommonWindowsRuntime.a':'source_custom_crt_archive',
               'Source/Windows/Common/libCommonWindows.a':'source_owner_archive',
               'Source/Windows/libntdll_ex.a':'source_ntdll_import_archive','Bin/'+module:'full_fex_module',
               **{row['path']:'compiler_data' for row in compiler_rows}}
        if target=='wow64':names['Source/Windows/libwow64_ex.a']='source_wow64_import_archive'
        for rel,role in names.items():
            raw,_=regular_bytes(output,rel,128*1024**2 if role.endswith('_archive') else 64*1024**2)
            row={'path':output.relative_to(root).as_posix()+'/'+rel,'role':role,'sha256':H(raw),'size_bytes':len(raw)}
            if role=='full_fex_module':
                # Original PE reader remains unchanged and compatible: exact
                # source .def, closed import/CHPE/export rules and zero delay.
                facts=module_bytes(raw,source,target)
                row['pe']=facts
            elif role.endswith('_archive'):row['archive']=archive_bytes(raw)
            artifacts.append(row)
        header_names=sorted(header_cache);header_ids={name:index for index,name in enumerate(header_names)}
        for dependency in dependencies:
            dependency['dependency_indices']=[header_ids[name] for name in dependency.pop('dependencies')]
        proofs[target]={'objects':objects,'selected_sources':sorted(compiled_sources),'link_edge':link,
            'dependency_files':dependencies,'selected_dependencies':[header_cache[p] for p in sorted(header_cache)],
            'symbol_map':symbols,'owner_profile_compiled':True,'full_custom_crt_linked':True,
            'source_runtime_qualified':False,'metadata_accounting':'unperformed','initializer_execution':'unperformed'}
    return sorted(artifacts,key=lambda row:row['path']),proofs


def command_gate(root,rows,expected,environment):
    need(type(rows) is list and len(rows)==len(expected),'fex_memory_command_closure')
    for row,(ident,argv) in zip(rows,expected.items()):
        exact(row,('id','argv','cwd','environment','timeout_seconds','max_stream_bytes','exit_code','status',
                   'error_domain','error_code','logs','elapsed_ms'),'fex_memory_command_fields')
        need(row['id']==ident and row['argv']==argv and row['cwd']==str(root)
             and row['environment']=={**environment,'PWD':str(root)}
             and row['timeout_seconds']==(3600 if ident.endswith('.build') and not ident.startswith('native') else 600)
             and row['max_stream_bytes']==MAX_LOG and type(row['exit_code']) is int and row['exit_code']==0
             and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0 and row['status']=='completed'
             and row['error_domain'] is None and row['error_code'] is None,'fex_memory_command_recipe')
        exact(row['logs'],('stdout','stderr'),'fex_memory_command_logs')
        for channel,ref in row['logs'].items():
            exact(ref,('path','sha256','size_bytes'),'fex_memory_command_log_fields')
            need(ref['path']==f'logs/{ident}/{channel}.bin' and type(ref['size_bytes']) is int and
                 0<=ref['size_bytes']<=MAX_LOG,'fex_memory_command_log_path')
            raw,_=regular_bytes(root,ref['path'],MAX_LOG)
            need(H(raw)==ref['sha256'] and len(raw)==ref['size_bytes'],'fex_memory_command_log_changed')
        observed,_=record_bytes(root,f'logs/{ident}/command.json')
        need(observed==row,'fex_memory_command_receipt_changed')


def qualification_gate(value):
    need(all(value[key] is False for key in FALSE_FLAGS) and value['qualification']==QUALIFICATION,
         'fex_memory_build_qualification_overclaim')


def verify_build(root,repo=REPO):
    """Offline independent replay of current source/recipe/object/link closure."""
    root=operation_output(root,repo_root=repo,require_empty=False,create=False)
    need(not (root/'failure.json').exists(),'fex_memory_failed_build')
    value,_=record_bytes(root,'build.json')
    exact(value,('schema_version','record_kind','scope','bindings','producer_sha256','input_snapshots',
        'materialized_source','wire','source_interfaces','commands','artifacts','module_proofs','resources','output_manifest',
        'modules_built_not_loaded','qualification','passed',*FALSE_FLAGS),'fex_memory_build_fields')
    need(type(value['schema_version']) is int and value['schema_version']==1
         and value['record_kind']=='fex_memory_modules_build' and value['scope']=='fex_component'
         and value['passed'] is True and value['modules_built_not_loaded'] is True,'fex_memory_build_scope')
    qualification_gate(value)
    need(value['producer_sha256']=={p:sha256(Path(repo)/p) for p in LOCAL_PRODUCERS},'fex_memory_producer_changed')
    bindings=value['bindings'];exact(bindings,('baseline','projection','derivatives','wine_build'),'fex_memory_bindings')
    baseline=Path(bindings['baseline']['root']);old=original.verify_build(baseline)
    need(sha256(baseline/'build.json')==bindings['baseline']['sha256']==BASE_BUILD_SHA,'fex_memory_baseline_changed')
    exact(bindings['projection'],('root','control_sha256','source_manifest_sha256','source_helper'),
          'fex_memory_projection_binding_fields')
    need(type(bindings['projection']['control_sha256']) is str and
         re.fullmatch('[0-9a-f]{64}',bindings['projection']['control_sha256']),
         'fex_memory_projection_binding_digest')
    source_helper=bound_source_helper(bindings['projection']['source_helper'])
    derived,projection=projection_gate(Path(bindings['projection']['root']),baseline,
                                     Path(bindings['derivatives']['root']),source_helper=source_helper,
                                     expected_control_sha256=bindings['projection']['control_sha256'])
    need(projection==bindings['projection'] and bindings['derivatives']['sha256']==GRAPH_SHA,'fex_memory_projection_binding')
    wire,wire_ref=wire_gate(Path(bindings['wine_build']['root']))
    need(wire_ref==bindings['wine_build'],'fex_memory_wine_wire_binding')
    manifest,raw=record_bytes(root,'materialized-source.json')
    need(H(raw)==value['materialized_source']['sha256'] and value['materialized_source']['path']=='materialized-source.json'
         and manifest=={'schema_version':1,'record_kind':'fex_memory_materialized_source','scope':'fex_component','files':derived['source_files']}
         and source_inventory(root/'source')==derived['source_files'],'fex_memory_materialized_source_changed')
    need(source_inventory(root/'wire')==[{'path':'wine/pear_fex_memory.h','sha256':WIRE_SHA,
             'size_bytes':len(wire),'mode':0o644}] and value['wire']=={'path':'wire/wine/pear_fex_memory.h',
             'sha256':WIRE_SHA,'size_bytes':len(wire)},'fex_memory_wire_copy_changed')
    interfaces=prepare.source_interfaces(root/'source');need(interfaces==value['source_interfaces'],'fex_memory_source_abi_changed')
    need(len(interfaces['services'])==8 and [len(m['exports']) for m in interfaces['modules']]==[20,23],
         'fex_memory_source_abi_closure')
    lock=load_json(old['bindings']['toolchain']['path']);config=original.validate_config(
        load_json(old['bindings']['config']['path']),old['bindings']['inputs']['sha256'])
    features=original.host_metadata(Path(old['bindings']['host_metadata']['path']));cross=old['cross']
    expected=recipe(root,old['bindings']['tools']['path'],lock,features,config,cross)
    command_gate(root,value['commands'],expected,original.complete_environment(lock,cross))
    artifacts,proofs=inspect_modules(root,cross,features,config,baseline)
    need(artifacts==value['artifacts'] and proofs==value['module_proofs'],'fex_memory_artifact_replay_changed')
    resources=value['resources'];exact(resources,('minimum_free_bytes','max_growth_bytes','reserve_free_bytes',
            'free_before_bytes','owned_after_bytes','free_after_bytes','parallel_jobs','peak_observation','owned_bytes_scope'),
            'fex_memory_resource_fields')
    need(all(type(resources[k]) is int and resources[k]>=0 for k in resources if k not in ('peak_observation','owned_bytes_scope'))
         and resources['parallel_jobs']==1 and resources['minimum_free_bytes']==8*1024**3
         and 512*1024**2<=resources['max_growth_bytes']<=8*1024**3
         and 2*1024**3<=resources['reserve_free_bytes']<=8*1024**3
         and resources['free_before_bytes']>=resources['minimum_free_bytes']
         and resources['owned_after_bytes']<=resources['max_growth_bytes']
         and resources['free_after_bytes']>=resources['reserve_free_bytes']
         and resources['peak_observation']=='unknown'
         and resources['owned_bytes_scope']=='regular_payload_excluding_control_records_v1','fex_memory_resource_admission')
    current=output_inventory(root)
    manifest,raw=record_bytes(root,'output-files.json')
    need(manifest=={'schema_version':1,'record_kind':'fex_memory_output_files','scope':'fex_component','files':current}
         and value['output_manifest']=={'path':'output-files.json','sha256':H(raw)}
         and resources['owned_after_bytes']==sum(row['size_bytes'] for row in current)
         and wine_owner.storage_size(root)<=resources['max_growth_bytes'],
         'fex_memory_output_manifest_changed')
    # Exact owned copies independently bind every selected producer, source
    # manifest, tool/config record, patch/Git derivative, header and fixture.
    paths=snapshot_sources(repo,baseline,Path(bindings['projection']['root']),
                           Path(bindings['derivatives']['root']),Path(bindings['wine_build']['root']),old,
                           source_helper=source_helper)
    verify_snapshots(root,value['input_snapshots'],paths)
    return value


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',required=True)
    args=parser.parse_args()
    try:
        verify_build(args.root);print('PASS: supplemented full-module bytes; initialization and runtime unperformed');return 0
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError) as exc:
        print('FAIL: '+getattr(exc,'code',type(exc).__name__),file=sys.stderr);return 1


def snapshot_sources(repo,baseline,projection,derivatives,wine_root,old,*,source_helper):
    """Exact finite input-copy set; tools themselves keep original byte receipts."""
    helper_ref=source_helper_reference(source_helper)
    paths={Path(repo)/p for p in LOCAL_PRODUCERS}|{original.FIXTURE,Path(helper_ref['path']),
        Path(baseline)/'build.json',Path(baseline)/'materialized-source.json',
        Path(baseline)/'pe/arm64ec/compile_commands.json',Path(baseline)/'pe/wow64/compile_commands.json',
        Path(projection)/'control.json',Path(projection)/'materialized-source.json',
        Path(derivatives)/'derivatives.json',Path(derivatives)/'final-source-proposal.json',
        Path(wine_root)/'build.json',Path(wine_root)/'source/include/wine/pear_fex_memory.h'}
    for name,row in old['bindings'].items():
        paths.add(Path(row['path'])/('prepared.json' if name in ('prepared','tools') else ''))
    paths.add(Path(old['cross']['wine_roles']['path']))
    paths.add(original.PATCH_ROOT/'series.json')
    for row in original.patch_set()['patches']:
        paths.add(original.PATCH_ROOT.joinpath(*relative(row['path'])))
    metadata=Path(old['bindings']['host_metadata']['path'])
    host=load_json(metadata)
    for row in host['commands']:
        for ref in row['logs'].values():paths.add(metadata.parent.joinpath(*relative(ref['path'])))
    graph,_=record_bytes(derivatives,'derivatives.json')
    paths.add(graph_path(derivatives,graph['normalization_helper'],1024**2))
    paths.add(graph_path(derivatives,graph['publication_series'],2*1024**2))
    for layer in graph['layers']:
        paths.add(graph_path(derivatives,layer['strict_patch'],2*1024**2))
        paths.add(graph_path(derivatives,layer['source_manifest'],2*1024**2))
        paths.add(graph_path(derivatives,layer['git_derivative'],2*1024**2))
    control,_=record_bytes(projection,'control.json')
    for row in control['commands']:
        paths.add(Path(projection)/row['stdout']);paths.add(Path(projection)/row['stderr'])
    need(len(paths)<=512 and all(p.is_absolute() and '..' not in p.parts for p in paths),
         'fex_memory_snapshot_source_set')
    return sorted(paths,key=str)


def verify_snapshots(root,rows,paths):
    need(type(rows) is list and len(rows)==len(paths),'fex_memory_snapshot_inventory')
    total=0
    for index,(row,path) in enumerate(zip(rows,paths)):
        exact(row,('source','copy','sha256','size_bytes'),'fex_memory_snapshot_fields')
        need(row['source']==str(path) and row['copy']==f'inputs/{index:04d}.bin',
             'fex_memory_snapshot_path_closure')
        current,_=regular_bytes(path.parent,path.name,8*1024**2)
        saved,mode=regular_bytes(root,row['copy'],8*1024**2)
        total+=len(saved)
        need(mode==0o600 and current==saved and H(saved)==row['sha256'] and
             len(saved)==row['size_bytes'] and total<=128*1024**2,'fex_memory_snapshot_changed')
    directory=Path(root)/'inputs'
    need({entry.name for entry in directory.iterdir()}=={f'{i:04d}.bin' for i in range(len(paths))},
         'fex_memory_snapshot_extra_file')


OUTPUT_CONTROLS={'build.json','failure.json','output-files.json'}


def output_inventory(root):
    """Exact regular payload inventory; final control records have separate hashes."""
    root=Path(root);device=root.stat().st_dev;rows=[];count=0;total=0;cases=set()
    for directory,dirs,names in os.walk(root,followlinks=False):
        dirs.sort();names.sort()
        for name in dirs+names:
            path=Path(directory)/name;rel=path.relative_to(root).as_posix();relative(rel)
            count+=1;need(count<=30000,'fex_memory_output_node_limit')
            need(rel.casefold() not in cases,'fex_memory_output_case_alias');cases.add(rel.casefold())
            info=path.lstat()
            need(info.st_dev==device and not stat.S_ISLNK(info.st_mode) and
                 (stat.S_ISDIR(info.st_mode) if name in dirs else stat.S_ISREG(info.st_mode)),
                 'fex_memory_output_kind')
        for name in names:
            path=Path(directory)/name;rel=path.relative_to(root).as_posix()
            if rel in OUTPUT_CONTROLS:continue
            raw,mode=regular_bytes(root,rel,128*1024**2)
            total+=len(raw);need(total<=8*1024**3,'fex_memory_output_bytes_limit')
            rows.append({'path':rel,'sha256':H(raw),'size_bytes':len(raw),'mode':mode})
    return sorted(rows,key=lambda row:row['path'])


if __name__=='__main__':raise SystemExit(main())
