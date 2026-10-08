#!/usr/bin/env python3
"""Reuse the native service fixture with the current 12-setting policy profile."""
from pathlib import Path
import argparse,fcntl,json,sys,subprocess
if not __package__:
 here=Path(__file__).resolve().parent
 sys.path[:]=[p for p in sys.path if Path(p or '.').resolve()!=here]
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO as R,need
from tools.fex import services,byte_readers
from tools.fex.common import sha256
from tools.fex.reconstruct import save
parser=argparse.ArgumentParser(description='Run existing Darwin service regressions against a reconstructed FEX build.')
parser.add_argument('--build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();root=args.output.absolute();base=args.build.resolve(strict=True)
need(root.parent==R/'.build/task5' and not root.exists(),'reconstruction_service_output')
need(json.loads((base/'build.json').read_text())['passed'] is True,'reconstruction_service_build')
with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);root.mkdir();rows=[];observations={}
 value=dict(scope='finite_native_darwin_services',passed=False,commands=rows,observations=observations,fex_build_sha256=sha256(base/'build.json'),guest_execution=False,restricted_operations=False)
 try:
  prior=json.loads((base/'logs/native.fixture/command.json').read_text());args=prior['argv'];exe=root/'pear-fex-services';args[args.index('-o')+1]=str(exe)
  p=subprocess.run(args,cwd=root,env=prior['environment'],capture_output=True,timeout=120);(root/'compile.stdout').write_bytes(p.stdout);(root/'compile.stderr').write_bytes(p.stderr);value['compile']=dict(argv=args,exit_code=p.returncode,source_sha256=sha256(R/'tests/fex/services/native_services.cpp'));assert p.returncode==0
  assert byte_readers.inspect_macho(exe)['architectures']==[byte_readers.MACH_ARM64];value['fixture_sha256']=sha256(exe)
  for role,lib in [('arm64ec','libarm64ecfex.so'),('wow64','libwow64fex.so')]:
   library=base/'install'/lib;assert byte_readers.inspect_macho(library)['architectures']==[byte_readers.MACH_ARM64]
   owned=root/role;owned.mkdir();result=services.run_command(root,role,['/usr/bin/arch','-arm64',str(exe),str(library),str(owned)],rows)
   observations[role]=services.observation(result['stdout'],128,policy_controls=26);assert not any(owned.iterdir());print(role+': eight services, 26 policy controls and owned worker cleanup passed',flush=True)
  value['passed']=True
 finally:
  save(root/'control.json',value);(root/'producer.py').write_bytes(Path(__file__).read_bytes())
