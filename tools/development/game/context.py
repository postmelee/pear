# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Closed owned-game inputs and manual policy on an explicit runtime operation.

Inspection only reads declared inputs. A game copy requires the actual live
runtime-owned operation; a saved inspection or signing receipt cannot grant it.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import os
import re
import shutil
import sys
import time

from pear_runtime import build
from pear_runtime.errors import need
from pear_runtime.assembly import core
from pear_runtime.assembly._common import encoded
from pear_runtime.fixtures import game_operation, game_prerequisites, producers, supervision
from pear_runtime.fixtures.context import inventory_shape
from pear_runtime.fixtures.game_types import PreparedGame
from pear_runtime.fixtures.types import Selection
from pear_runtime.fixtures.inputs import save
from . import inputs

FIELDS=frozenset(('schema_version','scope','candidate','runtime_ref','operation_ref',
    'profile_ref','capabilities_ref','provider_root','producer_manifest_ref','seed_root',
    'seed_ref','seed_inventory','modules','output_root','game_root','snapshot_ref',
    'game_files','required_controls_ref','predecessor_release_ref','helper_refs','manual_policy'))
REF_FIELDS=('runtime_ref','operation_ref','profile_ref','capabilities_ref',
    'producer_manifest_ref','seed_ref','snapshot_ref','required_controls_ref','predecessor_release_ref')
FIXED_HELPERS={'copy':'/bin/cp','arch':'/usr/bin/arch',
               'screencapture':'/usr/sbin/screencapture','log':'/usr/bin/log'}
GAME_COUNT=69
RESERVE_BYTES=6*1024**3


def _ref_shape(value):
    need(type(value) is dict and set(value)=={'path','sha256','size_bytes'} and
         type(value['path']) is str and type(value['size_bytes']) is int and
         0<=value['size_bytes']<=8*1024**3 and type(value['sha256']) is str and
         re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'game_reference_shape')
    path=Path(value['path'])
    need(path.is_absolute() and '..' not in path.parts and
         path.resolve(strict=True)==path and not path.is_symlink(),'game_reference_alias')
    return path


def _directory(value):
    need(type(value) is str,'game_root_shape')
    path=Path(value)
    need(path.is_absolute() and '..' not in path.parts and path.is_dir() and
         path.resolve(strict=True)==path and not path.is_symlink(),'game_root_alias')
    return path


def _relative(value):
    need(type(value) is str and value and '\\' not in value and not value.startswith('/') and
         all(part not in ('','.','..') for part in value.split('/')),'game_relative_path')
    return Path(value)


def _capture(value):
    return producers.capture(value['producer_manifest_ref'],value['provider_root'],
        entry_modules=game_operation.GAME_ENTRY_MODULES,
        dynamic_paths=game_operation.GAME_DYNAMIC_PATHS,scope=game_operation.GAME_SCOPE)


def descriptor(ref):
    """Decode only the closed explicit descriptor, without execution or autofill."""
    value=core.read_ref(ref)
    need(type(value) is dict and set(value)==FIELDS and type(value['schema_version']) is int and
         value['schema_version']==1 and value['scope']=='owned_game_development_inputs' and
         value['candidate']=='d25-game' and value['manual_policy']=='manual_feedback_v1',
         'game_context_shape')
    for name in REF_FIELDS:_ref_shape(value[name])
    roots={name:_directory(value[name]) for name in ('game_root','seed_root','provider_root','output_root')}
    need(value['seed_ref']['path']==str(roots['seed_root']/'case.json'),'game_seed_binding')
    inventory_shape(value['seed_inventory'])
    rows=value['game_files']
    need(type(rows) is list and len(rows)==GAME_COUNT,'game_file_count')
    seen=set()
    for row in rows:
        need(type(row) is dict and set(row)=={'relative','ref'},'game_file_shape')
        path=_relative(row['relative']);need(row['relative'] not in seen,'game_file_duplicate')
        seen.add(row['relative'])
        need(_ref_shape(row['ref'])==roots['game_root']/path,'game_file_binding')
    need({'Megabonk.exe','GameAssembly.dll'}<=seen,'game_required_files')
    need(type(value['modules']) is dict and set(value['modules'])=={'ntdll.dll','xtajit64.dll'},
         'game_module_set')
    for row in value['modules'].values():
        need(type(row) is dict and set(row)=={'seed_sha256','selected_ref'} and
             type(row['seed_sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['seed_sha256']) is not None,
             'game_module_shape')
        _ref_shape(row['selected_ref'])
    helpers=value['helper_refs']
    need(type(helpers) is dict and set(helpers)=={*FIXED_HELPERS,'python'},'game_helper_set')
    for name,row in helpers.items():
        path=_ref_shape(row)
        expected=Path(FIXED_HELPERS[name]) if name in FIXED_HELPERS else Path(sys.executable).resolve(strict=True)
        need(path==expected,'game_helper_binding')
    runtime_root=Path(value['runtime_ref']['path']).parent
    input_roots=[roots['game_root'],roots['seed_root'],roots['provider_root'],runtime_root,Path(ref['path']).parent]
    input_roots.extend(Path(row['path']).parent for row in helpers.values())
    input_roots.extend(Path(value[name]['path']).parent for name in REF_FIELDS)
    output=roots['output_root']
    need(all(not output.is_relative_to(root) and not root.is_relative_to(output) for root in input_roots),
         'game_output_overlap')
    core.checked_ref(ref)
    return value


class GameContext:
    def __init__(self,ref):
        self.ref=deepcopy(ref);self.value=descriptor(self.ref)
        self._ref_bytes=encoded(self.ref);self._value_bytes=encoded(self.value)
        self.candidate=Selection(self.value['candidate'],Path(self.value['runtime_ref']['path']).parent)
        self._producers=_capture(self.value)
        output=Path(self.value['output_root'])
        need(all(not output.is_relative_to(root) and not root.is_relative_to(output)
                 for root in self._producers.roots.values()),'game_output_source_overlap')
        self._provider_binding=dict(provider_root=self.value['provider_root'],
            provider_ref=supervision.provenance_ref(),source_refs=supervision.source_refs(self.value['provider_root']))
        self._ledger=inputs.Ledger()
        self._operation=None;self._output=None;self._active=False;self._completed=False
        self._validated_end=False;self._assessment_finalized=False;self._producer_rows=None
        self._prepared=None;self._prepared_bytes=None;self._prepared_files=None
        self._runtime=None;self._runtime_value=None;self.selected=None
        self._clock=time.monotonic();self.timings=[]

    @property
    def operation(self):return self._operation

    @property
    def provider_root(self):return Path(self.value['provider_root'])

    @property
    def seed(self):return Path(self.value['seed_root'])

    def mark(self,name):
        now=time.monotonic();self.timings.append(dict(name=name,seconds=now-self._clock,
            wall_utc=build.point()['wall_utc'],monotonic_seconds=now));self._clock=now

    def _admit(self):
        need(encoded(self.ref)==self._ref_bytes and encoded(self.value)==self._value_bytes and
             core.read_ref(self.ref)==self.value,'game_context_changed')
        need(type(self.candidate) is Selection and self.candidate.name==self.value['candidate'] and
             self.candidate.runtime==Path(self.value['runtime_ref']['path']).parent,'game_context_candidate')
        self._producers.recheck()
        runtime,value,selected=game_operation.admit_candidate(self.value)
        game_prerequisites.admit(self.value)
        need(runtime==self.candidate.runtime,'game_context_runtime_binding')
        need(self.selected is None or selected==self.selected,'game_context_capabilities_changed')
        self.selected=deepcopy(selected)
        ledger=inputs.Ledger() if self._ledger.closed else self._ledger
        if self._ledger.closed:
            for row,before in self._ledger.rows.values():
                need(inputs.identity(Path(row['path']).lstat())==before,'game_input_changed_after_finish')
        for row in (self.ref,*(self.value[name] for name in REF_FIELDS),
                    *(row['selected_ref'] for row in self.value['modules'].values()),
                    *self.value['helper_refs'].values()):ledger.check(row)
        inputs.validate_game(ledger,self.value)
        snapshot=ledger.record(self.value['snapshot_ref'])
        rows=[row for depot in snapshot['platforms']['windows'] for row in depot['files'] if not row['flags']&64]
        need([row['path'] for row in rows]==[row['relative'] for row in self.value['game_files']],
             'game_snapshot_order')
        inputs.validate_seed(self.value)
        need(self._provider_binding==dict(provider_root=self.value['provider_root'],
            provider_ref=supervision.provenance_ref(),source_refs=supervision.source_refs(self.provider_root)),
            'game_provider_changed')
        if ledger is not self._ledger:ledger.finish()
        return runtime,value

    def fresh_output(self,path):
        path=Path(path)
        need(path.is_absolute() and path.parent==Path(self.value['output_root']) and
             path.name not in ('','.','..') and path.parent.resolve(strict=True)==path.parent and
             not path.exists() and not path.is_symlink(),'game_fresh_output')
        return path

    def storage_admission(self,output):
        return self._storage_budget(self.fresh_output(output))

    def _storage_budget(self,output):
        self._producers.recheck()
        files={row['path']:row for row in self.value['seed_inventory'] if row['kind']=='file'}
        seed_bytes=sum(row['size'] for row in files.values());budgeted_seed=max(seed_bytes,842557436)
        game_bytes=sum(row['ref']['size_bytes'] for row in self.value['game_files'])
        growth=0
        for name,row in self.value['modules'].items():
            prior=files.get('drive_c/windows/system32/'+name)
            need(prior is not None and prior['sha256']==row['seed_sha256'],'game_seed_module')
            growth+=max(0,row['selected_ref']['size_bytes']-prior['size'])
        allowance=1024**3
        additional=game_bytes+budgeted_seed+growth+allowance+self._producers.logical_bytes
        free=shutil.disk_usage(output.parent).free
        need(free>=additional+RESERVE_BYTES,'game_storage_capacity')
        return dict(schema_version=1,scope='single_owned_game_diagnostic',output=str(output),
            observed_at=build.point(),game_input_logical_bytes=game_bytes,
            seed_inventory_logical_bytes=seed_bytes,budgeted_seed_bytes=budgeted_seed,
            positive_module_growth_bytes=growth,captures_logs_authority_metadata_allowance_bytes=allowance,
            producer_snapshot_bytes=self._producers.logical_bytes,additional_peak_bytes=additional,
            reserve_bytes=RESERVE_BYTES,required_free_bytes=additional+RESERVE_BYTES,observed_free_bytes=free,
            apfs_clone_savings_assumed=False,execution_authorized_by_this_record=False)

    def inspect(self,output):
        need(self._operation is None and not self._completed,'game_inspection_state')
        self._admit();storage=self.storage_admission(output)
        return dict(schema_version=1,scope='owned_game_development_inspection',status='input_admitted',
            descriptor_ref=deepcopy(self.ref),candidate=self.candidate.name,
            **{name:deepcopy(self.value[name]) for name in ('runtime_ref','operation_ref','profile_ref',
                'capabilities_ref','producer_manifest_ref','required_controls_ref','predecessor_release_ref')},
            output=str(Path(output)),storage=storage,selected_capabilities=deepcopy(self.selected),
            game_inputs=dict(snapshot_ref=deepcopy(self.value['snapshot_ref']),file_count=GAME_COUNT,
                             logical_bytes=storage['game_input_logical_bytes']),
            seed=dict(seed_ref=deepcopy(self.value['seed_ref']),inventory_entries=len(self.value['seed_inventory']),
                      logical_bytes=storage['seed_inventory_logical_bytes']),
            source_capture=dict(manifest_ref=deepcopy(self.value['producer_manifest_ref']),
                file_count=len(self._producers.refs),logical_bytes=self._producers.logical_bytes),
            helper_refs=deepcopy(self.value['helper_refs']),manual_policy=self.value['manual_policy'],
            current_authority_assessed=False,execution_authorized_by_this_record=False,
            runtime_execution_performed=False,game_execution_performed=False,game_qualified=False)

    def begin_game(self,output,*,operation):
        need(self._operation is None and not self._active and not self._completed,'game_context_single_run')
        need(type(operation) is game_operation.GameOperation and operation.context is self,
             'game_context_operation')
        path=self.fresh_output(output);operation.assert_current(path,operation.operation_id)
        self.storage_admission(path)
        self._operation=operation;self._output=path
        try:self._runtime,self._runtime_value=self._admit()
        except BaseException:
            self._completed=True;raise
        self._active=True
        return self._runtime,self._runtime_value

    def _live(self,output=None):
        need(self._operation is not None and type(self._operation) is game_operation.GameOperation and
             self._operation.context is self and self._output is not None,'game_context_operation')
        need(output is None or Path(output)==self._output,'game_context_output')
        self._operation.assert_current(self._output,self._operation.operation_id)

    def _owned_output(self,output):
        self._live(output);path=Path(output)
        need(path.is_dir() and path.resolve(strict=True)==path and not path.is_symlink(),'game_output_alias')
        return path

    def prepare_game(self,output):
        output=self._owned_output(output)
        need(self._active and not self._completed and self._prepared is None,'game_prepare_state')
        self._admit();self._storage_budget(output);core.checked_ref(self.value['helper_refs']['copy'])
        source_files=inputs.game_copy(Path(self.value['game_root']),Path(self.value['snapshot_ref']['path']),output/'game')
        need(source_files==[row['ref'] for row in self.value['game_files']],'game_copied_source_binding')
        game=output/'game';target=game/'GameAssembly.dll';target_ref=build.fact(target);st=target.lstat()
        prepared=PreparedGame(game_root=game,executable_ref=build.fact(game/'Megabonk.exe'),
            target=dict(dev=st.st_dev,ino=st.st_ino,bytes=st.st_size,sha256=target_ref['sha256']),
            source_files=deepcopy(source_files),snapshot_ref=deepcopy(self.value['snapshot_ref']))
        self._prepared=prepared;self._prepared_bytes=encoded(self._prepared_value(prepared))
        self._prepared_files=[build.fact(game/_relative(row['relative'])) for row in self.value['game_files']]
        self._check_prepared();self._admit();self._live()
        return prepared

    @staticmethod
    def _prepared_value(value):
        return dict(game_root=str(value.game_root),executable_ref=value.executable_ref,target=value.target,
                    source_files=value.source_files,snapshot_ref=value.snapshot_ref)

    def _check_prepared(self):
        value=self._prepared;need(type(value) is PreparedGame and
            encoded(self._prepared_value(value))==self._prepared_bytes,'game_prepared_changed')
        game=self._output/'game'
        need(value.game_root==game and game.resolve(strict=True)==game and game.is_dir(),'game_prepared_root')
        expected={row['relative'] for row in self.value['game_files']};directories=set()
        for name in expected:
            directories.update(str(p) for p in Path(name).parents if str(p)!='.')
        found=set();found_dirs=set()
        for base,dirs,files in os.walk(game,followlinks=False):
            path=Path(base)
            need(path.resolve(strict=True)==path and len(found)+len(found_dirs)<=4096,'game_prepared_tree')
            for name in dirs:
                child=path/name;need(not child.is_symlink(),'game_prepared_alias')
                found_dirs.add(str(child.relative_to(game)))
            found.update(str((path/name).relative_to(game)) for name in files)
        need(found==expected and found_dirs==directories,'game_prepared_inventory')
        for old,row in zip(self._prepared_files,self.value['game_files'],strict=True):
            path=game/_relative(row['relative']);need(path.resolve(strict=True)==path and
                build.fact(path)==old and old['sha256']==row['ref']['sha256'] and
                old['size_bytes']==row['ref']['size_bytes'],'game_prepared_file_changed')
        target=game/'GameAssembly.dll';st=target.lstat();actual=build.fact(target)
        need(value.target==dict(dev=st.st_dev,ino=st.st_ino,bytes=st.st_size,sha256=actual['sha256']) and
             value.executable_ref==build.fact(game/'Megabonk.exe') and
             value.source_files==[row['ref'] for row in self.value['game_files']] and
             value.snapshot_ref==self.value['snapshot_ref'],'game_prepared_binding')

    def recheck_prepared(self,output):
        """Full copied-byte check immediately before the runtime's fixed loader."""
        self._owned_output(output)
        need(self._active and not self._completed,'game_prepared_state')
        self._admit();self._check_prepared();self._live()
        return self._prepared

    def baseline(self,path):
        self._live();path=Path(path)
        need(self._active and path.parent==self._output and not path.exists(),'game_baseline_output')
        self._admit()
        save(path,dict(schema_version=1,scope='explicit_owned_game_current_inputs',passed=True,
            game_context_ref=self.ref,runtime_ref=self.value['runtime_ref'],
            operation_ref=self.value['operation_ref'],snapshot_ref=self.value['snapshot_ref'],
            seed_ref=self.value['seed_ref'],historical_ancestry_replayed=False,game_qualified=False))

    def preserve_sources(self,output):
        output=self._owned_output(output)
        need(self._active and self._producer_rows is None,'game_source_capture_state')
        self._producer_rows=self._producers.preserve(output)
        return self._producer_rows

    def witness_binding(self):
        self._live();self._producers.recheck()
        need(self._provider_binding['provider_ref']==supervision.provenance_ref() and
             self._provider_binding['source_refs']==supervision.source_refs(self.provider_root),'game_provider_changed')
        return deepcopy(self._provider_binding)

    def child_environment(self,environment):
        self._live();self._producers.recheck()
        return dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',
            PYTHONPATH=os.pathsep.join(str(root) for root in self._producers.roots.values()),
            HOME=environment['HOME'],TMPDIR=environment['TMPDIR'])

    def finish(self):
        self._live();need(self._active and not self._completed,'game_context_not_active')
        try:
            runtime,value=self._admit();self._check_prepared()
            need(runtime==self._runtime and value==self._runtime_value,'game_context_runtime_changed')
            self._ledger.finish();self._validated_end=True
        finally:self._active=False;self._completed=True
        return runtime,value

    def finalize_assessment(self,output):
        output=self._owned_output(output)
        need(self._completed and self._validated_end and not self._active and
             not self._assessment_finalized and self._producer_rows is not None,'game_finalization_state')
        runtime,value=self._admit();self._check_prepared()
        need(runtime==self._runtime and value==self._runtime_value,'game_context_runtime_changed')
        rows=core.read_ref(build.fact(output/'producers.json'))
        need(rows==self._producer_rows,'game_source_snapshot_rows')
        for row in rows:
            core.checked_ref(row['original']);core.checked_ref(row['snapshot'])
            need(row['original']['sha256']==row['snapshot']['sha256'] and
                 row['original']['size_bytes']==row['snapshot']['size_bytes'],'game_source_snapshot_changed')
        self._live();self._assessment_finalized=True
        return dict(passed=True,game_context_ref=deepcopy(self.ref),
                    producers_ref=build.fact(output/'producers.json'),game_qualified=False)
