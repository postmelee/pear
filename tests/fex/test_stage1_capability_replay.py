"""Reject command/target/policy mutations without claiming real compilations."""
import copy
from pathlib import Path
import sys
import struct
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.fex import check, verify
from tools.fex.common import Error, load_json, sha256

class RecipeReplay(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.prepared=self.root/'prepared';self.tc=self.root/'cross'
        self.lock=load_json(ROOT/'runtime/fex/toolchain.json')
        self.config=load_json(ROOT/'runtime/fex/build-config.json')
        self.data={'commands':[]}
        for ident,argv in check.command_recipe(self.root,self.prepared,self.tc,self.lock).items():
            logs={}
            for name in ('stdout','stderr'):
                p=self.root/'logs'/ident/(name+'.bin');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
                logs[name]={'path':p.relative_to(self.root).as_posix(),'sha256':sha256(p),'size_bytes':p.stat().st_size}
            self.data['commands'].append({'id':ident,'argv':argv,'exit_code':0,'elapsed_ms':0,
                'environment':check.environment_contract(self.tc,self.lock,self.config),'logs':logs})
    def replay(self,value):
        return verify.verify_command_receipts(value,self.root,self.prepared,self.tc,self.lock,self.config)
    def command(self,value,name):return next(r for r in value['commands'] if r['id']==name)
    def test_complete_recipe_control_is_accepted(self):self.replay(self.data)
    def test_wrong_compiler_fixture_header_target_or_dynamic_link_is_refused(self):
        for name,index,replacement in [('arm64ec.language',3,'/usr/bin/clang'),
            ('arm64ec.layout',-3,'other.cpp'),('arm64ec.layout',8,'-I/other'),
            ('arm64ec.static-link',9,'-dynamic'),('arm64ec.source-imports',4,'arm64')]:
            value=copy.deepcopy(self.data);self.command(value,name)['argv'][index]=replacement
            with self.subTest(name=name,index=index),self.assertRaises(Error):self.replay(value)
    def test_incomplete_duplicate_failed_or_extra_commands_are_refused(self):
        values=[]
        value=copy.deepcopy(self.data);value['commands'].pop();values.append(value)
        value=copy.deepcopy(self.data);value['commands'].append(value['commands'][0]);values.append(value)
        value=copy.deepcopy(self.data);value['commands'][0]['exit_code']=1;values.append(value)
        value=copy.deepcopy(self.data);value['commands'][0]['argv'].append('-Wl,--unresolved-symbols=ignore-all');values.append(value)
        for value in values:
            with self.assertRaises(Error):self.replay(value)
    def test_changed_deployment_environment_and_log_bytes_are_refused(self):
        value=copy.deepcopy(self.data);value['commands'][0]['environment']['MACOSX_DEPLOYMENT_TARGET']='11.0'
        with self.assertRaises(Error):self.replay(value)
        p=self.root/self.data['commands'][0]['logs']['stdout']['path'];p.write_bytes(b'changed')
        with self.assertRaises(Error):self.replay(self.data)
    def test_log_stream_omission_and_path_substitution_are_refused(self):
        value=copy.deepcopy(self.data);del value['commands'][0]['logs']['stderr']
        with self.assertRaises(Error):self.replay(value)
        value=copy.deepcopy(self.data);value['commands'][0]['logs']['stdout']['path']='logs/other/stdout.bin'
        with self.assertRaises(Error):self.replay(value)

class BuildPolicy(unittest.TestCase):
    def setUp(self):self.config=load_json(ROOT/'runtime/fex/build-config.json');self.digest=sha256(ROOT/'runtime/fex/inputs.json')
    def test_current_policy_is_accepted(self):check.validate_config(self.config,self.digest)
    def test_changed_ordering_cache_overrides_or_qualification_are_refused(self):
        for name,value in [('TSOEnabled',False),('DiskCache',True),('ProfileStats',True)]:
            config=copy.deepcopy(self.config);config['runtime_options'][name]=value
            with self.subTest(name=name),self.assertRaises(Error):check.validate_config(config,self.digest)
        for name,value in [('unsupported_override_policy','ignore'),('deployment_target','11.0'),
                            ('host_architecture','x86_64'),('native_root_cmake_status','ready')]:
            config=copy.deepcopy(self.config);config[name]=value
            with self.subTest(name=name),self.assertRaises(Error):check.validate_config(config,self.digest)
    def test_missing_static_dependency_flags_are_refused(self):
        config=copy.deepcopy(self.config);config['link_flags'].remove('-nodefaultlibs')
        with self.assertRaises(Error):check.validate_config(config,self.digest)

class DefaultCRTMetadataReader(unittest.TestCase):
    def image(self,version=1):
        # Original format-reader bytes, never compiled, linked or executed.
        data=bytearray(2560);data[:2]=b'MZ';struct.pack_into('<I',data,60,128)
        data[128:132]=b'PE\0\0';struct.pack_into('<HH',data,132,0x8664,2)
        struct.pack_into('<H',data,148,240);opt=152;base=0x180000000
        struct.pack_into('<H',data,opt,0x20b);struct.pack_into('<Q',data,opt+24,base);struct.pack_into('<I',data,opt+32,4096)
        struct.pack_into('<I',data,opt+56,0x4000);struct.pack_into('<I',data,opt+108,16)
        struct.pack_into('<II',data,opt+112+80,0x2000,232)
        for i,(rva,raw,size,flags) in enumerate([(0x1000,512,512,0x60000020),(0x2000,1024,1024,0x40000040)]):
            at=opt+240+i*40;struct.pack_into('<IIII',data,at+8,size,rva,size,raw);struct.pack_into('<I',data,at+36,flags)
        struct.pack_into('<I',data,1024,232);struct.pack_into('<Q',data,1024+200,base+0x2100)
        struct.pack_into('<III',data,1280,version,0x2180,2)
        struct.pack_into('<IIII',data,1408,0x1001,128,0x1082,128)
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);p=Path(tmp.name)/'format.dll';p.write_bytes(data);return p
    def test_default_crt_version_one_with_mapped_ec_and_x64_ranges(self):
        self.assertEqual(check.inspect_fixture_arm64ec(self.image())['chpe_version'],1)
    def test_other_versions_cannot_be_guessed_supported(self):
        for version in (0,2,3):
            with self.subTest(version=version),self.assertRaises(Error):check.inspect_fixture_arm64ec(self.image(version))

class ClosedCheckEvidence(unittest.TestCase):
    def test_private_fields_duplicate_flags_or_facts_cannot_be_exported(self):
        facts={'aarch64':{'outer_machine':0xaa64},'arm64ec':{'outer_machine':0x8664}}
        rows=[{'id':'input-and-tool-closure','status':'passed','required':True},
              {'id':'aarch64-cxx20-layout-static-link','status':'passed','required':True,'pe_facts':facts['aarch64'],'pe_execution':False},
              {'id':'arm64ec-cxx20-layout-static-link','status':'passed','required':True,'pe_facts':facts['arm64ec'],'pe_execution':False},
              {'id':'static-runtime-member-inventory','status':'passed','required':True}]
        verify.verify_checks(rows,facts)
        mutations=[]
        value=copy.deepcopy(rows);value[1]['pe_execution']=True;mutations.append(value)
        value=copy.deepcopy(rows);value[1]['pe_facts']['outer_machine']=99;mutations.append(value)
        value=copy.deepcopy(rows);value[0]['private_path']='/private/example';mutations.append(value)
        value=copy.deepcopy(rows);value.append(value[0]);mutations.append(value)
        for value in mutations:
            with self.assertRaises(Error):verify.verify_checks(value,facts)

class LinkMemberEvidence(unittest.TestCase):
    def map(self,text):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        p=Path(tmp.name)/'map';p.write_text(text);return p
    def selected(self):
        return '\n'.join(' 0001:00001000 '+symbol+' 0000000180001000     '+library+':member.o' for library,symbol in
            [('libc++','_ZNSt3__16chrono12steady_clock3nowEv'),('libc++abi','__cxa_guard_acquire'),
             ('libunwind','_Unwind_GetIP'),('libclang_rt.builtins-aarch64','__udivti3')])
    def test_actual_member_and_symbol_rows_are_required(self):
        result=check.link_contributions(self.map(self.selected()))
        self.assertEqual(set(result),{'libc++.a','libc++abi.a','libunwind.a','compiler-builtins'})
    def test_symbol_from_fixture_or_library_flag_is_insufficient(self):
        for text in (self.selected().replace('libunwind:member.o','fixture.obj'),
                     self.selected().replace('_Unwind_GetIP','unrelated'),
                     '-lunwind _Unwind_GetIP\n'+self.selected().replace('libunwind:member.o','fixture.obj')):
            with self.assertRaises(Error):check.link_contributions(self.map(text))

if __name__=='__main__':unittest.main()
