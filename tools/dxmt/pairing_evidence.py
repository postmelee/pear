#!/usr/bin/env python3
"""Pure finite native pairing evidence plus explicit immutable diagnostics review.

This reader never signs, admits, runs Wine, creates a device or grants review.
An existing run keeps diagnostics_review=unperformed; a separate root-authored
private assessment closes only the selected finite native Metal API scope.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime
import importlib.util
import os
from pathlib import Path
import re
import stat
import sys
from common import (REPO, Error, decode_json, digest, encoded, fields, need,
                    owned_directory, read_relative)

SCOPE='finite_native_metal_api_pairing'
REVIEW='diagnostics-review.json'
CLASSIFICATIONS={'nonvalidation_native_diagnostic','validation_enabled_notice','metal_api_warning'}
UNPERFORMED=('shader_workload','general_renderer','performance','hybrid_execution',
             'translated_guest_execution','game_qualification','distribution_qualification')
REVIEW_FIELDS=('schema_version','record_kind','scope','review','review_actor','reviewed_at_utc',
    'run_ref','case_ref','assessment_ref','runtime_ref','producers','logs','diagnostics',
    'metal_environment','assessment')
FINDING_FIELDS=('role','channel','path','byte_offset','byte_count','sha256','classification')
VALIDATION=re.compile(r'\b(?:metal|shader)\s+(?:(?:api|gpu|shader)\s+)?validation\b|\bmtldebug\w*',re.I)
ENABLED_NOTICES={'Metal API Validation Enabled','Metal GPU Validation Enabled','Shader Validation Enabled'}
NSLOG_NOTICE=re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) '
    r'wine\[([1-9]\d*):([1-9]\d*)\] (.+)')
WARNING=re.compile(r'\bwarn(?:ing)?\b',re.I)
VALIDATION_ERROR=re.compile(r'\b(?:failed\s+assertion|assertion\s+(?:failure|failed))\b|'
    r'\b(?:metal|shader|mtl\w*|validation)\b[^\n]*\b(?:error|failed|invalid)\b|'
    r'\b(?:error|failed|invalid)\b[^\n]*\b(?:metal|shader|mtl\w*|validation)\b',re.I)


def same(left,right,code):need(encoded(left)==encoded(right),code)


def captured_module(path,raw,alias):
    spec=importlib.util.spec_from_file_location(alias,path)
    need(spec is not None and spec.loader is not None,'pair_evidence_source_loader')
    module=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),vars(module))
    return module


def adapters(repo=REPO):
    raw_run=read_relative(repo,'tools/dxmt/run_pairing.py')
    raw_runtime=read_relative(repo,'tools/dxmt/pairing_runtime.py')
    runner=captured_module(Path(repo)/'tools/dxmt/run_pairing.py',raw_run,'_pear_dxmt_evidence_run')
    runtime=captured_module(Path(repo)/'tools/dxmt/pairing_runtime.py',raw_runtime,'_pear_dxmt_evidence_runtime')
    current=producer_hashes(repo,runner,runtime)
    need(current['tools/dxmt/run_pairing.py']==digest(raw_run)
         and current['tools/dxmt/pairing_runtime.py']==digest(raw_runtime),'pair_evidence_source_changed')
    return runner,runtime,raw_run,current


def producer_hashes(repo,runner,runtime):
    values=runtime.producers(repo)
    for path,sha in runner.producers(repo).items():
        need(path not in values or values[path]==sha,'pair_evidence_producer_conflict')
        values[path]=sha
    values['tools/dxmt/pairing_evidence.py']=digest(read_relative(repo,'tools/dxmt/pairing_evidence.py'))
    return dict(sorted(values.items()))


def pure_replay(root,repo,runner,runtime,raw_run):
    """Reuse exact verify_run code with one documented pure dependency adapter.

    The ordinary verify_run calls live profile/signature admission. Only its
    isolated function globals copy replaces runtime_values with structural
    replay and preserves the original scope assertions. No module is patched.
    """
    captured=[]
    def structural_values(path,repo=repo):
        value,_,_=runtime.verify_structural(path,repo=repo)
        need(value['code_publication_policy']=='page-wx'and value['runtime_eligible']is False
             and value['game_qualified']is False,'pair_runtime_scope')
        captured.append(value)
        return value
    nodes=[node for node in ast.parse(raw_run).body if isinstance(node,ast.FunctionDef)and node.name=='verify_run']
    need(len(nodes)==1 and not nodes[0].decorator_list,'pair_evidence_replay_function')
    namespace=dict(vars(runner));namespace['runtime_values']=structural_values
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'tools/dxmt/run_pairing.py','exec'),namespace)
    observed=namespace['verify_run'](root,repo=repo)
    need(len(captured)==1,'pair_evidence_runtime_replay_count')
    return observed,captured[0]


def diagnostic_lines(raw_logs):
    lines=[]
    for (role,channel),raw in sorted(raw_logs.items()):
        if channel!='stderr':continue
        offset=0
        for line in raw.splitlines(keepends=True):
            size=len(line)
            # Full source protocol is checked independently before exclusion.
            fixture=role=='loader'and line.startswith(b'{"record_kind":"pear_metal_pairing"')
            if not fixture and line.strip():
                lines.append({'role':role,'channel':channel,'path':role+'.'+channel+'.log',
                              'byte_offset':offset,'byte_count':size,'sha256':digest(line)})
            offset+=size
    return lines


def review_context(root,repo=REPO):
    """Return bindings/line inventory only; this does not create or grant review."""
    root=owned_directory(root,repo);runner,runtime,raw_run,current=adapters(repo)
    raw=read_relative(root,'run.json');run=decode_json(raw)
    observed,_=pure_replay(root,repo,runner,runtime,raw_run)
    # verify_run has already independently replayed every case and assessment.
    case_raw=read_relative(root,'case.json',16*1024**2)
    case=decode_json(case_raw,16*1024**2,max_nodes=1000000)
    assessment_raw=read_relative(root,'assessment.json')
    same(decode_json(assessment_raw),{'passed':True,'error':None,'observations':observed},
         'pair_evidence_assessment_changed')
    logs=runner.verify_logs(root,case)
    _,diagnostics=runner.native_rows(logs[('loader','stderr')])
    same(observed['diagnostics'],{'sha256':digest(diagnostics),'size_bytes':len(diagnostics),
        'review':'unperformed','scope':'captured_nonfixture_loader_stderr'},'pair_evidence_diagnostics_changed')
    need(run['diagnostics_review']=='unperformed'and run['passed']is True
         and run['ordinary_arm64_pe_execution_performed']is True and run['native_pairing_observed']is True
         and all(run[key]is False for key in ['hybrid_execution_performed','translated_guest_execution_performed',
             'game_qualified','runtime_eligible','distribution_qualified']),
         'pair_evidence_run_scope')
    for key,path,data in [('case_ref','case.json',case_raw),('assessment_ref','assessment.json',assessment_raw)]:
        same(run[key],{'path':path,'sha256':digest(data)},'pair_evidence_reference_changed')
    runtime_root=owned_directory(run['runtime_ref']['path'],repo)
    need(digest(read_relative(runtime_root,'runtime.json'))==run['runtime_ref']['sha256'],
         'pair_evidence_runtime_changed')
    need(read_relative(root,'run.json')==raw and producer_hashes(repo,runner,runtime)==current,
         'pair_evidence_changed_during_replay')
    return {'run_ref':{'path':'run.json','sha256':digest(raw)},'case_ref':run['case_ref'],
        'assessment_ref':run['assessment_ref'],'runtime_ref':run['runtime_ref'],'producers':current,
        'logs':[{'role':role,'channel':channel,'path':role+'.'+channel+'.log','sha256':digest(data),
                 'size_bytes':len(data)}for (role,channel),data in sorted(logs.items())],
        'diagnostics':observed['diagnostics'],'metal_environment':runner.METAL_ENV,
        'finding_inputs':diagnostic_lines(logs),'observations':observed,
        'notice_pids':notice_process_ids(case)},logs


def notice_process_ids(case):
    """Use only identities already validated by the exact finite run replay.

    Registered Wine descendants share the loader stderr stream. Their prefix
    PID is evidence of the recorded process identity, not general log trust.
    """
    values={role:{item['identity']['pid']}for role,item in case['processes'].items()}
    values['loader'].update(item['identity']['pid']for item in case['registrations'])
    need(all(type(pid)is int and 1<pid<=2147483647 for pids in values.values()for pid in pids),
         'pair_review_notice_identities')
    return values


def enabled_notice(text,pids):
    if text in ENABLED_NOTICES:return True
    match=NSLOG_NOTICE.fullmatch(text)
    if match is None:return False
    timestamp,pid,tid,body=match.groups()
    try:datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S.%f')
    except ValueError:raise Error('pair_review_notice_timestamp')from None
    need(1<int(pid)<=2147483647 and 0<int(tid)<=18446744073709551615,
         'pair_review_notice_process_bounds')
    need(pids is not None and int(pid)in pids,'pair_review_notice_process')
    return body in ENABLED_NOTICES


def classify_finding(row,line,pids=None):
    try:text=line.decode('utf-8').strip()
    except UnicodeDecodeError:raise Error('pair_review_unknown_diagnostic_encoding')from None
    need(not VALIDATION_ERROR.search(text),'pair_review_validation_error')
    kind=row['classification'];need(kind in CLASSIFICATIONS,'pair_review_classification')
    validation=VALIDATION.search(text) is not None
    if kind=='nonvalidation_native_diagnostic':
        need(not validation,'pair_review_unclassified_validation')
    elif kind=='validation_enabled_notice':
        need(enabled_notice(text,pids),
             'pair_review_unknown_validation_notice')
    else:
        need(validation and WARNING.search(text)is not None
             and re.search(r'\bshader\b',text,re.I)is None,'pair_review_unknown_validation_warning')


def verify_native_evidence(root,repo=REPO):
    """Pure complete gate for this finite native API schedule, never game support."""
    root=owned_directory(root,repo)
    raw=read_relative(root,REVIEW,2*1024**2)
    info=(root/REVIEW).lstat()
    need(stat.S_ISREG(info.st_mode)and stat.S_IMODE(info.st_mode)==0o444 and info.st_uid==os.getuid(),
         'pair_review_ownership_mode')
    review=decode_json(raw,2*1024**2,max_nodes=100000)
    fields(review,REVIEW_FIELDS,'dxmt_pairing_diagnostics_review')
    need(review['scope']==SCOPE and review['review']=='performed'and review['review_actor']=='root_orchestrator',
         'pair_review_scope')
    need(type(review['reviewed_at_utc'])is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',review['reviewed_at_utc']),
         'pair_review_time')
    try:datetime.strptime(review['reviewed_at_utc'],'%Y-%m-%dT%H:%M:%SZ')
    except ValueError:raise Error('pair_review_time')from None
    context,logs=review_context(root,repo)
    for key in ['run_ref','case_ref','assessment_ref','runtime_ref','producers','logs','diagnostics','metal_environment']:
        same(review[key],context[key],'pair_review_binding_changed')
    assessment=review['assessment']
    fields(assessment,['method','coverage','validation_errors_observed','findings',*UNPERFORMED])
    need(assessment['method']=='explicit_raw_log_review'
         and assessment['coverage']=='all_captured_stderr_nonfixture_lines'
         and assessment['validation_errors_observed']is False
         and all(assessment[key]=='unperformed'for key in UNPERFORMED),'pair_review_assessment_scope')
    rows=assessment['findings'];need(type(rows)is list and len(rows)==len(context['finding_inputs']),
                                   'pair_review_finding_coverage')
    for row,expected in zip(rows,context['finding_inputs']):
        fields(row,FINDING_FIELDS)
        same({key:row[key]for key in expected},expected,'pair_review_finding_changed')
        need(type(row['byte_offset'])is int and type(row['byte_count'])is int,'pair_review_finding_bounds')
        line=logs[(row['role'],row['channel'])][row['byte_offset']:row['byte_offset']+row['byte_count']]
        classify_finding(row,line,context['notice_pids'][row['role']])
    need(read_relative(root,REVIEW,2*1024**2)==raw,'pair_review_changed_during_replay')
    # Recheck bytes after review, without repeating execution or live admission.
    runner,runtime,_,_=adapters(repo)
    need(producer_hashes(repo,runner,runtime)==context['producers'],'pair_evidence_producer_changed')
    for row in context['logs']:
        data=read_relative(root,row['path'],2097152 if row['channel']=='events'else 262144)
        need(len(data)==row['size_bytes']and digest(data)==row['sha256'],'pair_evidence_log_changed')
    for key in ['run_ref','case_ref','assessment_ref']:
        ref=context[key]
        need(digest(read_relative(root,ref['path'],16*1024**2))==ref['sha256'],'pair_evidence_receipt_changed')
    need(digest(read_relative(Path(context['runtime_ref']['path']),'runtime.json'))==context['runtime_ref']['sha256'],
         'pair_evidence_runtime_changed')
    return {'schema_version':1,'record_kind':'dxmt_pairing_native_evidence','scope':SCOPE,
        'native_pairing_observed':True,'ordinary_arm64_pe_execution_performed':True,
        'diagnostics_review':'performed','metal_api_validation':'reviewed_no_errors',
        'finite_native_scope_complete':True,**{key:'unperformed'for key in UNPERFORMED},
        'runtime_eligible':False,'game_qualified':False,'distribution_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True)
    parser.add_argument('--require-complete',required=True,action='store_true');args=parser.parse_args(argv)
    try:
        print(encoded(verify_native_evidence(args.run)).decode(),end='');return 0
    except (Error,OSError,ValueError,KeyError,TypeError)as exc:
        print(encoded({'finite_native_scope_complete':False,'runtime_eligible':False,
            'error':getattr(exc,'code','pair_native_evidence_failed')}).decode(),end='',file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
