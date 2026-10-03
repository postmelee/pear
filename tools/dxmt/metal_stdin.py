#!/usr/bin/env python3
"""Execute only the selected original shader recipes through bounded stdin.

Generated into an owned build by deterministic_pair. This is a build adapter,
not a GPU/runtime gate or a general xcrun replacement.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import time

SOURCES = {
 'src/airconv/shaders/air_msad.metal': ('bb1f622f63026a0154164ed385e91e9d759f5bada897e6b0a76ff7710bc5565d',1445),
 'src/airconv/shaders/air_samplepos.metal': ('f17da691bffe9d2ab60d20e137d3ee71c3cbade714de3f35c0ee827578f320b8',1259),
 'src/airconv/shaders/air_tessellation.metal': ('aa7b3e264bf91cd885b5981805878cadb3b1f9f587a5131940ae9ee669a0fbca',28303),
 'src/dxmt/dxmt_command.metal': ('8c07739065fd1b6c0b6d4aebc1e70473ec4918c540cb79f789db8ea113cf2ff0',20732)}
HEADER = 'src/dxmt/dxmt_command_constants.hpp'
HEADER_PIN = ('6145cddd7ea3885c1885f1920768c6843655ca178647924a527f91f717ac57d9',627)
EXTRAS = {name: [] if name.startswith('src/dxmt/') else ['-std=metal3.1','--target=air64-apple-macos14.0'] for name in SOURCES}
OUTPUTS = {name: ('src/dxmt/libdxmt.a.p/' if name.startswith('src/dxmt/') else
                 'src/airconv/darwin/libairconv.a.p/')+PurePosixPath(name).stem+'.air' for name in SOURCES}
SPEC_FIELDS = {'schema_version','record_kind','root','metal','environment','adapter_sha256','resources_ref'}
COMMAND_FIELDS = {'schema_version','record_kind','id','original_argv','argv','cwd','environment',
 'stdin','quoted_header','tool','resources_ref','logs','output','dependencies','elapsed_ms','exit_code',
 'process_started','compilation_attempted','passed','bound_outcome','native_engine_execution_performed','gpu_execution_performed'}
MAX_LOG = 1024**2
TIMEOUT = 600


class Error(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def need(ok,code):
    if not ok:raise Error(code)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


def relative(value):
    need(type(value)is str and not value.startswith('/')and '\\'not in value and '\x00'not in value
         and all(part not in('','.','..')for part in value.split('/')),'shader_path')
    return value.split('/')


def directory(value):
    path=Path(value).absolute();need('..'not in path.parts,'shader_root')
    current=Path(path.anchor)
    for part in path.parts[1:]:
        current/=part;need(stat.S_ISDIR(current.lstat().st_mode),'shader_directory_alias')
    return path


def read(root,path,limit=2**20):
    root=directory(root);parts=relative(path)
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child
        leaf=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            before=os.fstat(leaf);need(stat.S_ISREG(before.st_mode)and before.st_size<=limit,'shader_file_bound')
            raw=bytearray()
            while len(raw)<=limit:
                data=os.read(leaf,min(65536,limit+1-len(raw)))
                if not data:break
                raw.extend(data)
            after=os.fstat(leaf)
            identity=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
            need(identity(before)==identity(after)and len(raw)==before.st_size,'shader_file_changed')
            return bytes(raw),stat.S_IMODE(before.st_mode)
        finally:os.close(leaf)
    finally:os.close(fd)


def fact(root,path,limit=2**20):
    raw,mode=read(root,path,limit);return {'path':path,'sha256':digest(raw),'size_bytes':len(raw),'mode':mode}


def write_new(root,path,value):
    target=Path(root).joinpath(*relative(path));directory(target.parent)
    descriptor=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
    with os.fdopen(descriptor,'wb')as stream:stream.write(encoded(value))


ROOT_TOKEN='@OWNED_DXMT_ROOT@'


def materialize(value,root):
    root=directory(root)
    need(value['root']==ROOT_TOKEN,'shader_root_template')
    env=value['environment']
    need(type(env)is dict and all(type(k)is str and type(v)is str for k,v in env.items()),'shader_environment')
    need(env.get('TMPDIR')==ROOT_TOKEN+'/tmp'and env.get('PATH','').startswith(ROOT_TOKEN+'/bin:'),
         'shader_environment_template')
    need(all(ROOT_TOKEN not in v for k,v in env.items()if k not in ['TMPDIR','PATH'])
         and env['PATH'].count(ROOT_TOKEN)==1,'shader_environment_template_slots')
    actual=dict(env);actual['TMPDIR']=str(root/'tmp');actual['PATH']=str(root/'bin')+env['PATH'][len(ROOT_TOKEN+'/bin'):]
    return {**value,'root':str(root),'environment':actual}


def load_spec(path,expected_sha):
    path=Path(path);raw,_=read(path.parent,path.name)
    need(type(expected_sha)is str and len(expected_sha)==64 and all(c in '0123456789abcdef'for c in expected_sha)
         and digest(raw)==expected_sha,'shader_spec_digest')
    value=json.loads(raw)
    need(type(value)is dict and set(value)==SPEC_FIELDS and type(value['schema_version'])is int
         and value['schema_version']==1 and value['record_kind']=='dxmt_shader_stdin_spec','shader_spec')
    value=materialize(value,path.parent)
    root=directory(value['root']);need(path==root/'shader-inputs.json','shader_spec_role')
    need(type(value['environment'])is dict and all(type(k)is str and type(v)is str
         for k,v in value['environment'].items())and value['environment'].get('SOURCE_DATE_EPOCH')=='0','shader_environment')
    need(digest(read(root,'bin/metal_stdin.py')[0])==value['adapter_sha256'],'shader_adapter_changed')
    tool=value['metal'];need(type(tool)is dict and set(tool)=={'path','resolved_path','sha256','size_bytes','mode'},'shader_tool')
    declared=Path(tool['path']);resolved=declared.resolve(strict=True)
    need(str(resolved)==tool['resolved_path']and resolved.is_absolute(),'shader_tool_resolution')
    observed=fact(resolved.parent,resolved.name,64*1024**2)
    need({k:observed[k]for k in ['sha256','size_bytes','mode']}=={k:tool[k]for k in ['sha256','size_bytes','mode']},'shader_tool_changed')
    return value


def plan(spec,argv):
    need(type(argv)is list and all(type(x)is str for x in argv),'shader_argv')
    need(len(argv)in(4,6)and argv[0]=='-o'and argv[2]=='-c'and argv[3].startswith('../source/'),'shader_recipe')
    name=argv[3][len('../source/'):]
    need(name in SOURCES and argv[1]==OUTPUTS[name]and argv[4:]==EXTRAS[name],'shader_source_or_flags')
    root=Path(spec['root']);ident=PurePosixPath(name).stem
    source='source/'+name;dependency='shader-evidence/'+ident+'.d';output='objects/'+OUTPUTS[name]
    actual=['/usr/bin/arch','-arm64',spec['metal']['path'],'-o',str(root/output),'-c','-x','metal','-',*EXTRAS[name],
            '-fmodules-cache-path='+str(root/'shader-cache'),'-iquote',str((root/source).parent),
            '-MMD','-MF',str(root/dependency)]
    return {'id':ident,'original_argv':list(argv),'argv':actual,'cwd':str(root/'objects'),
            'source':source,'output':output,'dependencies':dependency,
            'quoted_header':('source/'+HEADER if name.startswith('src/dxmt/')else None)}


def checked_source(root,path,name):
    raw,mode=read(root,path,32768);need((digest(raw),len(raw))==(HEADER_PIN if name==HEADER else SOURCES[name]),'shader_source_changed')
    return raw,{'path':path,'sha256':digest(raw),'size_bytes':len(raw),'mode':mode}


def stop(process):
    errors=[];observed=None
    def capture(operation,error):
        row={'operation':operation,'error':getattr(error,'code',type(error).__name__)}
        if isinstance(error,OSError):row['native_error']={'domain':'posix_errno','code':error.errno}
        errors.append(row)
    try:running=process.poll()is None
    except BaseException as error:
        capture('poll',error);running=True
    if running:
        try:process.kill()
        except BaseException as error:capture('kill',error)
    try:
        result=process.wait(timeout=5)
        if type(result)is int:observed=result
        else:errors.append({'operation':'wait','error':'shader_cleanup_exit_unknown'})
    except BaseException as error:capture('wait',error)
    return observed,errors


def command(spec,argv):
    root=directory(spec['root']);selected=plan(spec,argv);ident=selected['id']
    directory(root/'objects');directory(root/'shader-evidence');directory(root/'shader-cache')
    need(Path.cwd()==root/'objects','shader_cwd')
    value={'schema_version':1,'record_kind':'dxmt_shader_stdin_command','id':ident,
           'original_argv':selected['original_argv'],'argv':selected['argv'],'cwd':selected['cwd'],
           'environment':spec['environment'],'stdin':None,'quoted_header':None,'tool':spec['metal'],
           'resources_ref':spec['resources_ref'],'logs':{},'output':None,'dependencies':None,
           'elapsed_ms':0,'exit_code':None,'process_started':False,'compilation_attempted':False,
           'passed':False,'bound_outcome':None,'native_engine_execution_performed':False,'gpu_execution_performed':False}
    process=None;start=time.monotonic();handles=[];primary=None
    try:
        source=selected['source'][len('source/'):]
        raw,value['stdin']=checked_source(root,selected['source'],source)
        if selected['quoted_header']:
            _,value['quoted_header']=checked_source(root,selected['quoted_header'],HEADER)
        for channel in ('stdout','stderr'):
            path='shader-evidence/'+ident+'.'+channel
            descriptor=os.open(root/path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
            handles.append(os.fdopen(descriptor,'wb'))
        value['compilation_attempted']=True
        process=subprocess.Popen(value['argv'],stdin=subprocess.PIPE,stdout=handles[0],stderr=handles[1],
                                 cwd=value['cwd'],env=value['environment'])
        value['process_started']=True
        input_pending=raw
        while True:
            if time.monotonic()-start>TIMEOUT:
                value['bound_outcome']='timeout';raise Error('shader_timeout')
            for handle in handles:
                need(os.fstat(handle.fileno()).st_size<=MAX_LOG,'shader_output_bound')
            try:
                process.communicate(input=input_pending,timeout=.1);break
            except subprocess.TimeoutExpired:
                input_pending=None
        value['exit_code']=process.returncode
        for handle in handles:need(os.fstat(handle.fileno()).st_size<=MAX_LOG,'shader_output_bound')
        need(type(process.returncode)is int and process.returncode==0,'shader_compiler_exit')
        need(read(root,selected['source'],32768)[0]==raw,'shader_source_changed')
        if selected['quoted_header']:checked_source(root,selected['quoted_header'],HEADER)
        value['output']=fact(root,selected['output'],16*1024**2)
        value['dependencies']=fact(root,selected['dependencies'],65536)
        value['passed']=True
    except BaseException as error:
        primary=error;value['error']=getattr(error,'code',type(error).__name__)
        if isinstance(error,OSError):value['native_error']={'domain':'posix_errno','code':error.errno}
        if process is not None:
            value['exit_code'],cleanup=stop(process)
            if cleanup:value['cleanup_errors']=cleanup
        if value['error']=='shader_output_bound':value['bound_outcome']='output_limit'
    finally:
        for index,handle in enumerate(handles):
            try:handle.close()
            except BaseException as error:
                row={'operation':'close_stream','channel':('stdout','stderr')[index],
                     'error':getattr(error,'code',type(error).__name__)}
                if isinstance(error,OSError):row['native_error']={'domain':'posix_errno','code':error.errno}
                value.setdefault('cleanup_errors',[]).append(row)
                if primary is None:
                    primary=error;value['passed']=False
                    value['error']=getattr(error,'code',type(error).__name__)
                    if isinstance(error,OSError):value['native_error']={'domain':'posix_errno','code':error.errno}
        value['elapsed_ms']=int((time.monotonic()-start)*1000)
        for channel in ('stdout','stderr'):
            path='shader-evidence/'+ident+'.'+channel
            if (root/path).exists():
                try:value['logs'][channel]=fact(root,path,MAX_LOG+16*1024**2)
                except Exception as error:
                    value.setdefault('evidence_errors',[]).append({'channel':channel,'error':getattr(error,'code',type(error).__name__),
                        'native_error':{'domain':'posix_errno','code':error.errno}if isinstance(error,OSError)else None})
                    if primary is None:primary=error;value['passed']=False
        path='shader-evidence/'+ident+('.json'if value['passed']else'.failed.json')
        try:write_new(root,path,value)
        except Exception as error:
            if primary is None:primary=error
            else:primary.evidence_error={'type':type(error).__name__,'code':getattr(error,'errno',None)}
    if primary is not None:raise primary
    return value


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--spec',required=True);parser.add_argument('--spec-sha',required=True);parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv)
    try:
        arguments=args.arguments[1:]if args.arguments[:1]==['--']else args.arguments
        command(load_spec(args.spec,args.spec_sha),arguments);return 0
    except Exception as error:
        sys.stderr.write('Deterministic shader construction failed: '+getattr(error,'code',type(error).__name__)+'\n');return 1


if __name__=='__main__':raise SystemExit(main())
