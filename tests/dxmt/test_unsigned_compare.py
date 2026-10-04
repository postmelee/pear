import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tools/dxmt'))
import compare as c
class StrictComparison(unittest.TestCase):
 def setUp(self):
  self.holder=tempfile.TemporaryDirectory();self.root=Path(self.holder.name).resolve()
  (self.root/'lib').mkdir();(self.root/'lib/data').write_bytes(b'owned plain-byte fixture')
 def tearDown(self):self.holder.cleanup()
 def rows(self):return c.scan_tree(self.root)
 def test_equal_only_unsigned_not_runtime(self):
  rows=self.rows();result=c.compare_entries(rows,copy.deepcopy(rows))
  self.assertTrue(result['raw_equal']);self.assertFalse(result['reconstruction_complete'])
  for key in ['native_execution_performed','hybrid_execution_performed','translated_guest_execution_performed','runtime_eligible','game_qualified','distribution_qualified']:self.assertIs(result[key],False)
 def test_changed_bytes_refuse_with_hashes(self):
  old=self.rows();(self.root/'lib/data').write_bytes(b'different plain bytes');result=c.compare_entries(old,self.rows())
  self.assertFalse(result['raw_equal']);self.assertIn('sha256',result['differences'][0]['changed_fields']);self.assertEqual(result['normalization_policy'],'none')
 def test_file_mode_difference(self):
  old=self.rows();(self.root/'lib/data').chmod(0o600);self.assertEqual(c.compare_entries(old,self.rows())['differences'][0]['changed_fields'],['mode'])
 def test_directory_mode_difference(self):
  old=self.rows();(self.root/'lib').chmod(0o700);self.assertFalse(c.compare_entries(old,self.rows())['raw_equal'])
 def test_omission_and_extra_file(self):
  old=self.rows();(self.root/'lib/data').unlink();(self.root/'lib/extra').write_bytes(b'data')
  self.assertEqual([r['path']for r in c.compare_entries(old,self.rows())['differences']],['lib/data','lib/extra'])
 def test_hardlink_refused(self):
  os.link(self.root/'lib/data',self.root/'lib/extra')
  with self.assertRaises(c.Error):self.rows()
 def test_contained_leaf_link_preserved(self):
  (self.root/'lib/alias').symlink_to('data');self.assertEqual(next(r['target']for r in self.rows()if r['kind']=='symlink'),'data')
 def test_changed_contained_link_target(self):
  (self.root/'lib/other').write_bytes(b'owned plain-byte fixture');(self.root/'lib/alias').symlink_to('data');old=self.rows()
  (self.root/'lib/alias').unlink();(self.root/'lib/alias').symlink_to('other');self.assertIn('target',c.compare_entries(old,self.rows())['differences'][0]['changed_fields'])
 def test_parent_relative_contained_link(self):
  (self.root/'other').mkdir();(self.root/'other/link').symlink_to('../lib/data');self.assertTrue(self.rows())
 def test_absolute_or_escaped_link(self):
  for target in ['/etc/passwd','../../etc/passwd']:
   with self.subTest(target=target):
    (self.root/'lib/alias').symlink_to(target)
    with self.assertRaises(c.Error):self.rows()
    (self.root/'lib/alias').unlink()
 def test_cycle_and_directory_alias(self):
  (self.root/'lib/a').symlink_to('b');(self.root/'lib/b').symlink_to('a')
  with self.assertRaises(c.Error):self.rows()
  (self.root/'lib/a').unlink();(self.root/'lib/b').unlink();(self.root/'alias').symlink_to('lib')
  with self.assertRaises(c.Error):self.rows()
 def test_missing_component_before_parent_is_not_lexically_normalized(self):
  (self.root/'lib/alias').symlink_to('missing/../data')
  with self.assertRaisesRegex(c.Error,'link_missing_target'):self.rows()
 def test_file_component_before_parent_is_refused(self):
  (self.root/'lib/alias').symlink_to('data/../data')
  with self.assertRaisesRegex(c.Error,'link_component'):self.rows()
 def test_actual_directory_before_parent_has_real_contained_meaning(self):
  (self.root/'lib/sub').mkdir();(self.root/'lib/alias').symlink_to('sub/../data');self.assertTrue(self.rows())
 def test_mode_changed_after_read_is_refused(self):
  real=c.os.read;changed=False
  def mutate(fd,size):
   nonlocal changed
   data=real(fd,size)
   if data and not changed:changed=True;(self.root/'lib/data').chmod(0o600)
   return data
  with patch.object(c.os,'read',side_effect=mutate),self.assertRaises(c.Error):self.rows()
 def test_root_alias(self):
  alias=self.root.parent/(self.root.name+'-alias');alias.symlink_to(self.root)
  try:
   with self.assertRaises(c.Error):c.scan_tree(alias)
  finally:alias.unlink()
 def test_source_replaced_during_read(self):
  real=c.os.read;replaced=False
  def changed(fd,size):
   nonlocal replaced
   data=real(fd,size)
   if data and not replaced:replaced=True;(self.root/'lib/data').unlink();(self.root/'lib/data').write_bytes(b'new source')
   return data
  with patch.object(c.os,'read',side_effect=changed),self.assertRaises(c.Error):self.rows()
 def test_unsafe_duplicate_paths(self):
  good=self.rows()
  for name in ['../data','/data','lib//data','lib/./data','lib/../data','lib\\data','lib/\x00data']:
   rows=copy.deepcopy(good);rows[-1]['path']=name
   with self.subTest(name=name),self.assertRaises(c.Error):c.validate_entries(rows)
  with self.assertRaises(c.Error):c.validate_entries(good+[good[-1]])
 def test_bool_mode_size_and_unknown_success(self):
  for key,value in [('mode',False),('size_bytes',True),('runtime_eligible',True)]:
   rows=self.rows();rows[-1][key]=value
   with self.subTest(key=key),self.assertRaises(c.Error):c.validate_entries(rows)
 def test_exact_old_manifest(self):
  rows=self.rows();manifest={'schema_version':1,'record_kind':'wine_build_inventory','files':[{k:r[k]for k in ['path','mode','size_bytes','sha256']}for r in rows if r['kind']=='file'],'symlinks':[]}
  self.assertEqual(c.check_wine_manifest(rows,manifest),rows)
  for change in ['missing','digest','alias','bool_version']:
   changed=copy.deepcopy(manifest)
   if change=='missing':changed['files']=[]
   elif change=='digest':changed['files'][0]['sha256']='0'*64
   elif change=='alias':changed['symlinks']=[{'path':'lib/absent','target':'data'}]
   else:changed['schema_version']=True
   with self.subTest(change=change),self.assertRaises(c.Error):c.check_wine_manifest(rows,changed)
 def prepare_overlay(self):
  for name in ['lib/wine','lib/wine/aarch64-unix','lib/wine/aarch64-windows','libexec']:(self.root/name).mkdir()
  for name in ['lib/wine/aarch64-unix/winemac.so','lib/wine/aarch64-windows/winemac.drv']:(self.root/name).write_bytes(b'old plain fixture')
  return [{'path':p,'kind':'file','mode':0o644,'size_bytes':3,'sha256':c.digest(b'new')}for p in c.REPLACEMENTS]
 def test_closed_overlay_preserves_base_data(self):
  replacements=self.prepare_overlay();rows=self.rows();changed=c.overlay_wine(rows,replacements)
  self.assertEqual(next(r for r in changed if r['path']=='lib/data'),next(r for r in rows if r['path']=='lib/data'))
  with self.assertRaises(c.Error):c.overlay_wine(rows,replacements[:-1])
  wrong=copy.deepcopy(replacements);wrong[-1]['path']='libexec/foreign.exe'
  with self.assertRaises(c.Error):c.overlay_wine(rows,wrong)
 def test_unplanned_existing_addition(self):
  replacements=self.prepare_overlay();(self.root/'lib/wine/aarch64-unix/winemetal.so').write_bytes(b'fixture')
  with self.assertRaises(c.Error):c.overlay_wine(self.rows(),replacements)
 def test_unknown_metadata_never_normalized(self):
  old=self.rows();changed=copy.deepcopy(old);changed[-1]['sha256']=c.digest(b'metadata or code unknown')
  result=c.compare_entries(old,changed);self.assertFalse(result['raw_equal']);self.assertEqual(result['normalization_policy'],'none')
if __name__=='__main__':unittest.main(verbosity=2)
