# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Current companion/gate bindings; all observers and sessions are synthetic."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import time
import unittest
from unittest.mock import Mock,patch

from tools.development.game import adapter,feedback,inputs,witness


class CurrentPolicyBindings(unittest.TestCase):
    def test_partial_session_failure_closes_exact_observer(self):
        observer=SimpleNamespace(close=Mock());failure=RuntimeError('selector failed')
        namespace=SimpleNamespace(DarwinObserver=Mock(return_value=observer),Session=Mock(side_effect=failure))
        with self.assertRaisesRegex(RuntimeError,'selector failed') as caught:
            adapter.companion_session(namespace,Path('/synthetic'))
        self.assertIs(caught.exception,failure);observer.close.assert_called_once()
        namespace.Session.assert_called_once_with(Path('/synthetic'),observer=observer)

    def test_partial_cleanup_failure_preserves_original_failure(self):
        original=RuntimeError('original');observer=SimpleNamespace(close=Mock(side_effect=RuntimeError('cleanup')))
        namespace=SimpleNamespace(DarwinObserver=Mock(return_value=observer),Session=Mock(side_effect=original))
        with self.assertRaises(RuntimeError) as caught:adapter.companion_session(namespace,Path('/synthetic'))
        self.assertIs(caught.exception,original);self.assertIn('cleanup',caught.exception.__notes__[0])

    def test_prelaunch_failure_closes_created_companions_and_restores_main_queue(self):
        main_queue=object();tap=object();closed=[]
        def session(name):
            return SimpleNamespace(selector=SimpleNamespace(close=lambda:closed.append(name+' selector')),
                observer=SimpleNamespace(close=lambda:closed.append(name+' observer')))
        value=SimpleNamespace(session=SimpleNamespace(observer=SimpleNamespace(queue=tap)),tap=tap,
                              helpers=session('witness'),hud_helpers=session('hud'))
        original=RuntimeError('construction');adapter.close_unlaunched(value,main_queue,original)
        self.assertIs(value.session.observer.queue,main_queue)
        self.assertEqual(closed,['hud selector','hud observer','witness selector','witness observer'])

    def test_hud_construction_failure_also_closes_first_original_session(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();queue=object();closed=[];observer_count=[]
            def observer():
                observer_count.append(1)
                return SimpleNamespace(queue=object(),close=lambda:closed.append('observer'+str(len(observer_count))))
            def make(output,*,observer):
                if Path(output).name=='hud':raise RuntimeError('HUD selector failed')
                return SimpleNamespace(observer=observer,selector=SimpleNamespace(close=lambda:closed.append('selector')))
            namespace=SimpleNamespace(DarwinObserver=observer,Session=make)
            gate=SimpleNamespace(check=lambda *a:({'operation_id':'op'},{'play_observation':{'hold_seconds':1800}}),
                grant=lambda *a:dict(maximum_play_seconds=1800,not_after_monotonic_ns=time.monotonic_ns()+10**12))
            session=SimpleNamespace(observer=SimpleNamespace(queue=queue))
            with self.assertRaisesRegex(RuntimeError,'HUD selector failed'):
                adapter.Adapter(session=session,output=root,candidate=SimpleNamespace(name='d25-game'),selection={},
                    sampler=None,deadline=None,launch=None,environment={},gate=gate,companion_factory=lambda:namespace)
            self.assertIs(session.observer.queue,queue);self.assertEqual(closed.count('selector'),1)
            self.assertEqual(len(closed),3)

    def test_gate_refusal_precedes_any_companion_or_output(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();factory=Mock();gate=SimpleNamespace(check=Mock(side_effect=RuntimeError('not current')))
            with self.assertRaisesRegex(RuntimeError,'not current'):
                adapter.Adapter(session=object(),output=root,candidate=object(),selection={},sampler=None,
                    deadline=None,launch=None,environment={},gate=gate,companion_factory=factory)
            factory.assert_not_called();self.assertFalse((root/'play').exists())

    def test_bound_factory_preserves_live_gate_and_captured_constructor(self):
        gate=object();companion=object();factory=feedback.bind_factory(gate=gate,companion_factory=companion)
        with patch.object(feedback,'FeedbackManualAdapter',return_value='adapter') as constructor:
            result=factory(session=1,output=2,candidate=3,selection=4,sampler=5,deadline=6,launch=7,environment=8)
        self.assertEqual(result,'adapter');self.assertIs(constructor.call_args.kwargs['gate'],gate)
        self.assertIs(constructor.call_args.kwargs['companion_factory'],companion)
        self.assertEqual(set(constructor.call_args.kwargs),{'session','output','candidate','selection','sampler',
            'deadline','launch','environment','gate','companion_factory'})

    def test_coordination_reader_keeps_floats_but_refuses_duplicate_nonfinite(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'record.json';p.write_text('{"seconds":0.25,"held":true}')
            self.assertEqual(inputs.coordination_read(p),{'seconds':0.25,'held':True})
            for data in ('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'):
                p.write_text(data)
                with self.assertRaises(Exception):inputs.coordination_read(p)

    def test_witness_provider_refusal_prevents_observer_and_protocol(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'config.json';p.write_text(json.dumps(dict(provider_root='/explicit',provider_ref={},source_refs={})))
            with (patch('pear_runtime.fixtures.supervision.companion_provider',side_effect=RuntimeError('provider changed')) as provider,
                  patch.object(witness,'witness') as protocol):
                with self.assertRaisesRegex(RuntimeError,'provider changed'):witness.main(['--config',str(p)])
            provider.assert_called_once_with('/explicit',provider_ref={},source_refs={});protocol.assert_not_called()

    def test_witness_frontend_passes_only_captured_original_observer(self):
        from contextlib import contextmanager
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'config.json';p.write_text(json.dumps(dict(provider_root='/explicit',provider_ref={'a':1},source_refs={'b':2})))
            observer=object();events=[]
            @contextmanager
            def provider(*args,**kwargs):
                events.append('before');yield SimpleNamespace(DarwinObserver=observer);events.append('after')
            with patch('pear_runtime.fixtures.supervision.companion_provider',provider),patch.object(witness,'witness') as protocol:
                witness.main(['--config',str(p)])
            protocol.assert_called_once_with(p,observer_factory=observer);self.assertEqual(events,['before','after'])

    def test_unpublished_hud_replacement_closes_when_old_handle_close_fails(self):
        from tools.development.game.manual import ManualAdapter
        for failed in ('selector','observer'):
            with self.subTest(failed=failed):
                old=SimpleNamespace(children={},selector=SimpleNamespace(close=Mock()),observer=SimpleNamespace(close=Mock()))
                getattr(old,failed).close.side_effect=RuntimeError('old '+failed+' close failed')
                replacement=SimpleNamespace(selector=SimpleNamespace(close=Mock()),observer=SimpleNamespace(close=Mock()))
                def parent(value,**kwargs):
                    value.hud_helpers=old;value.root=Path('/synthetic');value.companion_factory=lambda:SimpleNamespace()
                with (patch.object(ManualAdapter,'__init__',parent),
                      patch.object(feedback,'companion_session',return_value=replacement),
                      patch.object(feedback.FeedbackManualAdapter,'close') as close):
                    with self.assertRaisesRegex(RuntimeError,'old '+failed+' close failed'):feedback.FeedbackManualAdapter()
                replacement.selector.close.assert_called_once();replacement.observer.close.assert_called_once()
                close.assert_called_once()

    def test_witness_start_error_is_not_masked_by_companion_close_failure(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            observer=SimpleNamespace(queue=object(),identity=lambda pid:{'pid':pid},executable=lambda pid:'/synthetic/python')
            helper=SimpleNamespace(observer=observer,launch=Mock(return_value=SimpleNamespace(exited=False)),wait_for=lambda *args:False)
            namespace=SimpleNamespace()
            gate=SimpleNamespace(check=lambda *a:({'operation_id':'op'},{'play_observation':{'hold_seconds':1800}}),
                grant=lambda *a:dict(maximum_play_seconds=1800,not_after_monotonic_ns=time.monotonic_ns()+10**12),
                context=SimpleNamespace(child_environment=lambda env:{},witness_binding=lambda:{},
                    value={'helper_refs':{'python':{'path':'/synthetic/python'}}}))
            main=SimpleNamespace(observer=SimpleNamespace(queue=object()))
            with (patch.object(adapter,'companion_session',return_value=helper),
                  patch.object(adapter.play_window,'Windows',return_value=object()),
                  patch.object(adapter.Adapter,'close',side_effect=RuntimeError('cleanup failed'))):
                with self.assertRaisesRegex(Exception,'play_witness_start_timeout') as caught:
                    adapter.Adapter(session=main,output=root,candidate=SimpleNamespace(name='d25-game'),selection={},
                        sampler=None,deadline=None,launch=None,environment={},gate=gate,companion_factory=lambda:namespace)
            self.assertEqual(caught.exception.evidence_errors[0]['phase'],'companion-close')
            self.assertIn('cleanup failed',caught.exception.__notes__[0])

    def test_additive_companion_evidence_failure_keeps_original_error(self):
        primary=RuntimeError('original cleanup')
        with patch.object(adapter,'record_companions',side_effect=RuntimeError('evidence failed')):
            with self.assertRaises(RuntimeError) as caught:
                with adapter.companion_evidence(object()):raise primary
        self.assertIs(caught.exception,primary)
        self.assertEqual(primary.evidence_errors[0]['phase'],'companion-evidence')

    def test_partial_cleanup_records_child_maps_even_after_cleanup_failure(self):
        primary=RuntimeError('construction');queue=object()
        value=SimpleNamespace(session=SimpleNamespace(observer=SimpleNamespace(queue=queue)),
            helpers=SimpleNamespace(selector=SimpleNamespace(close=Mock(side_effect=RuntimeError('close failed'))),
                                    observer=SimpleNamespace(close=Mock())))
        with patch.object(adapter,'record_companions') as record:
            adapter.close_unlaunched(value,queue,primary)
        record.assert_called_once_with(value);self.assertTrue(primary.evidence_errors)


if __name__=='__main__':unittest.main()
