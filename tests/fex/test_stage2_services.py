"""Portable service outcome/command replay controls; no native fixture executes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from tools.fex import services
from tools.fex.common import Error


def valid():
    value={'schema_version':1,'record_kind':'fex_native_service_observation','scope':'fex_component','service_count':8,'cache_line_bytes':128,'pid':12345,'mapping_controls':7,'policy_controls':20,'owned_workers':2,'workers_joined':2,'software_tso_required':True,'descriptor_cleanup':True,'passed':True}
    value.update({key:services.UNSUPPORTED for key in ('hardware_tso_status','kernel_control_status','linux_advice_status','vma_naming_status','stats_status')})
    value.update({key:False for key in ('restricted_operations','fex_initialization','jit_execution','pe_execution','guest_execution')})
    return value


class ServiceOutcomeTests(unittest.TestCase):
    def test_finite_outcome_preserves_unsupported_services(self):
        self.assertEqual(services.observation(json.dumps(valid()).encode(),128),valid())

    def test_incomplete_abi_workers_policy_cleanup_or_geometry_rejected(self):
        for name,value in (('service_count',7),('workers_joined',1),('policy_controls',19),('descriptor_cleanup',False),('cache_line_bytes',64),('pid',0),('pid',True)):
            with self.subTest(name=name,value=value):
                data=valid();data[name]=value
                with self.assertRaises(Error):services.observation(json.dumps(data).encode(),128)

    def test_fake_acceleration_and_runtime_overclaims_rejected(self):
        for name in ('hardware_tso_status','kernel_control_status','linux_advice_status','vma_naming_status','stats_status','guest_execution','fex_initialization','jit_execution','pe_execution','restricted_operations'):
            with self.subTest(name=name):
                data=valid();data[name]=0 if name.endswith('_status') else True
                with self.assertRaises(Error):services.observation(json.dumps(data).encode(),128)
        data=valid();data['runtime_qualified']=True
        with self.assertRaisesRegex(Error,'service_observation_fields'):services.observation(json.dumps(data).encode(),128)


class ServiceCommandReplayTests(unittest.TestCase):
    def fixture(self,root):
        recipe={role:['qualified-fixture',role] for role in services.ROLES};rows=[]
        for role,argv in recipe.items():
            logs=root/'logs'/role;logs.mkdir(parents=True)
            row={'id':role,'argv':argv,'cwd':str(root),'environment':services.ENV,'returncode':0,'elapsed_ms':1,'status':'completed','logs':{}}
            for stream in ('stdout','stderr'):
                raw=json.dumps(valid()).encode() if stream=='stdout' else b''
                path=logs/(stream+'.bin');path.write_bytes(raw)
                row['logs'][stream]={'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)}
            rows.append(row)
        return recipe,rows

    def test_exact_private_command_logs_replay_and_detect_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);recipe,rows=self.fixture(root)
            self.assertEqual(set(services.command_rows(root,rows,recipe)),set(services.ROLES))
            (root/'logs/arm64ec/stdout.bin').write_bytes(b'changed')
            with self.assertRaisesRegex(Error,'service_log_changed'):services.command_rows(root,rows,recipe)

    def test_missing_duplicate_failed_or_changed_commands_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);recipe,rows=self.fixture(root)
            changed=copy.deepcopy(rows);changed[1]=copy.deepcopy(changed[0])
            for candidates in (rows[:1],changed):
                with self.assertRaisesRegex(Error,'service_command_closure'):services.command_rows(root,candidates,recipe)
            for key,value in (('returncode',1),('argv',['other-program']),('environment',{'DYLD_INSERT_LIBRARIES':'other'})):
                changed=copy.deepcopy(rows);changed[0][key]=value
                with self.assertRaisesRegex(Error,'service_command_recipe'):services.command_rows(root,changed,recipe)


class ServiceFailureReceiptTests(unittest.TestCase):
    def test_bounded_failure_preserves_command_and_existing_stream_without_fake_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);rows=[]
            def failure(argv,**kwargs):
                (kwargs['output_dir']/'stderr.bin').write_bytes(b'finite fixture timeout')
                raise Error('command_timeout')
            with mock.patch.object(services,'bounded_command',side_effect=failure):
                with self.assertRaisesRegex(Error,'command_timeout'):services.run_command(root,'arm64ec',['admitted-fixture'],rows)
            self.assertEqual(len(rows),1);self.assertIsNone(rows[0]['returncode']);self.assertEqual(rows[0]['status'],'failed')
            self.assertEqual(rows[0]['error'],'command_timeout');self.assertEqual(rows[0]['logs']['stderr']['size_bytes'],22)
            self.assertNotIn('stdout',rows[0]['logs'])

if __name__=='__main__':unittest.main()
