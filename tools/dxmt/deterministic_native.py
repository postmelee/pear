#!/usr/bin/env python3
"""Distinct source-bound native admission/run/review for deterministic products.

Only an orchestrator invokes signing/admission/finite execution. Independent
native evidence uses pure structural replay and an explicit immutable review.
No historical module, record, sys.path or short sys.modules alias is patched.
"""
from __future__ import annotations
import argparse
import ast
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
CONSTRUCTOR_PIN_SHA='de00f6306e49df551efab363f96751a9cdc897ddc12606e976f398c89eac9e2b'
PIN_SHA='b0240dff62d8b152ee40650ee3b363f6ed4a35b6a2f9a2176fa9050435e65ff4'
OWN={'tools/dxmt/deterministic_native.py':'deterministic_native.py',
     'tools/dxmt/native-pins.json':'native-pins.json',
     'tools/dxmt/constructor-pins.json':'constructor-pins.json'}
KIND_MAP={key:'dxmt_deterministic_'+key[len('dxmt_'):] for key in (
 'dxmt_pairing_authorization','dxmt_pairing_materialization','dxmt_pairing_signed_runtime',
 'dxmt_pairing_runtime','dxmt_pairing_runtime_failure','dxmt_pairing_admission',
 'dxmt_pairing_admission_failure','dxmt_pairing_case','dxmt_pairing_run','dxmt_pairing_run_failure',
 'dxmt_pairing_diagnostics_review','dxmt_pairing_native_evidence')}
SCOPE_MAP={'development_finite_native_metal_pairing':'development_finite_deterministic_native_metal_pairing',
 'finite_native_metal_pairing':'finite_deterministic_native_metal_pairing',
 'finite_native_metal_api_pairing':'finite_deterministic_native_metal_api_pairing'}
LITERALS={**KIND_MAP,**SCOPE_MAP}


class Error(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)
def need(value,code):
    if not value:raise Error(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def same(left,right,code):need(encoded(left)==encoded(right),code)


def selected_functions(raw,namespace,path):
    """Closed record-kind/scope derivation; every other AST node is preserved."""
    before=[node for node in ast.parse(raw).body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
            and node.name!='main']
    need(before and all(isinstance(node,ast.FunctionDef) for node in before),'native_function_set')
    counts={};nodes=copy.deepcopy(before)
    class Literals(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value)is str and node.value in LITERALS:
                old=node.value;node.value=LITERALS[old];counts[old]=counts.get(old,0)+1
            return node
    nodes=[Literals().visit(node)for node in nodes]
    tree=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
    # Comparing the inverse transform protects statement/signature/decorator
    # identity in addition to the entire already-pinned predecessor source.
    restored=copy.deepcopy(nodes);inverse={v:k for k,v in LITERALS.items()}
    class Restore(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value)is str and node.value in inverse:node.value=inverse[node.value]
            return node
    restored=[Restore().visit(node)for node in restored]
    need(ast.dump(ast.Module(body=restored,type_ignores=[]),include_attributes=False)==
         ast.dump(ast.Module(body=before,type_ignores=[]),include_attributes=False),'native_function_semantics_changed')
    exec(compile(tree,path,'exec'),namespace)
    return {'source_sha256':digest(raw),'functions':[node.name for node in before],
            'before_ast_sha256':digest(ast.dump(ast.Module(body=before,type_ignores=[]),include_attributes=False).encode()),
            'after_ast_sha256':digest(ast.dump(tree,include_attributes=False).encode()),
            'literal_changes':{key:{'replacement':LITERALS[key],'count':count}for key,count in sorted(counts.items())}},ast.unparse(tree).encode()


def bounded_source(root,leaf):
    need(type(leaf)is str and leaf and '/'not in leaf and leaf not in ('.','..'),'native_source_leaf')
    root=Path(root).absolute();need('..'not in root.parts,'native_source_root')
    directory=os.open(root.anchor,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in root.parts[1:]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=child
        fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory)
        try:
            before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_size<=2**20,'native_source_bound')
            raw=bytearray()
            while len(raw)<=2**20:
                chunk=os.read(fd,min(65536,2**20+1-len(raw)))
                if not chunk:break
                raw.extend(chunk)
            after=os.fstat(fd)
            identity=lambda row:(row.st_dev,row.st_ino,row.st_mode,row.st_size,row.st_mtime_ns,row.st_ctime_ns)
            need(identity(before)==identity(after)and len(raw)==before.st_size,'native_source_changed')
            return bytes(raw)
        finally:os.close(fd)
    finally:os.close(directory)


def read_own():
    result={}
    for logical,leaf in OWN.items():
        raw=bounded_source(HERE,leaf)
        result[logical]={'path':str(HERE/leaf),'sha256':digest(raw),'raw':raw}
    return result


class Adapter:
    def __init__(self,repo,constructor_root,executed_native_sha=None):
        captured=bounded_source(HERE,'deterministic_native.py')
        self.executed_native_sha=digest(captured) if executed_native_sha is None else executed_native_sha
        need(type(self.executed_native_sha)is str and len(self.executed_native_sha)==64
             and digest(captured)==self.executed_native_sha,'native_executed_source_changed')
        self.repo=Path(repo).resolve(strict=True);self.constructor_root=Path(constructor_root).resolve(strict=True)
        # Admit all exact constructor sources before any source execution.
        pin_raw=bounded_source(HERE,'constructor-pins.json')
        need(digest(pin_raw)==CONSTRUCTOR_PIN_SHA,'native_constructor_pins_changed')
        pin=json.loads(pin_raw)
        need(set(pin)=={'schema_version','record_kind','files'}and type(pin['schema_version'])is int
             and pin['schema_version']==1 and pin['record_kind']=='dxmt_deterministic_constructor_sources'
             and set(pin['files'])=={'deterministic_pair.py','deterministic_reuse.py','metal_stdin.py','reuse-pins.json'},
             'native_constructor_pin_set')
        constructor_raw={leaf:bounded_source(self.constructor_root,leaf)for leaf in pin['files']}
        need(all(digest(constructor_raw[leaf])==expected for leaf,expected in pin['files'].items()),
             'native_constructor_source_changed')
        self.constructor_pins=pin['files']
        spec=importlib.util.spec_from_file_location('_pear_deterministic_native_constructor',self.constructor_root/'deterministic_pair.py')
        self.pair=importlib.util.module_from_spec(spec)
        raw=constructor_raw['deterministic_pair.py']
        modules={}
        def frozen_local(name):
            need(name in ('deterministic_reuse','metal_stdin'),'native_constructor_helper')
            if name not in modules:
                path=self.constructor_root/(name+'.py')
                helper_spec=importlib.util.spec_from_file_location('_pear_deterministic_native_'+name,path)
                module=importlib.util.module_from_spec(helper_spec)
                exec(compile(constructor_raw[name+'.py'],str(path),'exec'),vars(module));modules[name]=module
            return modules[name]
        tree=ast.parse(raw)
        local_nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef)and node.name=='local']
        need(len(local_nodes)==1 and not local_nodes[0].decorator_list,'native_constructor_loader_source')
        tree.body=[node for node in tree.body if node is not local_nodes[0]]
        self.pair.local=frozen_local
        exec(compile(tree,str(self.constructor_root/'deterministic_pair.py'),'exec'),vars(self.pair))
        self.capture=self.pair.reuse.Captured(self.repo,self.constructor_root)
        try:
            pin_raw=self.pair.reuse.read_file(HERE,'native-pins.json')
            need(digest(pin_raw)==PIN_SHA,'native_pin_manifest_changed')
            pins=json.loads(pin_raw)
            need(set(pins)=={'schema_version','record_kind','files'} and type(pins['schema_version'])is int
                 and pins['schema_version']==1 and pins['record_kind']=='dxmt_deterministic_native_predecessor_pins',
                 'native_pin_manifest')
            for path,pin in pins['files'].items():
                need(path not in self.capture.raw,'native_predecessor_overlap')
                value=self.pair.reuse.read_file(self.repo,path)
                need(digest(value)==pin,'native_predecessor_changed')
                self.capture.raw[path]=value;self.capture.pins[path]=pin
            self.own=read_own()
            need(self.own['tools/dxmt/deterministic_native.py']['sha256']==self.executed_native_sha,
                 'native_executed_source_changed')
            self.constructor_sources=self.pair.own_sources()
            # Original supervisor short alias assignments are isolated too.
            self.capture.module_view.LEGACY=dict(self.capture.module_view.LEGACY,
                **{name:'tools/wine/'+name+'.py' for name in
                    ('modules','abi_review','dynamic_evidence','exception_evidence','run_fixtures','api_runner')})
            self.common=self.capture.load('tools/dxmt/common.py')
            self.runtime,self.runtime_proof,_=self.derive('tools/dxmt/pairing_runtime.py')
            self.runner,self.runner_proof,self.runner_raw=self.derive('tools/dxmt/run_pairing.py')
            self.evidence,self.evidence_proof,_=self.derive('tools/dxmt/pairing_evidence.py')
            self.gates()
        except BaseException:
            self.capture.close();raise
    def close(self):self.capture.close()
    def derive(self,path):
        original=self.capture.load(path);namespace=dict(vars(original))
        facts,derived=selected_functions(self.capture.raw[path],namespace,path)
        if 'SCOPE'in namespace:namespace['SCOPE']=SCOPE_MAP.get(namespace['SCOPE'],namespace['SCOPE'])
        # Module attributes are a view of one new globals namespace. Function
        # globals remain that same dictionary, not the historical module's dict.
        module=SimpleNamespace(**namespace);module.namespace=namespace
        return module,facts,derived
    def source_read(self,root,path,limit=8*1024**2):
        if Path(root)==self.repo:
            if path in self.own:
                current=read_own()[path];same({key:current[key]for key in ('path','sha256')},
                    {key:self.own[path][key]for key in ('path','sha256')},'native_own_source_changed')
                need(len(current['raw'])<=limit,'native_source_bound');return current['raw']
            if path in self.constructor_sources:
                row=self.constructor_sources[path];p=Path(row['path'])
                raw=self.pair.reuse.read_file(p.parent,p.name)
                need(digest(raw)==row['sha256']and len(raw)<=limit,'native_constructor_changed');return raw
        return self.common.read_relative(root,path,limit)
    def producers(self,repo=None):
        need(repo is None or Path(repo)==self.repo,'native_repository')
        need(all(digest(bounded_source(self.constructor_root,leaf))==expected
                 for leaf,expected in self.constructor_pins.items()),'native_constructor_source_changed')
        values=self.capture.closure()
        values.update({path:row['sha256']for path,row in self.constructor_sources.items()})
        values.update({path:row['sha256']for path,row in self.own.items()})
        need(values['tools/dxmt/deterministic_native.py']==self.executed_native_sha,'native_executed_source_changed')
        # Current bytes must be identical before/after every structural/live gate.
        for path,pin in values.items():need(digest(self.source_read(self.repo,path))==pin,'native_producer_changed')
        return dict(sorted(values.items()))
    def descriptor(self,operation):
        need(operation in ('runtime','run'),'native_operation')
        return {'schema_version':1,'record_kind':'dxmt_deterministic_native_adapter','operation':operation,
            'source_gates':{'build_kind':self.pair.KIND,'original_records_accepted':False,
                'fresh_39_case_native_execution_required':True,'diagnostics_review_required':True},
            'predecessor_functions':{'runtime':self.runtime_proof,'run':self.runner_proof,'evidence':self.evidence_proof},
            'constructor_sources':self.constructor_sources,
            'constructor_loading':{'source_sha256':self.constructor_pins['deterministic_pair.py'],
                'local_loader':'closed_preverified_helper_bytes','record_kind_changed':False},
            'adapter_sources':{path:{key:row[key]for key in ('path','sha256')}for path,row in self.own.items()},
            'native_loading':{'source_sha256':self.executed_native_sha,'current_source_match_required':True},
            'producers':self.producers(),'runtime_eligible':False,'game_qualified':False,'distribution_qualified':False}
    def descriptor_check(self,root,operation):
        value=self.common.decode_json(self.common.read_relative(root,'adapter.json'))
        same(value,self.descriptor(operation),'native_adapter_changed')
    def output(self,path,operation,repo=None):
        root=self.common.output_directory(path,self.repo)
        self.common.write_new(root/'adapter.json',self.descriptor(operation));return root
    def local_source(self,path,alias,raw=None):
        key=self.capture.source_path(path)
        need(key in self.capture.raw,'native_local_source')
        if raw is not None:need(raw==self.capture.raw[key],'native_local_capture_changed')
        module=self.capture.load(key)
        # The old supervisor asks for its declared short alias after local().
        self.capture.module_view[alias]=module
        return module
    def gates(self):
        reader=self.capture.load('tools/dxmt/pairing_check.py')
        new_reader=SimpleNamespace(**dict(vars(reader),verify_build=lambda root,repo=self.repo:
                                      self.pair.verify_build(root,repo=repo)))
        def set_values(module,**values):
            module.namespace.update(values)
            for key,value in values.items():setattr(module,key,value)
        runtime_body=self.runtime.verify_structural
        def structural(root,repo=self.repo):
            self.descriptor_check(root,'runtime')
            result=runtime_body(root,repo=repo)
            need(result[0]['record_kind']==KIND_MAP['dxmt_pairing_runtime'],'native_runtime_kind')
            self.producers(repo);return result
        set_values(self.runtime,REPO=self.repo,producers=self.producers,read_relative=self.source_read,
                   pairing_check=new_reader,verify_structural=structural,
                   output_directory=lambda path,repo=self.repo:self.output(path,'runtime',repo))
        run_body=self.runner.verify_run
        def replay(root,repo=self.repo):
            self.descriptor_check(root,'run');result=run_body(root,repo=repo)
            self.producers(repo);return result
        def runtime_values(root,repo=self.repo):
            value=self.runtime.verify_runtime(root,repo=repo)
            need(value['record_kind']==KIND_MAP['dxmt_pairing_runtime'] and
                 value['runtime_eligible']is False and value['game_qualified']is False,'native_runtime_scope')
            return value
        set_values(self.runner,REPO=self.repo,producers=self.producers,read_relative=self.source_read,
            local=self.local_source,runtime_values=runtime_values,verify_run=replay,
            output_directory=lambda path,repo=self.repo:self.output(path,'run',repo))
        def adapters(repo=self.repo):
            need(Path(repo)==self.repo,'native_repository')
            return self.runner,self.runtime,self.runner_raw,self.producers(repo)
        # Original evidence pure_replay selects the derived verify_run source and
        # replaces only live runtime_values with exact structural replay, retaining
        # every physical-lifetime/event/permission/source/raw-log check.
        pure_body=self.evidence.pure_replay
        def pure(root,repo,runner,runtime,raw_run):
            self.descriptor_check(root,'run')
            return pure_body(root,repo,runner,runtime,raw_run)
        set_values(self.evidence,REPO=self.repo,read_relative=self.source_read,adapters=adapters,
            producer_hashes=lambda repo,runner,runtime:self.producers(repo),pure_replay=pure)
    def prepare(self,build,profile,output):
        return self.runtime.prepare(build,profile,output,repo=self.repo)
    def structural(self,root):return self.runtime.verify_structural(root,repo=self.repo)
    def admit(self,root):return self.runtime.verify_runtime(root,repo=self.repo)
    def run(self,root,output):return self.runner.run(root,output,repo=self.repo)
    def verify_run(self,root):return self.runner.verify_run(root,repo=self.repo)
    def review_context(self,root):return self.evidence.review_context(root,repo=self.repo)
    def verify_evidence(self,root):
        value=self.evidence.verify_native_evidence(root,repo=self.repo)
        need(value['record_kind']==KIND_MAP['dxmt_pairing_native_evidence'],'native_evidence_kind')
        return value


@contextmanager
def adapter(repo,constructor_root,executed_native_sha=None):
    value=Adapter(repo,constructor_root,executed_native_sha)
    try:yield value
    finally:value.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True);parser.add_argument('--constructor-root',required=True)
    choice=parser.add_mutually_exclusive_group(required=True)
    for action in ('prepare','structural','admit','run','verify-run','review-context','evidence'):
        choice.add_argument('--'+action,action='store_true')
    parser.add_argument('--build');parser.add_argument('--profile');parser.add_argument('--runtime')
    parser.add_argument('--output');parser.add_argument('--run-root');args=parser.parse_args(argv)
    try:
        with adapter(args.repo,args.constructor_root)as value:
            if args.prepare:
                need(args.build and args.profile and args.output,'native_prepare_arguments')
                result=value.prepare(args.build,args.profile,args.output)
            elif args.structural:result=value.structural(args.runtime)[0]
            elif args.admit:result=value.admit(args.runtime)
            elif args.run:result=value.run(args.runtime,args.output)
            elif args.verify_run:result=value.verify_run(args.run_root)
            elif args.review_context:result=value.review_context(args.run_root)[0]
            else:result=value.verify_evidence(args.run_root)
            print(encoded(result).decode(),end='');return 0
    except Exception as error:
        record={'passed':False,'runtime_eligible':False,'error':getattr(error,'code',type(error).__name__)}
        if isinstance(error,OSError):record['native_error']={'domain':'POSIX','code':error.errno}
        elif getattr(error,'native_error',None)is not None:record['native_error']=error.native_error
        print(encoded(record).decode(),end='',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
