"""Finite source-only Git discovery regression; no FEX build/initialization.

Only private temporary Git repositories and fixed Git init/apply commands run.
The genuine nested-directory test replaces the large selected source proof with
an explicit two-file source fixture; no graph/runtime qualification is inferred.
"""
import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
_repository=Path(os.environ.get('PEAR_FEX_TEST_REPO',Path(__file__).resolve().parents[2])).resolve(strict=True)
sys.path.insert(0,str(_repository))
from tools.fex import memory_fex_source as source,memory_fex_check as evidence
H=lambda b:hashlib.sha256(b).hexdigest()
COMMAND_OBSERVATIONS=[]
FIXTURE_OBSERVATIONS=[]

class _SourceFixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-source-git-')
        self.root=Path(self.temp.name).resolve();self.output=self.root/'output';self.output.mkdir()
    def tearDown(self):self.temp.cleanup()
class SourceGitEnvironment(_SourceFixture):
    def test_canonical_output_is_exact_single_ceiling_and_home_is_preserved(self):
        value=source.git_environment(self.output)
        expected={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','GIT_CONFIG_NOSYSTEM':'1',
                  'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CEILING_DIRECTORIES':str(self.output)}
        if 'HOME' in os.environ:expected['HOME']=os.environ['HOME']
        self.assertEqual(value,expected)
    def test_inherited_git_directory_worktree_and_ceiling_are_not_forwarded(self):
        with patch.dict(os.environ,{'GIT_DIR':'/not-owned','GIT_WORK_TREE':'/not-owned','GIT_CEILING_DIRECTORIES':'/not-owned'}):
            value=source.git_environment(self.output)
        self.assertNotIn('GIT_DIR',value);self.assertNotIn('GIT_WORK_TREE',value)
        self.assertEqual(value['GIT_CEILING_DIRECTORIES'],str(self.output))
    def test_absent_home_remains_absent(self):
        with patch.dict(os.environ,{},clear=True):value=source.git_environment(self.output)
        self.assertNotIn('HOME',value)
    def test_symlink_alias_directory_refused(self):
        alias=self.root/'alias';alias.symlink_to(self.output)
        with self.assertRaises(evidence.Error):source.git_environment(alias)
    def test_relative_or_file_boundary_refused(self):
        file=self.root/'file';file.write_bytes(b'x')
        for path in (Path('relative-output'),file):
            with self.subTest(path=path),self.assertRaises(evidence.Error):source.git_environment(path)
    def test_colon_delimited_path_cannot_be_a_single_ceiling(self):
        output=self.root/'output:second';output.mkdir()
        with self.assertRaises(evidence.Error):source.git_environment(output)

class GenuineNestedGitSource(_SourceFixture):
    def basic_environment(self):
        value={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
        if 'HOME' in os.environ:value['HOME']=os.environ['HOME']
        return value
    def capture(self,argv,cwd,env,*,runner=None,**kwargs):
        actual=(runner or subprocess.run)(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,**kwargs)
        COMMAND_OBSERVATIONS.append({'argv':list(argv),'cwd':str(cwd),'environment':dict(env),
            'exit_code':actual.returncode,'stdout_sha256':H(actual.stdout),'stdout_bytes':len(actual.stdout),
            'stderr_sha256':H(actual.stderr),'stderr_bytes':len(actual.stderr),
            'raw_stdout':actual.stdout.decode('utf-8'),'raw_stderr':actual.stderr.decode('utf-8')})
        return actual
    def file(self,path,data):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(0o644);return path
    def inventory(self,root):
        return [{'path':str(p.relative_to(root)),'sha256':H(p.read_bytes()),'mode':p.stat().st_mode&0o777}
                for p in sorted(root.rglob('*')) if p.is_file()]
    def test_genuine_parent_repository_skip_and_production_ceiling_application(self):
        ambient=self.root/'ambient';ambient.mkdir();env=self.basic_environment()
        initialized=self.capture(['/usr/bin/git','init','--quiet',str(ambient)],self.root,env)
        self.assertEqual(initialized.returncode,0,initialized.stderr.decode())
        outside=self.file(ambient/'outside.txt',b'ambient file untouched\n')
        git_before=self.inventory(ambient/'.git');outside_before=outside.read_bytes()
        patch_bytes=(b'diff --git a/changed.cpp b/changed.cpp\n--- a/changed.cpp\n+++ b/changed.cpp\n'
                     b'@@ -1 +1 @@\n-before\n+after\n'
                     b'diff --git a/added.cpp b/added.cpp\nnew file mode 100644\n--- /dev/null\n+++ b/added.cpp\n'
                     b'@@ -0,0 +1 @@\n+added\n')
        patch_file=self.file(self.root/'patches/01.patch',patch_bytes)
        unisolated=ambient/'.build/task5/unisolated/source';unisolated.mkdir(parents=True)
        self.file(unisolated/'changed.cpp',b'before\n')
        for action in ('check','apply'):
            argv=['/usr/bin/git','apply',*(['--check'] if action=='check' else []),str(patch_file)]
            actual=self.capture(argv,unisolated,env)
            self.assertEqual(actual.returncode,0,actual.stderr.decode())
        self.assertEqual((unisolated/'changed.cpp').read_bytes(),b'before\n')
        self.assertFalse((unisolated/'added.cpp').exists())
        baseline=self.root/'baseline';self.file(baseline/'source/changed.cpp',b'before\n')
        rows=[{'path':'added.cpp','sha256':H(b'added\n'),'size_bytes':6,'mode':0o644},
              {'path':'changed.cpp','sha256':H(b'after\n'),'size_bytes':6,'mode':0o644}]
        graph_root=self.root/'tiny-fixture-graph'
        selected=self.file(graph_root/'git/01.patch',patch_bytes)
        graph={'layers':[{'order':1,'git_derivative':{'path':'git/01.patch','sha256':H(patch_bytes),'size_bytes':len(patch_bytes)}}],
               'final_changed_source_rows':rows,'new_files':['added.cpp']}
        self.file(graph_root/'derivatives.json',source.encoded(graph))
        proposal={'schema_version':1,'record_kind':'fex_memory_source_proposal','scope':'source_only',
             'baseline_manifest_sha256':evidence.BASE_SOURCE_SHA,'derivatives_manifest_sha256':evidence.GRAPH_SHA,
             'files':rows,'materialization_performed':False,'compilation_performed':False}
        self.file(graph_root/'final-source-proposal.json',source.encoded(proposal))
        output=ambient/'.build/task5/isolated'
        original_run=subprocess.run;captured=[]
        def actual_run(argv,**kwargs):
            self.assertEqual(kwargs['env'],source.git_environment(output))
            self.assertEqual(kwargs['cwd'],output/'source')
            captured.append(dict(kwargs['env']))
            result=original_run(argv,**kwargs)
            COMMAND_OBSERVATIONS.append({'argv':list(argv),'cwd':str(kwargs['cwd']),'environment':dict(kwargs['env']),
                'exit_code':result.returncode,'stdout_sha256':H(result.stdout),'stdout_bytes':len(result.stdout),
                'stderr_sha256':H(result.stderr),'stderr_bytes':len(result.stderr),
                'raw_stdout':result.stdout.decode('utf-8'),'raw_stderr':result.stderr.decode('utf-8')})
            return result
        # Only the two-file source-selection proof is an injected finite double.
        # Production source copy, environment, Git subprocesses and final-byte
        # comparison all execute unchanged against the real nested repository.
        with patch.object(evidence,'selected_projection',return_value={'source_files':rows}), \
             patch.object(source.subprocess,'run',side_effect=actual_run):
            result=source.project(baseline,graph_root,output)
        self.assertTrue(result['passed']);self.assertEqual(len(captured),2)
        self.assertTrue(all(v['GIT_CEILING_DIRECTORIES']==str(output) for v in captured))
        self.assertEqual((output/'source/changed.cpp').read_bytes(),b'after\n')
        self.assertEqual((output/'source/added.cpp').read_bytes(),b'added\n')
        self.assertEqual((baseline/'source/changed.cpp').read_bytes(),b'before\n')
        self.assertEqual(outside.read_bytes(),outside_before)
        self.assertEqual(self.inventory(ambient/'.git'),git_before)
        self.assertFalse((output/'source/.git').exists());self.assertFalse((output/'.git').exists())
        FIXTURE_OBSERVATIONS.append({'scope':'genuine_nested_git_source_environment_only',
            'old_git_checks_exit_zero_but_skip':True,'new_production_git_applies_exact_change_and_addition':True,
            'ambient_git_bytes_and_modes_unchanged':True,'baseline_source_unchanged':True,
            'source_selection_fixture_injected':True,'full_thirteen_layer_source_qualified':False,
            'compiler_execution':False,'fex_initialization':False})

if __name__=='__main__':unittest.main()
