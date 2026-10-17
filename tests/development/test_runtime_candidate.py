# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable selector admission and isolated state tests; no runtime execution."""
from contextlib import contextmanager
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from tools.development import runtime_candidate as candidate


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ('runtime', 'private', 'seed', 'outputs', 'old-preview', 'builds'):
            (self.root / name).mkdir()
        self.runtime = self.root / 'runtime'
        (self.runtime / 'locks').mkdir()
        self.historical = self.put(self.runtime / 'locks/task56-reconstruction-v1.json', {'historical': True})
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Selector test', '-c', 'user.email=selector@example.invalid',
                 'commit', '-qm', 'Synthetic runtime metadata')
        self.pin = self.git('rev-parse', 'HEAD').strip()
        self.pins = {'wine': '1' * 40, 'fex': '2' * 40, 'dxmt': '3' * 40}
        refs, operations = {}, []
        for role in ('wine', 'fex', 'graphics'):
            directory = self.root / 'builds' / role
            directory.mkdir()
            operation = self.put(directory / 'operation.json',
                dict(scope='task56_component_build', operation_id=role, released=True))
            operations.append(operation)
            source = {'wine': self.pins['wine']}
            if role == 'fex':
                source['fex'] = self.pins['fex']
            if role == 'graphics':
                source['dxmt'] = self.pins['dxmt']
            refs[role] = self.put(directory / 'build.json', dict(scope='development_component_build',
                status='passed', operation_id=role,
                roots={k: dict(kind='git', commit=v) for k, v in source.items()}))
        self.build_refs = refs
        self.operation_refs = operations
        runtime = self.put(self.root / 'private/runtime.json',
            dict(development_assembly=dict(builds=list(refs.values()), component_operations=operations)))
        operation = self.put(self.root / 'private/assembly.json', {'assembly': True})
        manifest = self.put(self.root / 'private/producers.json', dict(roots={'runtime': str(self.runtime)}))
        profile = self.put(self.root / 'private/profile.json', {'synthetic': True})
        self.descriptor = dict(runtime_ref=runtime, operation_ref=operation, producer_manifest_ref=manifest,
            provider_root=str(self.runtime), seed_root=str(self.root / 'seed'),
            output_root=str(self.root / 'outputs'), profile_ref=profile)
        self.descriptor.update(schema_version=1, scope='redistributable_runtime_fixtures', candidate='d25-game',
            capabilities_ref=self.put(self.root / 'private/capabilities.json', {}),
            seed_ref=self.put(self.root / 'seed/case.json', {}), seed_inventory=[], modules={}, fixture_refs={})
        self.desc = self.put(self.root / 'private/descriptor.json', self.descriptor)
        self.lock = dict(schema_version=1, scope='pear_development_candidate_lock', purpose=candidate.PURPOSE,
            candidate=dict(runtime=candidate.compact(runtime), assembly_operation=candidate.compact(operation),
                           builds={k: candidate.compact(v) for k, v in refs.items()}),
            component_sources=self.pins, tool_sources=dict(runtime=self.pin, wine='4' * 40, fex='5' * 40),
            assembly_tool_checkpoint=self.pin,
            reconstruction={**self.historical, 'path': 'locks/task56-reconstruction-v1.json'})
        self.lock_ref = self.put(self.root / 'private/lock.json', self.lock)
        self.spec = dict(schema_version=1, scope='pear_development_selection', purpose=candidate.PURPOSE,
            runtime_checkout=dict(path=str(self.runtime), commit=self.pin), lock_ref=self.lock_ref,
            fixture_descriptor_ref=self.desc, game_descriptor_ref=None, state_root=str(self.root / 'state'),
            protected_roots=[str(self.root / 'old-preview')])
        self.spec_ref = self.put(self.root / 'private/spec.json', self.spec)
        self.preview = self.root / 'old-preview/save.bin'
        self.preview.write_bytes(b'preserve original state')

    def git(self, *args):
        return subprocess.check_output(['/usr/bin/git', '-C', str(self.runtime), *args], text=True)

    def put(self, path, value):
        path.write_text(json.dumps(value, sort_keys=True) + '\n')
        return candidate.fact(path)

    def update_spec(self, **changes):
        self.spec.update(changes)
        self.spec_ref = self.put(Path(self.spec_ref['path']), self.spec)

    def update_lock(self):
        self.lock_ref = self.put(Path(self.lock_ref['path']), self.lock)
        self.update_spec(lock_ref=self.lock_ref)

    def refused(self, code):
        return self.assertRaisesRegex(candidate.Refusal, '^' + code + '$')

    def test_admit_exact_closed_metadata(self):
        value, lock, _ = candidate.selection(self.spec_ref)
        self.assertEqual(value, self.spec)
        self.assertEqual(lock['component_sources'], self.pins)
        self.assertFalse((self.root / 'state').exists())

    def test_purpose_mismatch(self):
        self.update_spec(purpose='preview')
        with self.refused('selection_scope'):
            candidate.selection(self.spec_ref)

    def test_boolean_schema_refused(self):
        self.update_spec(schema_version=True)
        with self.refused('selection_scope'):
            candidate.selection(self.spec_ref)

    def test_unknown_field_refused(self):
        self.update_spec(activate_preview=True)
        with self.refused('selection_scope'):
            candidate.selection(self.spec_ref)

    def test_runtime_commit_mismatch(self):
        self.update_spec(runtime_checkout=dict(path=str(self.runtime), commit='f' * 40))
        with self.refused('checkout_commit'):
            candidate.selection(self.spec_ref)

    def test_dirty_runtime_refused(self):
        (self.runtime / 'unreviewed.py').write_text('pass\n')
        with self.refused('checkout_dirty'):
            candidate.selection(self.spec_ref)

    def test_assume_unchanged_index_refused(self):
        self.git('update-index', '--assume-unchanged', 'locks/task56-reconstruction-v1.json')
        (self.runtime / 'locks/task56-reconstruction-v1.json').write_text('{}')
        self.assertEqual(self.git('status', '--porcelain').strip(), '')
        with self.refused('checkout_hidden_index_flags'):
            candidate.selection(self.spec_ref)

    def test_fifo_metadata_refused_without_open(self):
        import os
        fifo = self.root / 'private/fifo'
        os.mkfifo(fifo)
        with self.refused('file_required'):
            candidate.fact(fifo)

    def test_growing_metadata_is_bounded(self):
        target = self.root / 'private/small.json'
        target.write_bytes(b'12345678')
        with patch.object(candidate, 'MAX_JSON', 4):
            with self.refused('metadata_size'):
                candidate.fact(target)

    def test_tool_pin_mismatch(self):
        self.lock['tool_sources']['runtime'] = 'f' * 40
        self.update_lock()
        with self.refused('lock_tool_commit'):
            candidate.selection(self.spec_ref)

    def test_candidate_lock_mismatch(self):
        self.lock['candidate']['runtime']['sha256'] = 'f' * 64
        self.update_lock()
        with self.refused('candidate_lock_mismatch'):
            candidate.selection(self.spec_ref)

    def test_build_set_cannot_duplicate(self):
        self.lock['candidate']['builds']['wine'] = copy.deepcopy(self.lock['candidate']['builds']['fex'])
        self.update_lock()
        with self.refused('build_lock_mismatch'):
            candidate.selection(self.spec_ref)

    def test_component_source_pin_mismatch(self):
        self.lock['component_sources']['wine'] = 'f' * 40
        self.update_lock()
        with self.refused('component_source_mismatch'):
            candidate.selection(self.spec_ref)

    def test_missing_input(self):
        Path(self.desc['path']).unlink()
        with self.assertRaises(FileNotFoundError):
            candidate.selection(self.spec_ref)
        self.assertFalse((self.root / 'state').exists())

    def test_changed_input(self):
        Path(self.desc['path']).write_text('{}\n')
        with self.refused('reference_changed'):
            candidate.selection(self.spec_ref)

    def test_alias_input(self):
        alias = self.root / 'descriptor-alias'
        alias.symlink_to(self.desc['path'])
        self.update_spec(fixture_descriptor_ref={**self.desc, 'path': str(alias)})
        with self.refused('path_alias'):
            candidate.selection(self.spec_ref)

    def test_state_inside_preview_refused(self):
        self.update_spec(state_root=str(self.root / 'old-preview/development'))
        with self.refused('state_input_overlap'):
            candidate.selection(self.spec_ref)
        self.assertEqual(self.preview.read_bytes(), b'preserve original state')

    def test_state_contains_inputs_refused(self):
        self.update_spec(state_root=str(self.root))
        with self.refused('state_input_overlap'):
            candidate.selection(self.spec_ref)

    def test_state_inside_runtime_refused(self):
        self.update_spec(state_root=str(self.runtime / 'development-state'))
        with self.refused('state_input_overlap'):
            candidate.selection(self.spec_ref)

    def test_output_inside_protected_refused(self):
        self.update_spec(protected_roots=[str(self.root / 'outputs')])
        with self.refused('diagnostic_protected_overlap'):
            candidate.selection(self.spec_ref)

    def test_game_joins_same_candidate(self):
        game = {**self.descriptor, 'runtime_ref': dict(path=self.desc['path'], **candidate.compact(self.desc))}
        ref = self.put(self.root / 'private/game.json', game)
        self.update_spec(game_descriptor_ref=ref)
        with self.refused('game_candidate_mismatch'):
            candidate.selection(self.spec_ref)

    def test_changed_component_operation(self):
        Path(self.operation_refs[0]['path']).write_text('{}')
        with self.refused('reference_changed'):
            candidate.selection(self.spec_ref)

    def test_prepare_requires_successful_inspection(self):
        with patch.object(candidate, 'inspect', side_effect=candidate.Refusal('synthetic_inspection_failure')):
            with self.refused('synthetic_inspection_failure'):
                candidate.prepare(Path(self.spec_ref['path']))
        self.assertFalse((self.root / 'state').exists())

    def synthetic_inspection(self, ref, *, kind='auto'):
        candidate.selection(ref)
        return dict(selection_ref=ref, execution_authorized_by_this_record=False)

    def test_prepare_select_and_reselect_preserve_preview(self):
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            first = candidate.prepare(Path(self.spec_ref['path']))
            self.assertFalse((self.root / 'state/active.json').exists())
            self.assertEqual(candidate.prepare(Path(self.spec_ref['path'])), first)
            selected = candidate.select(first['path'])
            self.assertEqual(selected['prepared_ref'], first)
            self.assertEqual(candidate.active_path(self.root / 'state'), first['path'])
            candidate.select(first['path'])
        self.assertEqual(self.preview.read_bytes(), b'preserve original state')
        self.assertEqual(len(list((self.root / 'state/transactions').iterdir())), 2)
        self.assertEqual((self.root / 'state/active.json').stat().st_mode & 0o777, 0o600)

    def test_reprepare_refuses_corrupt_existing_record(self):
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            first = candidate.prepare(Path(self.spec_ref['path']))
            target = Path(first['path'])
            value = candidate.read_ref(first)
            value['scope'] = 'foreign_record'
            self.put(target, value)
            before = target.read_bytes()
            with self.refused('prepared_selection_shape'):
                candidate.prepare(Path(self.spec_ref['path']))
            self.assertEqual(target.read_bytes(), before)

    def test_foreign_state_refused_without_mutation(self):
        state = self.root / 'state'; state.mkdir()
        self.put(state / 'owner.json', {'foreign': True})
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            with self.refused('foreign_state_root'):
                candidate.prepare(Path(self.spec_ref['path']))
        self.assertEqual(sorted(p.name for p in state.iterdir()), ['owner.json'])

    def test_changed_prepared_spec_refused(self):
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            prepared = candidate.prepare(Path(self.spec_ref['path']))
            self.update_spec(purpose='preview')
            with self.refused('reference_changed'):
                candidate.select(prepared['path'])
        self.assertFalse((self.root / 'state/active.json').exists())

    def test_active_alias_refused(self):
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            prepared = candidate.prepare(Path(self.spec_ref['path']))
            (self.root / 'state/active.json').symlink_to(self.preview)
            with self.refused('path_alias'):
                candidate.select(prepared['path'])
        self.assertEqual(self.preview.read_bytes(), b'preserve original state')

    def test_previous_selection_from_another_state_is_preserved_and_refused(self):
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            first = candidate.prepare(Path(self.spec_ref['path']))
            second_spec = {**self.spec, 'state_root': str(self.root / 'second-state')}
            second_ref = self.put(self.root / 'private/second-spec.json', second_spec)
            second = candidate.prepare(second_ref['path'])
            active = self.root / 'state/active.json'
            self.put(active, dict(schema_version=1, scope='pear_active_development_selection',
                                  prepared_ref=second))
            before = active.read_bytes()
            with self.refused('previous_selection_foreign_state'):
                candidate.select(first['path'])
            self.assertEqual(active.read_bytes(), before)
            self.assertEqual(list((self.root / 'state/transactions').iterdir()), [])

    def test_boolean_owner_schema_refused(self):
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            first = candidate.prepare(Path(self.spec_ref['path']))
            self.put(self.root / 'state/owner.json', dict(schema_version=True,
                scope='pear_development_selection_state', purpose=candidate.PURPOSE))
            with self.refused('foreign_state_root'):
                candidate.select(first['path'])

    def test_wrong_diagnostic_descriptor_never_executes(self):
        request = self.put(self.root / 'private/request.json', {'descriptor_ref': self.lock_ref})
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection), \
             patch.object(candidate.os, 'execve') as execute:
            prepared = candidate.prepare(Path(self.spec_ref['path']))
            with self.refused('diagnostic_descriptor_mismatch'):
                candidate.diagnose(prepared['path'], request['path'])
            execute.assert_not_called()

    def test_fixture_inspection_never_constructs_game_context(self):
        from unittest.mock import Mock
        context = Mock()
        context.inspect.return_value = {'scope': 'synthetic_fixture_inspection'}
        api = types.SimpleNamespace(FIELDS=set(self.descriptor), FixtureContext=Mock(return_value=context))
        types_module = types.ModuleType('pear_runtime.fixtures.types')
        types_module.Selection = Mock()
        game_module = types.ModuleType('tools.development.game.context')
        game_module.GameContext = Mock(side_effect=AssertionError('game inspection on fixture path'))
        with patch.object(candidate, 'load_runtime', return_value=api), \
             patch.dict('sys.modules', {'pear_runtime.fixtures.types': types_module,
                                       'tools.development.game.context': game_module}):
            result = candidate.inspect(self.spec_ref, kind='fixture')
        self.assertEqual(result['inspected_kind'], 'fixture')
        self.assertIsNone(result['game'])
        self.assertFalse(result['execution_authorized_by_this_record'])
        context.inspect.assert_called_once()
        game_module.GameContext.assert_not_called()

    def test_game_inspection_never_constructs_fixture_context(self):
        from unittest.mock import Mock
        game_ref = self.put(self.root / 'private/game-descriptor.json', self.descriptor)
        self.update_spec(game_descriptor_ref=game_ref)
        context = Mock(value=self.descriptor)
        context.inspect.return_value = {'scope': 'synthetic_game_inspection'}
        game_module = types.ModuleType('tools.development.game.context')
        game_module.GameContext = Mock(return_value=context)
        api = types.SimpleNamespace(FIELDS=set(self.descriptor),
            FixtureContext=Mock(side_effect=AssertionError('fixture inspection on game path')))
        with patch.object(candidate, 'load_runtime', return_value=api), \
             patch.dict('sys.modules', {'tools.development.game.context': game_module}):
            result = candidate.inspect(self.spec_ref)
        self.assertEqual(result['inspected_kind'], 'game')
        self.assertIsNone(result['fixture'])
        self.assertFalse(result['runtime_execution_performed'])
        api.FixtureContext.assert_not_called()
        game_module.GameContext.assert_called_once_with(game_ref)

    @contextmanager
    def isolated_runtime_imports(self):
        # Test-only isolation; production must refuse an already-loaded impostor.
        with patch.dict(sys.modules), patch.object(sys, 'path', list(sys.path)):
            for name in tuple(sys.modules):
                if name == 'pear_runtime' or name.startswith('pear_runtime.'):
                    del sys.modules[name]
            yield

    def runtime_package(self, root, label, *, marker=None):
        package = root / 'pear_runtime/fixtures'
        package.mkdir(parents=True, exist_ok=True)
        initializer = '' if marker is None else (
            'from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n')
        files = {
            'pear_runtime/__init__.py': initializer,
            'pear_runtime/fixtures/__init__.py': '',
            'pear_runtime/fixtures/types.py': 'class Selection:\n    def __init__(self,*args,**kwargs): pass\n',
            'pear_runtime/fixtures/context.py': (
                'FIELDS = set(' + repr(sorted(self.descriptor)) + ')\n'
                'class FixtureContext:\n    def __init__(self,*args,**kwargs): pass\n'
                '    def inspect(self,output): return {"imported_origin": ' + repr(label) + '}\n'),
        }
        notice = ('# SPDX-FileCopyrightText: 2026 Pear contributors\n'
                  '# SPDX-License-Identifier: GPL-3.0-or-later\n')
        for relative, body in files.items():
            (root / relative).write_text(notice + body)
        return list(files)

    def bind_runtime_package(self, paths):
        self.git('add', '.')
        self.git('-c', 'user.name=Selector test', '-c', 'user.email=selector@example.invalid',
                 'commit', '-qm', 'Synthetic runtime bootstrap')
        self.pin = self.git('rev-parse', 'HEAD').strip()
        self.spec['runtime_checkout']['commit'] = self.pin
        self.lock['tool_sources']['runtime'] = self.pin
        self.update_lock()
        rows = [dict(root='runtime', path=path, **candidate.compact(candidate.fact(self.runtime / path)))
                for path in paths]
        manifest = self.put(self.root / 'private/producers.json',
                            dict(roots={'runtime': str(self.runtime)}, files=rows))
        self.descriptor['producer_manifest_ref'] = manifest
        self.desc = self.put(self.root / 'private/descriptor.json', self.descriptor)
        self.update_spec(fixture_descriptor_ref=self.desc)
        return rows

    def runtime_bootstrap(self):
        return self.bind_runtime_package(self.runtime_package(self.runtime, 'selected-pinned-root'))

    def cli_import_case(self, selected_present):
        self.runtime_bootstrap()
        foreign = self.root / 'foreign-runtime'
        marker = self.root / 'foreign-imported'
        self.runtime_package(foreign, 'unadmitted-root', marker=marker)
        with patch.object(candidate, 'inspect', side_effect=self.synthetic_inspection):
            prepared = candidate.prepare(self.spec_ref['path'])
        pythonpath = [str(foreign)] + ([str(self.runtime)] if selected_present else [])
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('PYTHON', 'WINE', 'FEX', 'DYLD_'))}
        env.update(PYTHONPATH=os.pathsep.join(pythonpath), PYTHONDONTWRITEBYTECODE='1',
                   GIT_OPTIONAL_LOCKS='0')
        result = subprocess.run([sys.executable, '-B', '-m', 'tools.development.runtime_candidate',
                                 'inspect', '--prepared', prepared['path'], '--kind', 'fixture'],
                                cwd=candidate.PEAR_ROOT, env=env, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['fixture']['imported_origin'], 'selected-pinned-root')
        self.assertFalse(value['runtime_execution_performed'])
        self.assertFalse(marker.exists(), 'unadmitted package body executed')
        self.assertEqual(self.preview.read_bytes(), b'preserve original state')

    def test_cli_promotes_selected_runtime_already_on_pythonpath(self):
        self.cli_import_case(selected_present=True)

    def test_cli_adds_selected_runtime_absent_from_pythonpath(self):
        self.cli_import_case(selected_present=False)

    def test_unadmitted_bootstrap_initializer_refused_before_import(self):
        self.runtime_bootstrap()
        manifest = candidate.read_ref(self.descriptor['producer_manifest_ref'])
        manifest['files'] = [row for row in manifest['files'] if row['path'] != 'pear_runtime/__init__.py']
        self.descriptor['producer_manifest_ref'] = self.put(self.root / 'private/producers.json', manifest)
        with self.isolated_runtime_imports(), \
             patch.object(candidate.importlib, 'import_module') as imported, \
             self.refused('runtime_bootstrap_origin'):
            candidate.load_runtime(self.spec, self.descriptor)
        imported.assert_not_called()

    def test_foreign_package_resolution_refused_before_initializer(self):
        paths = self.runtime_package(self.runtime, 'selected-pinned-root')
        (self.runtime / 'pear_runtime/__init__.py').unlink()
        self.bind_runtime_package([path for path in paths if path != 'pear_runtime/__init__.py'])
        foreign = self.root / 'foreign-runtime'
        marker = self.root / 'foreign-imported'
        self.runtime_package(foreign, 'unadmitted-root', marker=marker)
        with self.isolated_runtime_imports(), \
             patch.object(candidate.importlib, 'import_module') as imported, \
             self.refused('runtime_bootstrap_origin'):
            sys.path[:0] = [str(foreign), str(self.runtime)]
            candidate.load_runtime(self.spec, self.descriptor)
        imported.assert_not_called()
        self.assertFalse(marker.exists())

    def test_bootstrap_source_symlink_refused_before_import(self):
        self.runtime_bootstrap()
        source = self.runtime / 'pear_runtime/fixtures/context.py'
        target = self.root / 'outside-context.py'
        target.write_bytes(source.read_bytes())
        source.unlink()
        source.symlink_to(target)
        with self.isolated_runtime_imports(), \
             patch.object(candidate.importlib, 'import_module') as imported, self.refused('path_alias'):
            candidate.load_runtime(self.spec, self.descriptor)
        imported.assert_not_called()

    def test_already_loaded_foreign_runtime_refused_unchanged(self):
        self.runtime_bootstrap()
        foreign = types.ModuleType('pear_runtime')
        foreign.__file__ = str(self.root / 'foreign-runtime/pear_runtime/__init__.py')
        with self.isolated_runtime_imports(), patch.object(candidate.importlib, 'import_module') as imported:
            sys.modules['pear_runtime'] = foreign
            with self.refused('loaded_runtime_origin'):
                candidate.load_runtime(self.spec, self.descriptor)
            self.assertIs(sys.modules['pear_runtime'], foreign)
        imported.assert_not_called()

    def test_loaded_package_foreign_search_path_refused(self):
        self.runtime_bootstrap()
        with self.isolated_runtime_imports():
            sys.path.insert(0, str(self.runtime))
            package = importlib.import_module('pear_runtime')
            package.__path__ = [str(self.root / 'foreign-runtime/pear_runtime')]
            with patch.object(candidate.importlib, 'import_module') as imported, \
                 self.refused('loaded_runtime_origin'):
                candidate.load_runtime(self.spec, self.descriptor)
            imported.assert_not_called()
            self.assertIs(sys.modules['pear_runtime'], package)

    def test_loaded_package_foreign_spec_refused(self):
        self.runtime_bootstrap()
        with self.isolated_runtime_imports():
            sys.path.insert(0, str(self.runtime))
            package = importlib.import_module('pear_runtime')
            package.__spec__ = importlib.util.spec_from_file_location(
                'pear_runtime', self.root / 'foreign-runtime/pear_runtime/__init__.py')
            with patch.object(candidate.importlib, 'import_module') as imported, \
                 self.refused('loaded_runtime_origin'):
                candidate.load_runtime(self.spec, self.descriptor)
            imported.assert_not_called()

    def test_loaded_selected_runtime_reused_with_canonical_package_paths(self):
        self.runtime_bootstrap()
        with self.isolated_runtime_imports():
            first = candidate.load_runtime(self.spec, self.descriptor)
            self.assertIs(candidate.load_runtime(self.spec, self.descriptor), first)
            self.assertEqual(sys.modules['pear_runtime'].__path__, [str(self.runtime / 'pear_runtime')])

    def fex_bootstrap(self):
        runtime_rows = self.runtime_bootstrap()
        root = self.root / 'fex'
        root.mkdir()
        source = root / 'observer.py'
        source.write_text('VALUE = 1\n')
        def command(*args):
            return subprocess.check_output(['/usr/bin/git', '-C', str(root), *args], text=True).strip()
        command('init', '-q')
        command('add', '.')
        command('-c', 'user.name=Selector test', '-c', 'user.email=selector@example.invalid',
                'commit', '-qm', 'Synthetic FEX tool source')
        pin = command('rev-parse', 'HEAD')
        self.lock['tool_sources']['fex'] = pin
        self.update_lock()
        ref = candidate.fact(source)
        manifest = self.put(self.root / 'private/fex-producer.json',
            dict(roots={'runtime': str(self.runtime), 'fex': str(root)},
                 files=runtime_rows + [dict(root='fex', path=source.name, **candidate.compact(ref))]))
        descriptor = {**self.descriptor, 'producer_manifest_ref': manifest}
        return root, source, descriptor

    def test_clean_pinned_fex_source_admitted_before_import(self):
        root, source, descriptor = self.fex_bootstrap()
        with self.isolated_runtime_imports():
            api = candidate.load_runtime(self.spec, descriptor)
            self.assertEqual(api.__file__, str(self.runtime / 'pear_runtime/fixtures/context.py'))
            self.assertEqual(sys.path[:2], [str(self.runtime), str(root)])

    def test_dirty_fex_source_refuses_before_import(self):
        root, source, descriptor = self.fex_bootstrap()
        source.write_text('VALUE = 2\n')
        with patch.object(candidate.importlib, 'import_module') as imported, self.refused('checkout_dirty'):
            candidate.load_runtime(self.spec, descriptor)
        imported.assert_not_called()

    def test_wrong_fex_checkpoint_refuses_before_import(self):
        root, source, descriptor = self.fex_bootstrap()
        self.lock['tool_sources']['fex'] = 'f' * 40
        self.update_lock()
        with patch.object(candidate.importlib, 'import_module') as imported, self.refused('checkout_commit'):
            candidate.load_runtime(self.spec, descriptor)
        imported.assert_not_called()

    def test_duplicate_json_refused(self):
        target = self.root / 'private/duplicate.json'
        target.write_text('{"x":1,"x":2}')
        with self.refused('duplicate_json_key'):
            candidate.read_ref(candidate.fact(target))

    def test_boolean_identity_refused(self):
        with self.refused('identity_value'):
            candidate.identity(dict(sha256='a' * 64, size_bytes=True))


if __name__ == '__main__':
    unittest.main()
