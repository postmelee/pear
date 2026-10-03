#!/usr/bin/env python3
"""Source-only exact projection of a reviewed FEX supplement graph.

Only fresh owned source files and fixed Git apply/check commands are permitted.
No compiler, module load, owner/VM operation or FEX initializer is called.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
if __package__:
    from . import memory_fex_check as evidence, memory_fex_build as constructor
    from .common import Error, need
else:
    # The sibling tools.py is a module, so remove this executable directory
    # before importing the repository's top-level tools namespace.
    script_directory=Path(__file__).resolve().parent
    sys.path[:]=[entry for entry in sys.path if Path(entry or os.getcwd()).resolve()!=script_directory]
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from tools.fex import memory_fex_check as evidence, memory_fex_build as constructor
    from tools.fex.common import Error, need

H=lambda raw:hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def canonical(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//'),'projection_input_absolute')
    evidence.relative(value[1:]);p=Path(value)
    need(str(p)==value and p.resolve(strict=True)==p,'projection_input_alias')
    return p

def git_environment(output):
    """Keep Git discovery inside the fresh canonical source-output directory.

    Git documents a colon-separated absolute-directory ceiling; source/ is
    below that ceiling, so an enclosing checkout cannot change apply scope.
    """
    output=Path(output)
    need(output.is_absolute() and output.is_dir() and output.resolve(strict=True)==output
         and ':' not in str(output),'projection_git_ceiling_directory')
    value={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','GIT_CONFIG_NOSYSTEM':'1',
           'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CEILING_DIRECTORIES':str(output)}
    if 'HOME' in os.environ:value['HOME']=os.environ['HOME']
    return value

def project(baseline,derivatives,output):
    baseline=canonical(os.fspath(baseline));derivatives=canonical(os.fspath(derivatives))
    output=Path(output)
    need(output.is_absolute() and not output.exists() and output.parent.resolve(strict=True)==output.parent,
         'projection_fresh_output')
    expected=evidence.selected_projection(baseline,derivatives)
    graph,graph_raw=evidence.record_bytes(derivatives,'derivatives.json')
    proposal,proposal_raw=evidence.record_bytes(derivatives,'final-source-proposal.json')
    need(proposal=={'schema_version':1,'record_kind':'fex_memory_source_proposal','scope':'source_only',
         'baseline_manifest_sha256':evidence.BASE_SOURCE_SHA,'derivatives_manifest_sha256':evidence.GRAPH_SHA,
         'files':expected['source_files'],'materialization_performed':False,'compilation_performed':False},
         'projection_expected_manifest')
    helper=evidence.source_helper_reference(str(Path(__file__).resolve()))
    git,mode=evidence.regular_bytes(Path('/usr/bin'),'git',32*1024**2,system_git=True)
    before=evidence.source_inventory(baseline/'source')
    output.mkdir(mode=0o700)
    commands=[]
    value={'schema_version':1,'record_kind':'fex_source_git_application_control','scope':'source_only','passed':False,
      'git_execution_performed':False,'compilation_performed':False,'module_initialization_performed':False,
      'owner_execution_performed':False,'guest_execution_performed':False,'stage3_complete':False,
      'layers':len(graph['layers']),'changed_paths':len(graph['final_changed_source_rows']),'new_files':len(graph['new_files']),
      'inputs':{'baseline_manifest_sha256':evidence.BASE_SOURCE_SHA,'derivatives_sha256':evidence.GRAPH_SHA,
        'expected_manifest_sha256':H(proposal_raw),'source_helper_sha256':helper['sha256']},
      'git':{'path':'/usr/bin/git','sha256':H(git),'size_bytes':len(git)},'commands':commands}
    try:
        constructor.copy_source(baseline/'source',output/'source',before)
        environment=git_environment(output)
        for layer in graph['layers']:
            evidence.graph_input(derivatives,layer['git_derivative'],2*1024**2)
            path=derivatives.joinpath(*evidence.relative(layer['git_derivative']['path']))
            for action in ('check','apply'):
                argv=['/usr/bin/git','apply',*(['--check'] if action=='check' else []),str(path)]
                started=time.monotonic();row={'layer':layer['order'],'action':action,'argv':argv,'cwd':str(output/'source'),
                    'attempted':True,'exit_code':None,'elapsed_ms':0}
                commands.append(row);value['git_execution_performed']=True
                try:child=subprocess.run(argv,cwd=output/'source',env=environment,stdin=subprocess.DEVNULL,
                      stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
                except BaseException as exc:
                    row['elapsed_ms']=int((time.monotonic()-started)*1000)
                    row['error']={'exception_type':type(exc).__name__}
                    if isinstance(exc,OSError):row['error'].update(native_error_domain='errno',native_error_code=exc.errno)
                    raise
                row['exit_code']=child.returncode;row['elapsed_ms']=int((time.monotonic()-started)*1000)
                for channel,data in (('stdout',child.stdout),('stderr',child.stderr)):
                    name=f'{layer["order"]:02d}-{action}.{channel}'
                    with (output/name).open('xb') as stream:stream.write(data)
                    row[channel]=name;row[channel+'_bytes']=len(data);row[channel+'_sha256']=H(data)
                    need(len(data)<=1024**2,'projection_git_output_limit')
                need(child.returncode==0,'projection_git_failed')
        observed=evidence.source_inventory(output/'source')
        need(observed==expected['source_files'],'projection_final_bytes')
        need(evidence.source_inventory(baseline/'source')==before,'projection_baseline_changed')
        final=encoded({'schema_version':1,'record_kind':'fex_materialized_source','scope':'fex_component','files':observed})
        (output/'materialized-source.json').write_bytes(final)
        value.update(passed=True,baseline_unchanged_observed=True,materialized_source_sha256=H(final),
          source_files=len(observed),source_bytes=sum(r['size_bytes'] for r in observed))
        (output/'control.json').write_bytes(encoded(value))
        return value
    except BaseException as exc:
        value['passed']=False;value['primary_error']={'code':getattr(exc,'code',type(exc).__name__),'exception_type':type(exc).__name__}
        if isinstance(exc,OSError):value['primary_error'].update(native_error_domain='errno',native_error_code=exc.errno)
        try:(output/'control.json').write_bytes(encoded(value))
        except BaseException as record_error:
            try:exc.failure_record_error=type(record_error).__name__
            except (AttributeError,TypeError):pass
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','derivatives','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--require-empty',required=True,action='store_true');args=parser.parse_args()
    try:
        value=project(args.baseline,args.derivatives,args.output)
        print(json.dumps({'passed':True,'layers':value['layers'],'source_files':value['source_files'],'source_bytes':value['source_bytes'],
              'compilation_performed':False,'module_initialization_performed':False,'owner_execution_performed':False}));return 0
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError) as exc:
        print('FAIL: '+getattr(exc,'code',type(exc).__name__),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
