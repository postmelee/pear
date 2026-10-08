#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Admit the unchanged #5 pair and clone/sign one #6 fixture bundle."""
from pathlib import Path
import argparse
import copy
import fcntl
import json
import plistlib
import shutil
import subprocess
import sys

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.corpus import REPO, digest
from tools.cpu.results import admit_build, read
from tools.wine.common import need, encoded
from tools.fex import reconstruction_check, memory_wine_runtime as signing

PRIOR_RUNTIME='daf965486f2c0b89c019c36638886efbfcaf590b25cd197839dc2fef60060506'
CHECKER='79dac00032746645cc040657618a1d05b581fa73b6c926d04fe15343a1097f2d'


def admit_pair(prior_repo):
    # Reuse the exact checker in an isolated namespace with an explicit receipt
    # repository. Do not weaken or mutate #5's own root/producer admission.
    raw=(prior_repo/'tools/fex/reconstruction_check.py').read_bytes()
    need(digest(raw)==CHECKER,'prior_checker_changed')
    namespace=dict(vars(reconstruction_check));namespace['REPO']=prior_repo
    signing.selected(raw,('command_gate','load','components'),namespace,'Task #5 component admission')
    wine=prior_repo/'.build/task5/stage6-wine3';fex=prior_repo/'.build/task5/stage6-fex1'
    receipts,_=namespace['components'](wine,wine,fex,fex)
    return receipts


def prepare(prior_repo, signing_source, build_root, output, correction=None):
    need(output.parent==REPO/'.build/task6' and not output.exists() and not output.is_symlink(),'fresh_cpu_runtime')
    need(shutil.disk_usage(REPO).free>=4*1024**3,'cpu_runtime_storage')
    manifest_path=REPO/'tests/cpu/corpus.json';manifest=read(manifest_path)
    build_raw=(build_root/'build.json').read_bytes();built=read(build_root/'build.json')
    if built.get('scope')=='cpu_ordering_build':
        from tools.cpu.ordering import admit_ordering_build
        admit_ordering_build(build_root)
    else:
        admit_build(manifest,manifest_path.read_bytes(),built,build_root)
    receipts=admit_pair(prior_repo)
    corrected=None
    if correction:
        from tools.cpu.fex_build import admit_correction
        corrected=admit_correction(correction,receipts)
    prior=prior_repo/'.build/task5/stage6-runtime-api2'
    raw=(prior/'runtime.json').read_bytes();need(digest(raw)==PRIOR_RUNTIME,'prior_runtime_changed')
    previous=json.loads(raw)
    need(all(previous['input_receipts'][k]==v for k,v in receipts.items()),'prior_runtime_pair')
    helpers,_=signing.signing_helpers(signing_source);reader=helpers.legacy(REPO)
    need(reader.inventory(prior/signing.BUNDLE)==previous['bundle_inventory'],'prior_bundle_changed')
    output.mkdir(mode=0o700)
    record=copy.deepcopy(previous);record.update(passed=False,kind='cpu_corpus_development_runtime',
        prior_runtime_sha256=PRIOR_RUNTIME,cpu_build_sha256=digest(build_raw),cpu_qualified=False,
        commands=[],copies=[],fixtures={},fixture_case='cpu-corpus')
    try:
        old_auth=json.loads((prior/'authorization.json').read_text())
        authorization,private,profile=helpers.capture_authorization(old_auth['original_ref']['path'],output,reader,[])
        need(authorization['capture']['sha256']==old_auth['capture']['sha256'] and
             authorization['claims']==old_auth['claims'],'cpu_profile_changed')
        subprocess.run(['/bin/cp','-cRp',str(prior/signing.BUNDLE),str(output/signing.BUNDLE)],check=True,timeout=120)
        need(reader.inventory(output/signing.BUNDLE)==previous['bundle_inventory'],'cpu_clone_changed')
        if corrected:
            dll=output/signing.PAYLOAD/'lib/wine/aarch64-windows/xtajit64.dll'
            need(digest(dll.read_bytes())=='10069347abcbace30b3874d91da0ee1b0460613b1794d60c6e56fac2b8a19237','prior_fex_binary')
            shutil.copyfile(correction/'deployment.dll',dll)
            record['baseline_input_receipts']=copy.deepcopy(record['input_receipts'])
            record['input_receipts']['fex']=record['input_receipts']['linked']=corrected['build_sha256']
            record['cpu_correction']=corrected
        target=output/signing.PAYLOAD/'libexec/pear-cpu';target.mkdir()
        for row in built['cases']:
            raw=(build_root/row['path']).read_bytes();need(digest(raw)==row['sha256'],'cpu_fixture_changed')
            path=target/row['path'];path.write_bytes(raw);path.chmod(0o755)
            record['fixtures'][row['id']]=dict(path=path.relative_to(output).as_posix(),sha256=row['sha256'])
        (output/'authorized-entitlements.plist').write_bytes(plistlib.dumps(authorization['claims']))
        (output/'authorized-entitlements.plist').chmod(0o600)
        images=copy.deepcopy(previous['native_images'])
        recipe=helpers.signing_recipe(output,images,private['identity'])
        for ident,argv in recipe:helpers.native(argv,output,ident,record['commands'])
        for image in images:
            path=output/image['path']
            reader.verify_code_origin(prior/image['path'],path)
            image.update(sha256=digest(path.read_bytes()),size_bytes=path.stat().st_size)
        logs=helpers.verify_commands(output,record['commands'],recipe)
        record.update(native_images=helpers.signatures_from_logs(output,images,logs,authorization['claims'],private,reader,profile),
                      bundle_inventory=reader.inventory(output/signing.BUNDLE),
                      authorization_sha256=digest((output/'authorization.json').read_bytes()),passed=True)
        print(json.dumps(dict(prepared=True,fixtures=len(record['fixtures']),guest_execution=False)))
    finally:
        (output/'runtime.json').write_bytes(encoded(record))
        (output/'producer.py').write_bytes(Path(__file__).read_bytes())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('prior-repo','signing-source','build','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument("--fex-correction",type=Path)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prepare(a.prior_repo.resolve(),a.signing_source.resolve(),a.build.resolve(),a.output.absolute(),a.fex_correction.resolve() if a.fex_correction else None)
