#!/usr/bin/env python3
"""Distinct deterministic graphics construction and independent byte replay.

Historical producers/receipts are immutable prerequisites. This constructor
changes only exact derived compiler environments and owned shader input.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent


def local(name):
    path=HERE/(name+'.py')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode)or before.st_size>1024**2:raise ValueError('local_source_bound')
        raw=bytearray()
        while len(raw)<=1024**2:
            chunk=os.read(fd,min(65536,1024**2+1-len(raw)))
            if not chunk:break
            raw.extend(chunk)
        after=os.fstat(fd)
        identity=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
        if identity(before)!=identity(after)or len(raw)!=before.st_size:raise ValueError('local_source_changed')
    finally:os.close(fd)
    spec=importlib.util.spec_from_file_location('_pear_deterministic_'+name,path)
    module=importlib.util.module_from_spec(spec);exec(compile(bytes(raw),str(path),'exec'),vars(module));return module


reuse=local('deterministic_reuse');metal=local('metal_stdin')
Error,need= reuse.Error,reuse.need
KIND='dxmt_deterministic_pairing_build'
SCOPE='typed_native_metal_pairing'
OWN_FILES={'tools/dxmt/deterministic_pair.py':'deterministic_pair.py',
           'tools/dxmt/deterministic_reuse.py':'deterministic_reuse.py',
           'tools/dxmt/metal_stdin.py':'metal_stdin.py',
           'tools/dxmt/reuse-pins.json':'reuse-pins.json'}
ADDITIONS=('constructor_sources','recipe_policy','qualification_ref','shader_commands','shader_spec_ref')
STABLE_WINE_OBJECTS='/pear/reconstruction/wine/objects'
WINE_COMPILATION_DIRECTORY_FLAG='-fdebug-compilation-dir='+STABLE_WINE_OBJECTS
QUAL_FIELDS={'schema_version','record_kind','scope','original_ref','wine_control_ref','metal_control_ref',
             'resource_ref','source_date_epoch','native_engine_execution_performed','gpu_execution_performed','metal_predecessor_refs',
             'wine_compilation_directory_ref','wine_compilation_directory_binding_ref'}


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def same(a,b,code):need(encoded(a)==encoded(b),code)
def own_sources():
    return {name:{'path':str(HERE/leaf),'sha256':digest(reuse.read_file(HERE,leaf))}
            for name,leaf in OWN_FILES.items()}


def cross_flags():
    # Autoconf expands this variable as shell words. These three closed tokens
    # contain no whitespace or quote syntax, regardless of the physical root.
    return ['-g','-O2',WINE_COMPILATION_DIRECTORY_FLAG]


def environments(old_wine,old_dxmt,physical,invocation):
    need('CROSSCFLAGS'not in old_wine and 'SOURCE_DATE_EPOCH'not in old_wine
         and 'SOURCE_DATE_EPOCH'not in old_dxmt,'det_existing_policy')
    wine,dxmt=dict(old_wine),dict(old_dxmt)
    wine['CROSSCFLAGS']=' '.join(cross_flags())
    wine['SOURCE_DATE_EPOCH']=dxmt['SOURCE_DATE_EPOCH']='0'
    return wine,dxmt


def policy(root,invocation):
    return {'schema_version':2,'source_date_epoch':'0','stable_wine_objects':STABLE_WINE_OBJECTS,
        'debug_compilation_directory_flag':WINE_COMPILATION_DIRECTORY_FLAG,'source_interface':'stdin_exact_original_bytes',
        'shader_options':metal.EXTRAS,'shader_inputs':{name:{'sha256':pin[0],'size_bytes':pin[1]}
            for name,pin in metal.SOURCES.items()},'normalization':'none',
        'raw_product_comparison_required':True,'fresh_native_evidence_required':True}


def resource_inventory(root,common):
    root=common.real_directory(root);items=[];count=0;total=0
    def add(path):
        nonlocal count,total
        info=path.lstat();name=path.relative_to(root).as_posix();count+=1
        need(count<=100000,'det_resource_count')
        if stat.S_ISREG(info.st_mode):
            need(info.st_size<=2*1024**3,'det_resource_file_bound');total+=info.st_size
            need(total<=8*1024**3,'det_resource_total_bound')
            items.append({'path':name,'type':'regular','sha256':common.sha256(path),
                          'size_bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode)})
        elif stat.S_ISLNK(info.st_mode):
            target=os.readlink(path);need(not Path(target).is_absolute(),'det_resource_absolute_alias')
            resolved=path.resolve(strict=True)
            need(resolved.is_relative_to(root)and(resolved.is_file()or resolved.is_dir()),'det_resource_alias_escape')
            items.append({'path':name,'type':'symlink','target':target,'mode':stat.S_IMODE(info.st_mode)})
        else:raise Error('det_resource_special')
    for parent,dirs,names in os.walk(root,followlinks=False):
        current=Path(parent);common.real_directory(current)
        for name in list(dirs):
            path=current/name
            if path.is_symlink():add(path);dirs.remove(name)
        for name in names:add(current/name)
    need(items,'det_resource_empty')
    return {'schema_version':1,'record_kind':'dxmt_metal_resource_inventory','root':str(root),
            'files':sorted(items,key=lambda x:x['path'])}


def resource_sidecar(ref,common):
    _,raw=ref_file(ref,common,32*1024**2)
    value=common.decode_json(raw,max_bytes=32*1024**2,max_nodes=1000000)
    need(type(value)is dict and set(value)=={'schema_version','record_kind','root','files','source_inventory_ref'},
         'det_resource_sidecar_fields')
    observed=resource_inventory(value['root'],common)
    same({key:value[key]for key in observed},observed,'det_resource_inventory_changed')
    path,original=ref_file(value['source_inventory_ref'],common,32*1024**2)
    old=common.decode_json(original,max_bytes=32*1024**2,max_nodes=1000000)
    reduced=[{key:item for key,item in row.items()if key!='mode'or row['type']=='regular'}for row in observed['files']]
    same(old,{'root':observed['root'],'files':reduced},'det_resource_origin_changed')
    return value


def ref_file(ref,common,limit=8*1024**2):
    common.fields(ref,['path','sha256']);path=Path(ref['path']);common.real_directory(path.parent)
    raw=common.read_relative(path.parent,path.name,limit);need(digest(raw)==ref['sha256'],'det_reference_changed')
    return path,raw


def external_fact(path,common):
    path=Path(path);resolved=path.resolve(strict=True);need(resolved.is_file()and not resolved.is_symlink(),'det_tool_regular')
    info=resolved.stat();return {'path':str(path),'resolved_path':str(resolved),'sha256':common.sha256(resolved),
                               'size_bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode)}


def make_dependencies(raw):
    need(type(raw)is bytes and len(raw)<=65536 and b'\x00'not in raw,'det_dependency_bound')
    text=raw.decode().replace('\\\n','');tokens=[];token='';escaped=False
    # Make escaping is parsed, never shell executed; exactly one target marker.
    marker=None
    for character in text:
        if escaped:token+=character;escaped=False
        elif character=='\\':escaped=True
        elif character==':':
            need(marker is None,'det_dependency_multiple_targets')
            tokens.append(token);token='';marker=len(tokens)
        elif character.isspace():
            if token:tokens.append(token);token=''
        else:token+=character
    if token:tokens.append(token)
    need(not escaped and marker==1 and len(tokens)>=2 and len(set(tokens[1:]))==len(tokens[1:]),'det_dependency_shape')
    return tokens[0],tokens[1:]


def replay_probe_streams(root,row,common):
    for name in ['stdout','stderr']:
        common.fields(row[name],['path','sha256','size_bytes']);raw=common.read_relative(root,row[name]['path'],metal.MAX_LOG)
        need(digest(raw)==row[name]['sha256']and len(raw)==row[name]['size_bytes'],'det_probe_stream_changed')
    need(type(row['exit_code'])is int and row['exit_code']==0 and type(row['elapsed_ms'])is int
         and 0<=row['elapsed_ms']<=600000,'det_probe_exit_or_bound')


METAL_PROBE_PRODUCER='cc0a2595fa43a5357e7b89a6896788b15b4aab430e3f18ea2f7db0a2c4f1c18d'


def probe_producer(value,pin,common):
    common.fields(value,['path','sha256','size_bytes','unchanged_observed'])
    path,raw=ref_file({key:value[key]for key in ['path','sha256']},common)
    need(value['sha256']==pin and type(value['size_bytes'])is int and len(raw)==value['size_bytes']
         and value['unchanged_observed']is True,'det_control_producer')
    return path


def external_bytes(path,common,limit=32*1024**2):
    path=Path(path);need(path.is_absolute()and '..'not in path.parts,'det_external_input_path')
    canonical=path.resolve(strict=True)
    return common.read_relative(common.real_directory(canonical.parent),canonical.name,limit)


METAL_PREDECESSOR_PINS = {
 'control': '56307bfb58837978fcf9c34bc9db041f20b17db3c7601d16a2004a7581047598',
 'producer': 'd8fc3898d1c2fc7e7937fe967328744276dd18f9436ed1dae2f9f468bfc2bd15',
 'recipe': 'f366f20f3abc9a86475beb21bb2f96db9db07d613cd91e7a4c3fa7c77fc6f286'}


def declared_path(raw,name):
    # Read one literal Path declaration in a hash-admitted original producer;
    # never execute it or decode/normalize its untrusted path spelling.
    nodes=[node for node in ast.parse(raw).body if isinstance(node,ast.Assign)
           and any(isinstance(target,ast.Name)and target.id==name for target in node.targets)]
    need(len(nodes)==1,'det_metal_declared_path')
    value=nodes[0].value
    need(isinstance(value,ast.Call)and isinstance(value.func,ast.Name)and value.func.id=='Path'
         and len(value.args)==1 and not value.keywords and isinstance(value.args[0],ast.Constant)
         and type(value.args[0].value)is str,'det_metal_declared_path')
    path=Path(value.args[0].value)
    need(path.is_absolute()and '..'not in path.parts,'det_metal_declared_path')
    return path


def metal_predecessor(value,root,refs,common):
    need(type(refs)is dict and set(refs)==set(METAL_PREDECESSOR_PINS),'det_metal_predecessor_refs')
    content={}
    for key,pin in METAL_PREDECESSOR_PINS.items():
        need(type(refs[key])is dict and set(refs[key])=={'path','sha256'}
             and refs[key]['sha256']==pin,'det_metal_predecessor_pin')
        content[key]=ref_file(refs[key],common)[1]
    prior,recipe=common.decode_json(content['control']),common.decode_json(content['recipe'])
    strong_raw=ref_file({key:value['producer'][key]for key in ['path','sha256']},common)[1]
    need(digest(strong_raw)==METAL_PROBE_PRODUCER,'det_metal_control_producer')
    need(Path(refs['control']['path'])==declared_path(strong_raw,'prior')/'control.json'
         and root==declared_path(strong_raw,'out')
         and Path(refs['control']['path']).parent==declared_path(content['producer'],'r')
         and Path(refs['recipe']['path'])==declared_path(content['producer'],'recipe'),
         'det_metal_predecessor_source_paths')
    need(value.get('prior_probe_sha256')==METAL_PREDECESSOR_PINS['control']
         and prior['recipe_sha256']==METAL_PREDECESSOR_PINS['recipe'], 'det_metal_predecessor_changed')
    _,cap_raw=ref_file(recipe['source_ref'],common)
    capability=common.decode_json(cap_raw)
    same(recipe['selected'],capability['selected'],'det_metal_predecessor_selected')
    same(recipe['environment'],capability['environment'],'det_metal_predecessor_environment')
    commands=[row for row in capability['commands']if row['id']=='metal.compile']
    need(len(commands)==1,'det_metal_predecessor_compile_set')
    same(recipe['accepted_compile_command'],commands[0],'det_metal_predecessor_recipe')
    selected=capability['selected']['metal']
    need(prior['tool']==selected['resolved_path'] and prior['tool_sha256']==selected['sha256']
         and value['tool_sha256']==selected['sha256'],'det_metal_predecessor_tool')
    expected=dict(capability['environment'])
    expected.update(PATH='/usr/bin:/bin:/usr/sbin:/sbin',TMPDIR=str(Path(refs['control']['path']).parent/'tmp'))
    same(prior['environment'],expected,'det_metal_predecessor_environment')
    expected['TMPDIR']=str(root/'tmp')
    same(value['environment'],expected,'det_metal_control_environment')
    return prior


def metal_control(ref,sources,original,resource,predecessor_refs,common):
    path,raw=ref_file(ref,common);root=path.parent;value=common.decode_json(raw)
    need(value.get('record_kind')=='root_actual_four_original_recipe_shader_independent_cache_compile_probe',
         'det_metal_control_kind')
    probe_producer(value['producer'],METAL_PROBE_PRODUCER,common)
    prior=metal_predecessor(value,root,predecessor_refs,common)
    need(all(value.get(k)is False for k in ['full_native_rebuild','gpu_execution','native_engine_execution',
          'pipeline_modified','stage5_complete'])and value['independent_owned_caches']is True
          and value['tool_and_source_unchanged']is True,'det_metal_control_scope')
    need(set(sources)==set(metal.SOURCES),'det_metal_control_source_set')
    originals={name:common.read_relative(original/'dxmt/source',name,32768)for name in [*sources,metal.HEADER]}
    same(value['original_sources'],{name:{'sha256':digest(data),'size_bytes':len(data)}for name,data in originals.items()},
         'det_metal_original_sources')
    catalog=value['toolchain_resources']
    common.fields(catalog,['root','inventory_path','inventory_sha256','rows','logical_bytes','unchanged_observed'])
    need(catalog['root']==resource['root']and catalog['unchanged_observed']is True,'det_metal_resource_scope')
    same(resource['source_inventory_ref'],{'path':str(root/catalog['inventory_path']),
        'sha256':catalog['inventory_sha256']},'det_metal_resource_origin')
    need(type(catalog['rows'])is int and catalog['rows']==len(resource['files'])
         and type(catalog['logical_bytes'])is int and catalog['logical_bytes']==sum(row.get('size_bytes',0)for row in resource['files']),
         'det_metal_resource_counts')
    settings=value['sdk_settings'];common.fields(settings,['path','sha256','size_bytes'])
    sdk_raw=external_bytes(settings['path'],common)
    need(digest(sdk_raw)==settings['sha256']and len(sdk_raw)==settings['size_bytes']
         and settings['path']==str(Path(value['environment']['SDKROOT'])/'SDKSettings.json'),'det_metal_sdk_changed')
    rows=value['commands'];need(type(rows)is list and len(rows)==8,'det_metal_control_count');seen=set();outputs={}
    for row in rows:
        source,side=row['source'],row['side'];need(source in sources and side in('short','sixteen-more-characters')
            and(source,side)not in seen,'det_metal_control_duplicate');seen.add((source,side))
        name=Path(source).stem;supplied=common.read_relative(root,side+'/source/'+source,32768)
        pin=metal.SOURCES[source];need(supplied==originals[source]and(digest(supplied),len(supplied))==pin
             and row['source_sha256']==pin[0]and row['source_bytes']==pin[1],'det_metal_control_source')
        expected=['/usr/bin/arch','-arm64',prior['tool'],'-o',str(root/(side+'-'+name+'.air')),
            '-c','-x','metal','-',*metal.EXTRAS[source],'-fmodules-cache-path='+str(root/side/'modules-cache'),
            '-iquote',str((root/side/'source'/source).parent),'-MMD','-MF',str(root/(side+'-'+name+'.d'))]
        same(row['argv'],expected,'det_metal_control_recipe')
        tool=external_fact(row['argv'][2],common)
        need(tool['sha256']==value['tool_sha256']and Path(tool['resolved_path']).is_relative_to(Path(resource['root']))
             and Path(tool['resolved_path']).parents[2]==Path(resource['root']),'det_metal_control_tool')
        replay_probe_streams(root,row,common)
        for field in ['air','dependencies']:
            receipt=row[field];payload=common.read_relative(root,receipt['path'])
            need(digest(payload)==receipt['sha256']and len(payload)==receipt['size_bytes'],'det_metal_control_output')
        output=common.read_relative(root,row['air']['path']);outputs[(source,side)]=output
        target,deps=make_dependencies(common.read_relative(root,row['dependencies']['path']))
        need(target==str(root/row['air']['path'])and len(deps)==(2 if source.startswith('src/dxmt/')else 1)
             and deps[0].endswith('/include/metal/module.modulemap'),'det_metal_control_dependencies')
        need(Path(deps[0]).is_relative_to(Path(resource['root'])),'det_metal_dependency_origin')
        entries=[item for item in resource['files']if item['path']==Path(deps[0]).relative_to(resource['root']).as_posix()]
        need(len(entries)==1 and entries[0]['type']=='regular','det_metal_dependency_not_accounted')
        need(row['dependencies']['quoted_constant_header_present']is source.startswith('src/dxmt/'),
             'det_metal_header_observation')
        if source.startswith('src/dxmt/'):
            header=side+'/source/'+metal.HEADER
            need(deps[1]==str(root/header)and common.read_relative(root,header)==originals[metal.HEADER],'det_metal_control_header')
    need(all(outputs[(source,'short')]==outputs[(source,'sixteen-more-characters')]for source in sources),
         'det_metal_control_bytes_differ')
    same(value['pairs'],[{'source':source,'both_commands_passed':True,'whole_air_bytes_equal':True}for source in sources],
         'det_metal_pairs_changed')
    return value


WINE_PROBE_PRODUCER='99918fc2b061adaca6853fa5e15e383451b42e204b941f7bf5efbbae77b5f7ab'


def probe_output(root,ref,common,limit=16*1024**2):
    data=common.read_relative(root,ref['path'],limit)
    need(digest(data)==ref['sha256']and type(ref['size_bytes'])is int and len(data)==ref['size_bytes'],
         'det_probe_payload_changed')
    return data


def wine_dependencies(root,side,ident,discovery,rows,argv,original,wine_tools,common):
    common.fields(rows,['before','after','depfile_sha256'])
    before=probe_output(root,discovery['dependency_preimage'],common,65536)
    dep_path=Path(argv[argv.index('-MF')+1]);need(dep_path.is_relative_to(root),'det_wine_depfile_scope')
    after=common.read_relative(root,dep_path.relative_to(root).as_posix(),65536)
    need(digest(after)==rows['depfile_sha256'],'det_wine_depfile_changed')
    parsed=[]
    for phase,raw in [('discovery',before),('compilation',after)]:
        target,dependencies=make_dependencies(raw)
        expected_target=('dllmain.o'if ident=='wine_object'else'pairing_pe.o')if phase=='discovery'else argv[argv.index('-o')+1]
        need(target==expected_target,'det_wine_dep_target')
        observed=[]
        for declared in sorted(dependencies):
            path=(root/side/'objects'/declared).resolve(strict=True)
            allowed=[original/'wine/source',original/'wine/objects',wine_tools/'llvm-mingw',root/side/'source']
            need(any(path.is_relative_to(base)for base in allowed),'det_wine_dependency_outside_inputs')
            data=external_bytes(path,common)
            observed.append({'path':str(path),'sha256':digest(data),'size_bytes':len(data)})
        need(len({row['path']for row in observed})==len(observed),'det_wine_dependency_alias_duplicate')
        parsed.append(observed)
    same(rows['before'],parsed[0],'det_wine_before_dependency_changed')
    same(rows['after'],parsed[1],'det_wine_after_dependency_changed')
    same(parsed[0],parsed[1],'det_wine_dependency_set_changed')
    required=[root/side/'source/dlls/winemac.drv/dllmain.c']if ident=='wine_object'else[
        root/side/'source/pairing_pe.c',root/side/'source/protocol.h']
    need(all(str(path)in{row['path']for row in parsed[0]}for path in required),'det_wine_required_dependency_missing')


def wine_control(ref,original,common):
    """Replay the exact producer-bound dependency-before/full-MD control.

    The earlier incomplete controls remain refused. This proves the measured
    input transport, path effect and LLD epoch; actual configure insertion and
    whole component equality are independently required by the new constructor.
    """
    path,raw=ref_file(ref,common);root=path.parent;value=common.decode_json(raw)
    need(value.get('record_kind')=='root_actual_Wine_PE_object_debug_map_and_LLD_epoch_probe',
         'det_wine_control_kind')
    need(value.get('input_closure')is not None and value.get('dependency_closure')is not None
         and value.get('dependency_commands')is not None,'det_wine_control_input_closure_missing')
    probe_producer(value['producer'],WINE_PROBE_PRODUCER,common)
    need(value['original_build_sha256']==common.sha256(original/'build.json')
         and all(value[k]is False for k in ['full_Wine_DXMT_rebuild','gpu_execution','module_loading','stage5_complete',
             'configure_CROSSCFLAGS_insertion'])and all(value[k]is True for k in ['original_inputs_unchanged',
             'protocol_source_and_copies_bound','original_complete_build_replay_before_and_after']),
         'det_wine_control_scope')
    build=common.decode_json(common.read_relative(original,'build.json'),max_bytes=8*1024**2,max_nodes=300000)
    expected_env=dict(build['wine_environment']);expected_env.update(SOURCE_DATE_EPOCH='0',TMPDIR=str(root/'tmp'))
    same(value['environment'],expected_env,'det_wine_control_environment')
    command_raw=common.read_relative(original,'logs/wine.driver/stdout',32*1024**2)
    need(digest(command_raw)==value['original_command_log_sha256'],'det_wine_control_original_log')
    selected=[shlex.split(line)for line in command_raw.decode().replace('\\\n',' ').splitlines()
        if ' -c 'in line and 'aarch64-windows/dllmain.o'in line]
    need(len(selected)==1,'det_wine_original_compile_set')
    same(value['original_wine_object_argv'],selected[0],'det_wine_original_compile_recipe')
    fixture=next(row['argv']for row in build['commands']if row['id']=='fixture.compile')
    same(value['original_fixture_argv'],fixture,'det_wine_original_fixture_recipe')
    expected_sources={'wine/source/dlls/winemac.drv/dllmain.c':'source/dlls/winemac.drv/dllmain.c',
        'inputs/tests/dxmt/pairing/pairing_pe.c':'source/pairing_pe.c',
        'inputs/tests/dxmt/pairing/protocol.h':'source/protocol.h'}
    expected_inputs={}
    for name in expected_sources:
        data=common.read_relative(original,name)
        expected_inputs[str(original/name)]={'sha256':digest(data),'size_bytes':len(data)}
    same(value['inputs'],expected_inputs,'det_wine_original_input_set')
    need(set(value['input_closure'])=={'short','sixteen-more-characters'},'det_wine_side_set')
    for side in ['short','sixteen-more-characters']:
        expected=[]
        for original_name,supplied_name in expected_sources.items():
            data=common.read_relative(original,original_name);supplied=common.read_relative(root,side+'/'+supplied_name)
            need(data==supplied,'det_wine_control_source_changed')
            expected.append({'original_path':str(original/original_name),'copy_path':str(root/side/supplied_name),
                'sha256':digest(supplied),'size_bytes':len(supplied)})
        same(value['input_closure'][side],expected,'det_wine_source_receipts')
    originals={'wine_object':selected[0],'finite_fixture_link':fixture}
    expected_tools={}
    for args in originals.values():
        canonical=Path(args[0]).resolve(strict=True);data=external_bytes(canonical,common,64*1024**2)
        expected_tools[str(canonical)]={'sha256':digest(data),'size_bytes':len(data)}
    same(value['tools'],expected_tools,'det_wine_probe_tool_set')
    wine_tools=Path(build['wine_tools_ref']['path'])
    rows=value['commands'];need(type(rows)is list and len(rows)==4,'det_wine_control_command_set')
    discoveries=value['dependency_commands'];need(type(discoveries)is list and len(discoveries)==4,'det_wine_discovery_count')
    need(set(value['dependency_closure'])=={'short','sixteen-more-characters'}and all(
        set(value['dependency_closure'][side])==set(originals)for side in value['dependency_closure']), 'det_wine_dependency_closure_set')
    seen=set();products={}
    for row in rows:
        side,ident=row['side'],row['name'];need(side in ['short','sixteen-more-characters']and ident in originals
            and(side,ident)not in seen,'det_wine_control_duplicate');seen.add((side,ident));replay_probe_streams(root,row,common)
        argv=row['argv'];expected=list(originals[ident]);expected[0]=str(Path(expected[0]).resolve(strict=True))
        output=root/side/'objects'/('dllmain.obj'if ident=='wine_object'else'pairing.exe')
        expected[expected.index('-o')+1]=str(output)
        if ident=='wine_object':
            for index,arg in enumerate(expected):
                if arg.startswith('-I')and not Path(arg[2:]).is_absolute():
                    expected[index]='-I'+str((original/'wine/objects'/arg[2:]).resolve(strict=True))
            expected+=['-fdebug-prefix-map='+str(root/side/'objects')+'='+STABLE_WINE_OBJECTS]
            depfile=root/side/'objects/dllmain.d'
        else:
            expected[expected.index(str(original/'inputs/tests/dxmt/pairing/pairing_pe.c'))]=str(root/side/'source/pairing_pe.c')
            depfile=root/side/'objects/pairing.d'
        expected+=['-MD','-MF',str(depfile)]
        same(argv,expected,'det_wine_control_recipe')
        need(row['cwd']==str(root/side/'objects'),'det_wine_control_cwd')
        matching=[d for d in discoveries if d['side']==side and d['name']==ident]
        need(len(matching)==1,'det_wine_discovery_duplicate');discovery=matching[0]
        dargs=list(expected);dargs[dargs.index('-MD')]='-M';dargs+=['-Wno-unused-command-line-argument']
        same(discovery['argv'],dargs,'det_wine_discovery_recipe')
        need(discovery['cwd']==row['cwd'],'det_wine_discovery_cwd');replay_probe_streams(root,discovery,common)
        wine_dependencies(root,side,ident,discovery,value['dependency_closure'][side][ident],argv,original,wine_tools,common)
        receipt=row['output'];need(receipt['path']==output.relative_to(root).as_posix(),'det_wine_probe_output_path')
        payload=probe_output(root,receipt,common)
        if ident=='finite_fixture_link':
            need(payload[:2]==b'MZ','det_wine_control_pe');peoff=struct.unpack_from('<I',payload,60)[0]
            need(payload[peoff:peoff+4]==b'PE\0\0'and struct.unpack_from('<H',payload,peoff+4)[0]==0xaa64
                 and struct.unpack_from('<I',payload,peoff+8)[0]==receipt['coff_timestamp']==0,'det_wine_epoch')
        else:need(struct.unpack_from('<H',payload)[0]==0xaa64,'det_wine_control_coff')
        products[(side,ident)]=payload
    # Clang's intermediate COFF timestamp is intentionally not accepted as a
    # reproducible product. This narrowly measured control compares all other
    # object bytes, while final products must have exact whole-byte equality.
    left,right=products[('short','wine_object')],products[('sixteen-more-characters','wine_object')]
    need(len(left)==len(right)and left[:4]==right[:4]and left[8:]==right[8:],'det_wine_object_non_timestamp_difference')
    need(products[('short','finite_fixture_link')]==products[('sixteen-more-characters','finite_fixture_link')],
         'det_wine_fixture_bytes_differ')
    expected_pairs=[{'name':ident,'both_commands_passed':True,
        'complete_bytes_equal':products[('short',ident)]==products[('sixteen-more-characters',ident)]}for ident in originals]
    same(value['pairs'],expected_pairs,'det_wine_pairs_changed')
    return value


WINE_FIXED_PRODUCER='554eb73a0936a7055c2119b1119ed4d675d9f4d715d7833d27c4cf906976fc07'
WINE_BINDING_PRODUCER='b408c17979d6a4d13af7d23b5afb535630e58b26a0f36896e4fac0b94fe85afd'
WINE_FAILED_CONFIGURE='320be8ba6941f87be6ce5b676214b142934a7c6f871a7747d0cb833a9abc9b93'
FIXED_FIELDS={'record_kind','producer','prior_ref','failed_configure_ref','inputs','commands','wine_configuration',
 'compiler_flag','objects_complete_bytes_equal','coincident_object_timestamps_are_not_fixed_epoch_proof',
 'configure_source_reused_read_only','all_inputs_unchanged','full_build','module_loading','gpu_execution','stage5_complete'}
BINDING_FIELDS={'schema_version','record_kind','observation_phase','control_ref','probe_producer','observer_producer',
 'input_before','input_after','generated_before','generated_after','diagnostic_source_alias','wine_configuration',
 'before_after_unchanged','native_operations_performed','initial_probe_modes_observed','full_build_qualified','stage5_complete'}
GENERATED_FIXED=('wine/objects/Makefile','wine/objects/config.log','wine/objects/include/config.h','wine/objects/config.status')


def fixed_observations(rows,expected_paths,common):
    need(type(rows)is list and len(rows)==len(expected_paths),'det_fixed_observation_count')
    need([row['path']for row in rows]==expected_paths,'det_fixed_observation_paths')
    for row in rows:
        common.fields(row,['path','resolved_path','sha256','size_bytes','mode'])
        need(type(row['size_bytes'])is int and row['size_bytes']>=0 and type(row['mode'])is int
             and 0<=row['mode']<=0o777,'det_fixed_observation_types')
        path=Path(row['path']);need(path.is_absolute()and '..'not in path.parts,'det_fixed_observation_path')
        common.real_directory(path.parent)
        need(not path.is_symlink()and path.resolve(strict=True)==path,'det_fixed_observation_alias')
        same(row,external_fact(path,common),'det_fixed_observation_changed')
    return rows


def fixed_makefile(raw):
    need(type(raw)is bytes and len(raw)<=64*1024**2,'det_fixed_makefile_bound')
    text=raw.decode();result={}
    for name in ['aarch64_CFLAGS','aarch64_CXXFLAGS']:
        found=re.findall(r'^'+name+r' = (.*)$',text,re.M)
        need(len(found)==1,'det_fixed_configuration_field')
        result[name]=shlex.split(found[0]);same(result[name],cross_flags(),'det_fixed_configuration_flags')
    return result


def fixed_post_binding(value,proof,control_ref,root,common):
    need(type(value)is dict and set(value)==BINDING_FIELDS and type(value['schema_version'])is int
         and value['schema_version']==1 and value['record_kind']=='root_Wine_fixed_directory_post_probe_binding'
         and value['observation_phase']=='post_original_probe','det_fixed_binding_scope')
    need(value['before_after_unchanged']is True and all(value[name]is False for name in
        ['native_operations_performed','initial_probe_modes_observed','full_build_qualified','stage5_complete']),
        'det_fixed_binding_claims')
    same(value['control_ref'],control_ref,'det_fixed_binding_control')
    same(value['probe_producer'],proof['producer'],'det_fixed_binding_producer')
    _,observer=ref_file(value['observer_producer'],common)
    need(value['observer_producer']['sha256']==WINE_BINDING_PRODUCER,'det_fixed_observer_producer')
    need(declared_path(observer,'root')==root,'det_fixed_observer_root')
    expected=sorted(proof['inputs'])
    before=fixed_observations(value['input_before'],expected,common)
    after=fixed_observations(value['input_after'],expected,common)
    same(before,after,'det_fixed_post_inputs_changed')
    for row in before:
        same({key:row[key]for key in ['sha256','size_bytes']},proof['inputs'][row['path']],
            'det_fixed_binding_input_changed')
    paths=[str(root/name)for name in GENERATED_FIXED]
    generated_before=fixed_observations(value['generated_before'],paths,common)
    generated_after=fixed_observations(value['generated_after'],paths,common)
    same(generated_before,generated_after,'det_fixed_generated_changed')
    expected_alias={'path':str(root/'wine/source'),'target':str(Path(proof['failed_configure_ref']['path']).parent/'wine/source')}
    same(value['diagnostic_source_alias'],expected_alias,'det_fixed_source_alias_scope')
    alias=Path(expected_alias['path']);need(alias.is_symlink()and os.readlink(alias)==expected_alias['target'],
        'det_fixed_source_alias_changed');common.real_directory(expected_alias['target'])
    observed=fixed_makefile(common.read_relative(root,GENERATED_FIXED[0],64*1024**2))
    same(value['wine_configuration'],observed,'det_fixed_binding_configuration')
    same(proof['wine_configuration'],observed,'det_fixed_probe_configuration')
    return value


def fixed_compilation_directory(control_ref,binding_ref,prior_ref,prior,common):
    path,raw=ref_file(control_ref,common,16*1024**2);root=path.parent
    value=common.decode_json(raw,max_bytes=16*1024**2,max_nodes=300000)
    need(type(value)is dict and set(value)==FIXED_FIELDS and
         value['record_kind']=='root_actual_fixed_Wine_compilation_directory_and_configure_probe',
         'det_fixed_probe_shape')
    same(value['prior_ref'],prior_ref,'det_fixed_prior')
    _,producer=ref_file(value['producer'],common)
    need(value['producer']['sha256']==WINE_FIXED_PRODUCER and declared_path(producer,'out')==root
         and declared_path(producer,'old_control')==Path(prior_ref['path']),'det_fixed_producer')
    need(value['compiler_flag']==WINE_COMPILATION_DIRECTORY_FLAG and
         all(value[name]is True for name in ['coincident_object_timestamps_are_not_fixed_epoch_proof',
         'configure_source_reused_read_only','all_inputs_unchanged'])and all(value[name]is False for name in
         ['full_build','module_loading','gpu_execution','stage5_complete']), 'det_fixed_probe_claims')
    failed_path,failed_raw=ref_file(value['failed_configure_ref'],common)
    need(value['failed_configure_ref']['sha256']==WINE_FAILED_CONFIGURE
         and declared_path(producer,'failed_root')==failed_path.parent,'det_fixed_failed_reference')
    failed=common.decode_json(failed_raw,max_bytes=8*1024**2,max_nodes=300000)
    need(failed['record_kind']==KIND and failed['passed']is False and failed['phase']=='wine.configure'
         and len(failed['commands'])==1,'det_fixed_failure_scope')
    original=failed['commands'][0]
    need(original['id']=='wine.configure'and type(original['exit_code'])is int and original['exit_code']==1,
         'det_fixed_original_configure')
    expected_inputs={}
    def add(path,fact):
        if path in expected_inputs:same(expected_inputs[path],fact,'det_fixed_conflicting_input')
        expected_inputs[path]=fact
    for side in prior['dependency_closure'].values():
        for item in side['wine_object']['before']:add(item['path'],{key:item[key]for key in ['sha256','size_bytes']})
    for path,item in prior['tools'].items():add(path,item)
    source=failed_path.parent/'wine/source'
    for item in failed['source']['wine']['after_files']:
        add(str(source/item['path']),{key:item[key]for key in ['sha256','size_bytes']})
    same(value['inputs'],expected_inputs,'det_fixed_input_closure')
    for path,item in expected_inputs.items():
        data=external_bytes(path,common,64*1024**2)
        same(item,{'sha256':digest(data),'size_bytes':len(data)},'det_fixed_input_bytes')
    commands=value['commands'];need(type(commands)is list and len(commands)==3,'det_fixed_command_count')
    selected=[row for row in prior['commands']if row['name']=='wine_object']
    need(len(selected)==2,'det_fixed_predecessor_command_count');products=[]
    for index,old in enumerate(selected):
        row=commands[index]
        common.fields(row,['id','argv','cwd','exit_code','elapsed_ms','stdout','stderr','output','depfile',
            'dependencies_unchanged_from_qualified_full_MD'])
        expected=[arg for arg in old['argv']if not arg.startswith('-fdebug-prefix-map=')]+[WINE_COMPILATION_DIRECTORY_FLAG]
        expected[expected.index('-o')+1]=str(root/('object'+str(index)+'.obj'))
        expected[expected.index('-MF')+1]=str(root/('object'+str(index)+'.d'))
        same(row['argv'],expected,'det_fixed_compile_recipe')
        need(row['id']=='wine_object_'+str(index)and row['cwd']==old['cwd']
             and row['dependencies_unchanged_from_qualified_full_MD']is True,'det_fixed_compile_scope')
        replay_probe_streams(root,row,common)
        need(row['output']['path']=='object'+str(index)+'.obj'and row['depfile']['path']=='object'+str(index)+'.d',
             'det_fixed_output_path')
        product=probe_output(root,row['output'],common)
        need(len(product)>=20 and struct.unpack_from('<H',product)[0]==0xaa64,'det_fixed_coff');products.append(product)
        target,deps=make_dependencies(probe_output(root,row['depfile'],common,65536))
        need(target==expected[expected.index('-o')+1],'det_fixed_dependency_target')
        paths=sorted({str((Path(old['cwd'])/name).resolve(strict=True))for name in deps})
        same(paths,sorted(item['path']for item in prior['dependency_closure'][old['side']]['wine_object']['before']),
             'det_fixed_dependency_set')
    need(len(products[0])==len(products[1])and products[0][:4]==products[1][:4]
         and products[0][8:]==products[1][8:],'det_fixed_non_timestamp_difference')
    need(value['objects_complete_bytes_equal']is (products[0]==products[1]),'det_fixed_object_comparison')
    row=commands[2];common.fields(row,['id','argv','cwd','environment','exit_code','elapsed_ms','stdout','stderr'])
    expected=[('--prefix='+str(root/'wine/install'))if arg.startswith('--prefix=')else arg for arg in original['argv']]
    same(row['argv'],expected,'det_fixed_configure_recipe')
    expected_env=dict(original['environment']);expected_env.update(TMPDIR=str(root/'tmp'),CROSSCFLAGS=' '.join(cross_flags()))
    same(row['environment'],expected_env,'det_fixed_configure_environment')
    need(row['id']=='wine.configure'and row['cwd']==str(root/'wine/objects'),'det_fixed_configure_scope')
    replay_probe_streams(root,row,common)
    binding_path,binding_raw=ref_file(binding_ref,common,32*1024**2)
    binding=common.decode_json(binding_raw,max_bytes=32*1024**2,max_nodes=1000000)
    fixed_post_binding(binding,value,control_ref,root,common)
    # Both records and their exact producers remain unchanged after replay.
    need(ref_file(control_ref,common,16*1024**2)[1]==raw and ref_file(binding_ref,common,32*1024**2)[1]==binding_raw,
         'det_fixed_records_changed')
    return value


def qualification(ref,original,common):
    _,raw=ref_file(ref,common);value=common.decode_json(raw)
    need(type(value)is dict and set(value)==QUAL_FIELDS and type(value['schema_version'])is int
         and value['schema_version']==3 and value['record_kind']=='dxmt_deterministic_input_qualification'
         and value['scope']=='compiler_source_and_resource_bytes_only'and value['source_date_epoch']=='0'
         and value['native_engine_execution_performed']is False and value['gpu_execution_performed']is False,
         'det_qualification_record')
    same(value['original_ref'],{'path':str(original/'build.json'),'sha256':common.sha256(original/'build.json')},'det_qualification_original')
    resource=resource_sidecar(value['resource_ref'],common)
    metal_control(value['metal_control_ref'],list(metal.SOURCES),original,resource,value['metal_predecessor_refs'],common)
    prior=wine_control(value['wine_control_ref'],original,common)
    fixed_compilation_directory(value['wine_compilation_directory_ref'],value['wine_compilation_directory_binding_ref'],
        value['wine_control_ref'],prior,common)
    return value,resource


def helpers(capture):
    names={'common':'common','stage3':'build','native':'build_native','builder':'pairing_build',
           'reader':'pairing_check','source':'pairing_source','wine_reuse':'pairing_reuse',
           'monitor':'pairing_monitor','tools':'tools'}
    return {key:capture.load('tools/dxmt/'+name+'.py')for key,name in names.items()}


def producer_values(h,capture,repo):
    inherited=h['stage3'].producers(repo)
    current={path:digest(reuse.read_file(repo,path))for path in h['builder'].PRODUCERS}
    current.update(capture.closure())
    origin=own_sources()
    current.update({path:row['sha256']for path,row in origin.items()})
    combined=dict(inherited)
    for path,sha in current.items():
        need(path not in combined or combined[path]==sha,'det_producer_conflict');combined[path]=sha
    return current,inherited,combined,origin


def producer_copies(root,value,h,capture,repo):
    current,inherited,combined,origin=producer_values(h,capture,repo)
    for name,expected in [('producers',current),('inherited_producers',inherited),
                         ('producer_files',combined),('constructor_sources',origin)]:
        same(value[name],expected,'det_'+name+'_changed')
    for path,sha in combined.items():
        need(digest(h['common'].read_relative(root,'producers/'+path))==sha,'det_producer_copy_changed')
    rows=h['tools'].files(root/'producers')
    need({row['path']for row in rows}==set(combined)and all(row['mode']==0o644 for row in rows),'det_producer_copy_set')


def input_configuration(root,invocation,makefile):
    raw=metal.read(root,makefile,64*1024**2)[0].decode()
    result={}
    for name in ['aarch64_CFLAGS','aarch64_CXXFLAGS']:
        matches=re.findall(r'^'+name+r' = (.*)$',raw,re.M)
        need(len(matches)==1,'det_config_cross_flags_missing')
        observed=shlex.split(matches[0])
        same(observed,cross_flags(),'det_config_cross_flags_changed')
        result[name]=observed
    return result


def wrapper(root,python,selected,spec_sha):
    # Preserve the exact original metallib branch. Only metal input transport
    # is changed; the adapter reconstructs each selected source's own flags.
    return ('#!/bin/sh\nset -eu\n'
      'test "$#" -ge 3 || exit 64\n'
      'test "$1" = "-sdk" && test "$2" = "macosx" || exit 64\n'
      'shift 2\ncase "$1" in\n'
      'metal) shift; exec /usr/bin/arch -arm64 '+shlex.quote(python)+' -B '+
       '"$(dirname \"$0\")/metal_stdin.py" --spec "$(dirname \"$(dirname \"$0\")\")/shader-inputs.json" --spec-sha '+shlex.quote(spec_sha)+' -- "$@";;\n'
      'metallib) shift; exec /usr/bin/arch -arm64 '+shlex.quote(selected['metallib']['path'])+' "$@";;\n'
      '*) exit 64;;\nesac\n').encode()


def generated_inputs(h,root,inputs,prepared,tools_root,tool_record,cap,roots,env,qualification_value):
    selected=cap['selected'];c=h['common']
    tool=external_fact(selected['metal']['path'],c)
    adapter=reuse.read_file(HERE,'metal_stdin.py')
    template=dict(env)
    need(env['TMPDIR']==str(root/'tmp')and env['PATH'].startswith(str(root/'bin')+':'),'det_environment_slots')
    template['TMPDIR']=metal.ROOT_TOKEN+'/tmp'
    template['PATH']=metal.ROOT_TOKEN+'/bin'+env['PATH'][len(str(root/'bin')):]
    spec={'schema_version':1,'record_kind':'dxmt_shader_stdin_spec','root':metal.ROOT_TOKEN,
        'metal':tool,'environment':template,'adapter_sha256':digest(adapter),
        'resources_ref':qualification_value['resource_ref']}
    generated=h['stage3'].generated_bytes(inputs,prepared,tools_root,tool_record,cap,roots)
    generated['bin/xcrun']=(wrapper(root,tool_record['native_tools']['python']['path'],selected,digest(encoded(spec))),0o755)
    generated['bin/metal_stdin.py']=(adapter,0o644)
    generated['shader-inputs.json']=(encoded(spec),0o644)
    return generated,metal.materialize(spec,root)


def shader_dependencies(root,selected,spec,common):
    target,deps=make_dependencies(common.read_relative(root,selected['dependencies'],65536))
    resources_path,_=ref_file(spec['resources_ref'],common,32*1024**2)
    resource=common.decode_json(common.read_relative(resources_path.parent,resources_path.name,32*1024**2),
        max_bytes=32*1024**2,max_nodes=1000000)
    resource_root=Path(resource['root'])
    source=selected['source'].removeprefix('source/')
    # The exact module map path derives from the admitted compiler dependency
    # record, not a hardcoded toolchain version: there is exactly one selected
    # metal/module.modulemap in the complete resource inventory.
    candidates=[row['path']for row in resource['files']if row['path'].endswith('/include/metal/module.modulemap')]
    need(len(candidates)==1,'det_module_map_ambiguous')
    expected=[str(resource_root/candidates[0])]
    if selected['quoted_header']:expected.append(str(root/selected['quoted_header']))
    same((target,deps),(str(root/selected['output']),expected),'det_shader_dependency_set')
    need(source in metal.SOURCES,'det_shader_dependency_source')
    return deps


def shader_records(root,spec,common):
    records=[];wanted=set()
    for source in metal.SOURCES:
        args=['-o',metal.OUTPUTS[source],'-c','../source/'+source,*metal.EXTRAS[source]]
        selected=metal.plan(spec,args);ident=selected['id'];path='shader-evidence/'+ident+'.json'
        value=common.decode_json(common.read_relative(root,path))
        need(type(value)is dict and set(value)==metal.COMMAND_FIELDS,'det_shader_record_fields')
        raw,pin=metal.checked_source(root,selected['source'],source)
        header=None
        if selected['quoted_header']:_,header=metal.checked_source(root,selected['quoted_header'],metal.HEADER)
        expected={'schema_version':1,'record_kind':'dxmt_shader_stdin_command','id':ident,
            'original_argv':args,'argv':selected['argv'],'cwd':selected['cwd'],
            'environment':spec['environment'],'stdin':pin,'quoted_header':header,'tool':spec['metal'],
            'resources_ref':spec['resources_ref'],'logs':{},
            'output':metal.fact(root,selected['output'],16*1024**2),
            'dependencies':metal.fact(root,selected['dependencies'],65536),
            'elapsed_ms':value['elapsed_ms'],'exit_code':0,'process_started':True,
            'compilation_attempted':True,'passed':True,'bound_outcome':None,
            'native_engine_execution_performed':False,'gpu_execution_performed':False}
        need(type(value['elapsed_ms'])is int and 0<=value['elapsed_ms']<=metal.TIMEOUT*1000+10000,
             'det_shader_elapsed')
        for stream in ['stdout','stderr']:
            log='shader-evidence/'+ident+'.'+stream
            expected['logs'][stream]=metal.fact(root,log,metal.MAX_LOG)
            wanted.add(log.removeprefix('shader-evidence/'))
        same(value,expected,'det_shader_command_changed')
        shader_dependencies(root,selected,spec,common)
        wanted.update([ident+'.json',ident+'.d'])
        records.append({'path':path,'sha256':digest(common.read_relative(root,path))})
    need({path.name for path in(root/'shader-evidence').iterdir()}==wanted,'det_shader_evidence_set')
    return records


def fixture_recipe(root,wine_tools):
    return [str(wine_tools/'llvm-mingw/bin/clang'),'--target=aarch64-w64-windows-gnu',
        '-std=c11','-Wall','-Wextra','-Werror','-O1','-fno-builtin','-nostdlib','-Wl,-e,mainCRTStartup',
        str(root/'inputs/tests/dxmt/pairing/pairing_pe.c'),'-lkernel32','-luser32','-o',
        str(root/'fixtures/pear-metal-pairing-arm64.exe')]


def pe_epoch(pe):
    need(pe.u('I',pe.pe+8)==0,'det_final_pe_epoch')
    rva,size=pe.dirs[6]
    if not rva and not size:return
    need(rva>0 and 0<size<=28*1024 and size%28==0,'det_debug_directory_shape')
    start=pe.offset(rva,size)
    need(all(pe.u('I',start+offset+4)==0 for offset in range(0,size,28)),'det_final_debug_epoch')


def final_epochs(root,h):
    inspector=h['stage3'].inspector();PE,_=inspector.pe_readers()
    paths=[h['reader'].REBUILT_PE,h['reader'].FIXTURE_PE]
    for name,target in h['stage3'].PE_TARGETS.items():
        paths.extend(['dxmt/compiler/'+name,'dxmt/objects/'+target,'dxmt/install/aarch64-windows/'+name])
    for path in paths:pe_epoch(PE(h['common'].read_relative(root,path,64*1024**2)))


def prepared_values(h,prior,repo):
    c,s,t,n=h['common'],h['stage3'],h['tools'],h['native']
    inputs,config,lock=s.input_values(prior['refs'],repo)
    _,roots,role_ref=s.selector(prior['wine_roles_ref']['path'],repo)
    prepared=s.verify_prepared(c.owned_directory(prior['prepared_ref']['path'],repo),repo)
    tool_root=c.owned_directory(prior['tools_ref']['path'],repo);tool_record=t.verify_tools(tool_root,repo)
    native=n.verify_shader_build(c.owned_directory(prior['native_ref']['path'],repo),repo)
    cap=c.decode_json(c.read_relative(c.owned_directory(native['capabilities_ref']['path'],repo),'capabilities.json'))
    return inputs,config,lock,roots,role_ref,prepared,tool_root,tool_record,native,cap


def constructor_record(value,reader):
    need(type(value)is dict and set(value)==set(reader.BUILD_FIELDS)|set(ADDITIONS),'det_build_field_set')
    need(type(value['schema_version'])is int and value['schema_version']==1 and value['record_kind']==KIND
         and value['scope']==SCOPE and value['passed']is True
         and all(value[name]is False for name in reader.RUNTIME_FLAGS),'det_build_scope')
    return value


def qualification_values(ref,h,repo):
    c=h['common'];_,raw=ref_file(ref,c);base=c.decode_json(raw)
    original_path,original_raw=ref_file(base['original_ref'],c)
    need(original_path.name=='build.json','det_original_receipt_role')
    original=c.owned_directory(original_path.parent,repo)
    need(digest(original_raw)==base['original_ref']['sha256'],'det_original_changed')
    original_value=h['reader'].verify_build(original,repo)
    value,resource=qualification(ref,original,c)
    return value,resource,original_value


def verify_build(root,repo):
    """Independent recipe/source/tool/output replay, with no native tool calls."""
    with reuse.legacy(repo)as capture:
        h=helpers(capture);c=h['common'];s=h['stage3'];reader=h['reader'];b=h['builder']
        root=c.owned_directory(root,repo);need(not(root/'failed.json').exists(),'det_failed_build')
        value=constructor_record(reader.decode_pair_build(c.read_relative(root,'build.json')),reader)
        producer_copies(root,value,h,capture,repo);reader.fixture_copies(root,value,repo)
        prior_root=c.owned_directory(value['prior_artifact']['path'],repo)
        same(value['prior_artifact'],s.reference(prior_root,'build.json'),'det_prior_changed')
        prior=s.verify_build(prior_root,repo)
        inputs,_,lock,roots,role_ref,prepared,tool_root,tool_record,native,cap=prepared_values(h,prior,repo)
        same(value['role_reference'],role_ref,'det_role_changed')
        q,resource,original=qualification_values(value['qualification_ref'],h,repo)
        same(original['prior_artifact'],value['prior_artifact'],'det_original_prior_mixed')
        wine_build=b.source_baseline(roots['native']);wine_lock,wine_config=reader.wine_inputs(wine_build,repo)
        wine_tools=c.real_directory(wine_build['tools_root'])
        same(value['wine_tools_ref'],h['wine_reuse'].verify_wine_tools(roots['native'],wine_build,wine_lock),'det_wine_tool_ref')
        need(value['wine_tools_ref']['path']==str(wine_tools),'det_wine_tool_path')
        series=c.read_relative(repo,h['source'].SERIES)
        need(digest(series)==value['series_sha256'],'det_series_changed')
        supplemental,changes=h['source'].validate_series(c.decode_json(series),repo)
        same(value['supplemental_inputs'],supplemental,'det_supplemental_changed')
        need(set(value['source'])=={'wine','dxmt'},'det_source_set')
        for component,baseline in [('wine',roots['native']/'source'),('dxmt',prior_root/'source')]:
            reader.source_projection(root,component,baseline,value['source'][component],changes[component])
        same(value['native_resolved_tools'],reader.external_native_tools(wine_lock),'det_native_tools_changed')
        invocation,tool_alias=reader.alias_paths(root,value['path_aliases'],wine_tools)
        wine_config['_native_tools']=wine_lock['native_tools']
        wine_env,env=environments(b.wine_environment(invocation,wine_build,wine_lock,tool_alias),
            s.environment(root/'dxmt',tool_root,tool_record),root,invocation)
        same(value['wine_environment'],wine_env,'det_wine_environment_changed')
        same(value['dxmt_environment'],env,'det_dxmt_environment_changed')
        same(value['recipe_policy'],policy(root,invocation),'det_recipe_policy_changed')
        generated,spec=generated_inputs(h,root/'dxmt',inputs,prepared,tool_root,tool_record,cap,roots,env,q)
        same(value['generated_inputs'],s.generated_facts(root/'dxmt',generated),'det_generated_changed')
        same(value['shader_spec_ref'],{'path':'dxmt/shader-inputs.json','sha256':digest(generated['shader-inputs.json'][0])},'det_spec_ref_changed')
        same(value['shader_commands'],shader_records(root/'dxmt',spec,c),'det_shader_record_refs')
        p=value['policy']
        same(p,h['native'].storage_policy(p['jobs'],p['growth_ceiling_bytes'],p['reserve_free_bytes']),'det_storage_policy')
        need(p['jobs']==2 and p['growth_ceiling_bytes']<=8*1024**3 and p['reserve_free_bytes']>=4*1024**3,'det_storage_scope')
        recipes={name:(args,cwd,wine_env,1800)for name,(args,cwd)in b.native_recipe(invocation,wine_build,wine_config,tool_alias).items()}
        recipes['fixture.compile']=(fixture_recipe(root,wine_tools),root,wine_env,60)
        for name,args in s.recipe(root/'dxmt',tool_root,tool_record,Path(native['llvm_ref']['path']),2).items():
            recipes[name]=(args,root,env,1800)
        reader.command_rows(root,value['commands'],recipes,p)
        variant=next(row for row in wine_config['variants']if row['id']=='arm64')
        actual=b.configuration_reader(wine_build)(root/'wine/objects/Makefile',variant,'page-wx',
            native_architecture_policy=True,source_policy='stable_relative_v1')
        same(value['wine_configuration'],actual,'det_configuration_changed')
        input_configuration(root,invocation,'wine/objects/Makefile')
        same(value['wine_configuration_files'],{name:c.sha256(root/'wine/objects'/name)
            for name in ['Makefile','config.log','include/config.h']},'det_configuration_receipts_changed')
        same(value['artifacts'],b.artifact_rows(root),'det_artifact_rows_changed')
        final_epochs(root,h)
        _,layout=s.role_layout(roots,inputs,lock)
        reader.inspect_pair(root,value,repo,layout)
        h['monitor'].directory_usage(root)
        return value


def construct(args,repo):
    """Root-run compiler construction. Merely importing never starts a tool."""
    with reuse.legacy(repo)as capture:
        h=helpers(capture);c,s,b,t=h['common'],h['stage3'],h['builder'],h['tools']
        prior_root=c.owned_directory(args.artifact,repo);prior=s.verify_build(prior_root,repo)
        inputs,_,lock,roots,role_ref,prepared,tool_root,tool_record,native,cap=prepared_values(h,prior,repo)
        qref={'path':str(Path(args.qualification).absolute()),'sha256':c.sha256(Path(args.qualification))}
        q,resources,original=qualification_values(qref,h,repo)
        same(original['prior_artifact'],s.reference(prior_root,'build.json'),'det_original_prior_mixed')
        wine_build=b.source_baseline(roots['native'])
        raw=c.read_relative(repo,h['source'].SERIES);supplemental,changes=h['source'].validate_series(c.decode_json(raw),repo)
        storage=h['native'].storage_policy(2,args.max_growth_bytes,args.reserve_free_bytes)
        need(storage['growth_ceiling_bytes']<=8*1024**3 and storage['reserve_free_bytes']>=4*1024**3,'det_storage_scope')
        need(shutil.disk_usage(repo).free>=storage['growth_ceiling_bytes']+storage['reserve_free_bytes'],'det_storage_admission')
        current,inherited,combined,origin=producer_values(h,capture,repo)
        root=c.output_directory(args.output,repo)
        value={'schema_version':1,'record_kind':KIND,'scope':SCOPE,'prior_artifact':s.reference(prior_root,'build.json'),
            'series_sha256':digest(raw),'supplemental_inputs':supplemental,'producers':current,'inherited_producers':inherited,
            'producer_files':combined,'constructor_sources':origin,'role_reference':role_ref,'policy':storage,
            'qualification_ref':qref,'source':{},'commands':[],'artifacts':[],'passed':False,
            'pairing_verified':False,'native_execution':False,'hybrid_execution':False,'translated_guest_execution':False,
            'game_qualified':False,'runtime_eligible':False}
        phase='source'
        try:
            for path,sha in combined.items():
                contents=reuse.read_file(HERE,OWN_FILES[path])if path in OWN_FILES else c.read_relative(repo,path)
                need(digest(contents)==sha,'det_producer_snapshot_changed');s.write_bytes(root,'producers/'+path,contents)
            for name in ['wine/objects','dxmt','tmp','fixtures']:(root/name).mkdir(parents=True,exist_ok=True)
            for component,baseline in [('wine',roots['native']/'source'),('dxmt',prior_root/'source')]:
                before,after=h['source'].project(baseline,root/component/'source',*changes[component])
                value['source'][component]={'baseline':str(baseline),'before_files':before,'after_files':after}
            wine_lock,wine_config=h['reader'].wine_inputs(wine_build,repo)
            phase='wine.tools.verify';value['wine_tools_ref']=h['wine_reuse'].verify_wine_tools(roots['native'],wine_build,wine_lock)
            wine_tools=c.real_directory(value['wine_tools_ref']['path']);wine_config['_native_tools']=wine_lock['native_tools']
            value['native_resolved_tools']=h['reader'].external_native_tools(wine_lock)
            holder=Path(tempfile.mkdtemp(prefix='pear-task7-pair-',dir='/private/tmp'));invocation=holder/'output';tool_alias=holder/'wine-tools'
            invocation.symlink_to(root,target_is_directory=True);tool_alias.symlink_to(wine_tools,target_is_directory=True)
            value['path_aliases']={'output':str(invocation),'tools':str(tool_alias),'holder':str(holder)}
            wine_env,env=environments(b.wine_environment(invocation,wine_build,wine_lock,tool_alias),
                s.environment(root/'dxmt',tool_root,tool_record),root,invocation)
            value['wine_environment']=wine_env;value['dxmt_environment']=env;value['recipe_policy']=policy(root,invocation)
            for ident,(argv,cwd)in b.native_recipe(invocation,wine_build,wine_config,tool_alias).items():
                phase=ident;h['monitor'].monitored_command(root,ident,argv,wine_env,storage,value['commands'],cwd=cwd,timeout=1800)
                if ident=='wine.configure':
                    variant=next(row for row in wine_config['variants']if row['id']=='arm64')
                    value['wine_configuration']=b.configuration_reader(wine_build)(root/'wine/objects/Makefile',variant,'page-wx',
                        native_architecture_policy=True,source_policy='stable_relative_v1')
                    input_configuration(root,invocation,'wine/objects/Makefile')
                    value['wine_configuration_files']={name:c.sha256(root/'wine/objects'/name)for name in ['Makefile','config.log','include/config.h']}
            value['fixture_sources']={name:digest(c.read_relative(repo,name))for name in h['reader'].FIXTURE_PATHS}
            for name,sha in value['fixture_sources'].items():
                contents=c.read_relative(repo,name);need(digest(contents)==sha,'det_fixture_source_changed');s.write_bytes(root,'inputs/'+name,contents)
            phase='fixture.compile';h['monitor'].monitored_command(root,phase,fixture_recipe(root,wine_tools),wine_env,storage,value['commands'],timeout=60)
            dxroot=root/'dxmt'
            for name in ['tmp','shader-cache','shader-evidence']:(dxroot/name).mkdir()
            _,layout=s.role_layout(roots,inputs,lock);s.copy_layout(dxroot,layout,roots)
            rebuilt=root/'wine/objects/dlls/winemac.drv/winemac.so';selected=dxroot/'wine-layout/lib/wine/aarch64-unix/winemac.so'
            shutil.copyfile(rebuilt,selected);selected.chmod(rebuilt.stat().st_mode&0o777)
            value['wine_layout']=[]
            for row in layout:
                if row['path']=='wine-layout/lib/wine/aarch64-unix/winemac.so':
                    value['wine_layout'].append({'path':row['path'],'sha256':c.sha256(selected),'size_bytes':selected.stat().st_size,
                        'mode':selected.stat().st_mode&0o777,'origin_role':'rebuilt-native','origin_path':h['reader'].REBUILT_DRIVER})
                else:value['wine_layout'].append(row)
            s.check_layout(dxroot,value['wine_layout'],value['wine_layout'])
            generated,spec=generated_inputs(h,dxroot,inputs,prepared,tool_root,tool_record,cap,roots,env,q)
            for name,(contents,mode)in generated.items():s.write_bytes(dxroot,name,contents,mode)
            value['generated_inputs']=s.generated_facts(dxroot,generated)
            value['shader_spec_ref']={'path':'dxmt/shader-inputs.json','sha256':digest(generated['shader-inputs.json'][0])}
            for ident,argv in s.recipe(dxroot,tool_root,tool_record,Path(native['llvm_ref']['path']),2).items():
                phase=ident
                if ident=='builtin.'+next(iter(s.PE_TARGETS)):
                    for name,target in s.PE_TARGETS.items():s.write_bytes(dxroot,'compiler/'+name,c.read_relative(dxroot,'objects/'+target,64*1024**2))
                h['monitor'].monitored_command(root,ident,argv,env,storage,value['commands'],timeout=1800)
                if ident=='dxmt.compile':value['shader_commands']=shader_records(dxroot,spec,c)
            value['artifacts']=b.artifact_rows(root)
            final_epochs(root,h)
            # Recheck every actual source/resource/control byte after compiler
            # work. Scope flags remain false even when all tools return zero.
            qualification_values(qref,h,repo)
            producer_copies(root,value,h,capture,repo)
            for name,sha in value['fixture_sources'].items():need(digest(c.read_relative(repo,name))==sha,'det_fixture_changed')
            need(digest(c.read_relative(repo,h['source'].SERIES))==value['series_sha256'],'det_series_changed')
            for component,baseline in [('wine',roots['native']/'source'),('dxmt',prior_root/'source')]:
                h['reader'].source_projection(root,component,baseline,value['source'][component],changes[component])
            value['passed']=True;c.write_new(root/'build.json',value);return value
        except BaseException as error:
            value.update(phase=phase,error=getattr(error,'code',type(error).__name__),passed=False)
            if isinstance(error,OSError):value['native_error']={'domain':'posix_errno','code':error.errno,'operation':phase}
            try:c.write_new(root/'failed.json',value)
            except BaseException as secondary:error.evidence_error={'type':type(secondary).__name__,'code':getattr(secondary,'errno',None)}
            raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',required=True)
    group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--construct',action='store_true');group.add_argument('--verify',action='store_true')
    parser.add_argument('--artifact');parser.add_argument('--qualification');parser.add_argument('--output',required=True)
    parser.add_argument('--max-growth-bytes',type=int);parser.add_argument('--reserve-free-bytes',type=int);parser.add_argument('--require-empty',action='store_true')
    args=parser.parse_args(argv)
    try:
        repo=Path(args.repo).resolve(strict=True)
        if args.construct:
            need(args.artifact and args.qualification and args.require_empty and args.max_growth_bytes is not None
                 and args.reserve_free_bytes is not None,'det_construct_arguments');construct(args,repo)
        else:verify_build(args.output,repo)
        print(encoded({'record_kind':KIND,'build_replayed':args.verify,'pair_constructed':True,
            'recipe':'source_bound_stdin_epoch_fixed_compilation_directory_v2','raw_reproduction_complete':False,
            'native_engine_execution_performed':False,'gpu_execution_performed':False,'game_qualified':False,
            'runtime_eligible':False}).decode(),end='');return 0
    except Exception as error:
        print(encoded({'record_kind':KIND,'error':getattr(error,'code',type(error).__name__),
            'pair_constructed':False,'raw_reproduction_complete':False,'runtime_eligible':False}).decode(),end='',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
