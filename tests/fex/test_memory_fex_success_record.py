"""Pure successful-record serialization controls; no actual build assertion."""
from copy import deepcopy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
REPO=Path(os.environ.get('PEAR_FEX_TEST_REPO',Path(__file__).resolve().parents[2])).resolve(strict=True)
sys.path.insert(0,str(REPO))
from tools.fex import memory_fex_check as e, memory_fex_build as b


def shape(items=0):
    # Finite injected evidence shape; only the serialization/scope functions
    # execute. The full source/tool/artifact verifier is never substituted.
    value={'schema_version':1,'record_kind':'fex_memory_modules_build','scope':'fex_component',
        'bindings':{},'producer_sha256':{},'input_snapshots':[],'materialized_source':{},'wire':{},
        'source_interfaces':{},'commands':[],'artifacts':[],'module_proofs':{'injected_nodes':[0]*items},
        'resources':{},'output_manifest':{},'modules_built_not_loaded':True,
        'qualification':dict(e.QUALIFICATION),'passed':True,**dict.fromkeys(e.FALSE_FLAGS,False)}
    return value


class SuccessfulRecord(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='pear-success-record-')
        self.addCleanup(self.temporary.cleanup);self.root=Path(self.temporary.name).resolve()
    def refuse(self,value):
        with self.assertRaises(e.Error):e.encoded_successful_build_record(value)
    def test_small_complete_record_roundtrips(self):
        value=shape();raw=e.encoded_successful_build_record(value)
        self.assertEqual(e.decode_successful_build_record(raw),value)
    def test_only_successful_record_can_use_extended_node_scope(self):
        value=shape(250100);raw=e.encoded(value)
        with self.assertRaises(e.Error):e.decode_json(raw,max_bytes=8*1024**2)
        self.assertEqual(e.decode_successful_build_record(raw),value)
    def test_generic_failure_decoder_limit_unchanged(self):
        (self.root/'failure.json').write_bytes(e.encoded({'failure_nodes':[0]*250100}))
        with self.assertRaises(e.Error):e.record_bytes(self.root,'failure.json')
    def test_generic_other_record_decoder_limit_unchanged(self):
        (self.root/'other.json').write_bytes(e.encoded({'other_nodes':[0]*250100}))
        with self.assertRaises(e.Error):e.record_bytes(self.root,'other.json')
    def test_named_failed_build_does_not_admit(self):
        value=shape(250100);value['passed']=False
        with self.assertRaises(e.Error):e.decode_successful_build_record(e.encoded(value))
    def test_explicit_success_bound_still_refuses_over_capacity(self):
        value=shape(500100)
        with self.assertRaises(e.Error):e.decode_successful_build_record(e.encoded(value))
    def test_writer_refuses_over_capacity_before_file_creation(self):
        with self.assertRaises(e.Error):b.write_successful_build_record(self.root,shape(500100))
        self.assertFalse((self.root/'build.json').exists())
    def test_byte_bound_retained(self):
        raw=e.encoded(shape());raw+=b' '*(8*1024**2+1-len(raw))
        with self.assertRaises(e.Error):e.decode_successful_build_record(raw)
    def test_depth_bound_retained(self):
        value=shape();tail=0
        for _ in range(66):tail=[tail]
        value['module_proofs']={'deep':tail};self.refuse(value)
    def test_duplicate_key_refused(self):
        raw=e.encoded(shape()).replace(b'"schema_version": 1,',b'"schema_version": 1,"schema_version": 1,')
        with self.assertRaises(e.Error):e.decode_successful_build_record(raw)
    def test_fractional_value_refused(self):
        value=shape();value['module_proofs']={'fraction':1.5};self.refuse(value)
    def test_large_integer_refused(self):
        value=shape();value['module_proofs']={'integer':2**53};self.refuse(value)
    def test_unknown_field_refused(self):
        value=shape();value['runtime_ready']=True;self.refuse(value)
    def test_missing_field_refused(self):
        value=shape();value.pop('artifacts');self.refuse(value)
    def test_wrong_record_kind_refused(self):
        value=shape();value['record_kind']='fex_memory_artifact_assessment';self.refuse(value)
    def test_wrong_scope_refused(self):
        value=shape();value['scope']='runtime';self.refuse(value)
    def test_failed_record_refused(self):
        value=shape();value['passed']=False;self.refuse(value)
    def test_not_complete_module_record_refused(self):
        value=shape();value['modules_built_not_loaded']=False;self.refuse(value)
    def test_version_bool_refused(self):
        value=shape();value['schema_version']=True;self.refuse(value)
    def test_qualification_flags_stay_closed(self):
        for key in e.FALSE_FLAGS:
            with self.subTest(key=key):
                value=shape();value[key]=True;self.refuse(value)
    def test_unperformed_qualification_metadata_refused_if_changed(self):
        value=shape();value['qualification']['aggregate_metadata']='passed';self.refuse(value)
    def test_nonlossless_nested_shape_refused(self):
        value=shape();value['module_proofs']={'tuple':(1,2)};self.refuse(value)
    def test_fixed_build_filename_roundtrips_actual_writer_bytes(self):
        value=shape(250100);ref=b.write_successful_build_record(self.root,value)
        decoded,raw=e.successful_build_record_bytes(self.root)
        self.assertEqual(decoded,value);self.assertEqual(raw,e.encoded_successful_build_record(value))
        self.assertEqual(ref,{'path':'build.json','sha256':e.H(raw)})
        self.assertEqual((self.root/'build.json').stat().st_mode&0o777,0o600)
    def test_existing_record_is_never_replaced(self):
        (self.root/'build.json').write_bytes(b'keep original')
        with self.assertRaises(FileExistsError):b.write_successful_build_record(self.root,shape())
        self.assertEqual((self.root/'build.json').read_bytes(),b'keep original')
    def test_readback_difference_is_not_success(self):
        with patch.object(e,'successful_build_record_bytes',return_value=(shape(),b'changed')):
            with self.assertRaises(e.Error):b.write_successful_build_record(self.root,shape())
    def test_failed_root_refuses_before_extended_success_reader(self):
        (self.root/'failure.json').write_bytes(b'keep failure')
        with patch.object(e,'operation_output',return_value=self.root),patch.object(e,'successful_build_record_bytes',side_effect=AssertionError('not admitted'))as decode:
            with self.assertRaises(e.Error):e.verify_build(self.root,repo=self.root)
        decode.assert_not_called()
    def test_failed_writer_primary_error_is_preserved(self):
        original=OSError(28,'injected storage failure')
        with patch.object(e,'encoded_successful_build_record',side_effect=original):
            with self.assertRaises(OSError)as caught:b.write_successful_build_record(self.root,shape())
        self.assertIs(caught.exception,original);self.assertFalse((self.root/'build.json').exists())


if __name__=='__main__':unittest.main()
