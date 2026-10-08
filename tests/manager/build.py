#!/usr/bin/env python3
"""Build/test Task #9 native foundation from verified offline inputs; no runtime launch."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import re
import uuid
from support import REPO, experiment_build as original, experiment_cases


def verify_inputs():
    original.verify_lock()
    for name in ('Cargo.toml', 'Cargo.lock'):
        if (REPO / 'manager' / name).read_bytes() != (original.EXPERIMENT / 'rust' / name).read_bytes():
            raise ValueError('manager dependency/profile closure differs from reviewed #3 input')
    config = REPO / 'manager/.cargo'
    if any((config / name).exists() or (config / name).is_symlink() for name in ('config', 'config.toml')):
        raise ValueError('unreviewed manager Cargo configuration')
    if (REPO / 'manager/src/json.rs').read_bytes() != (original.EXPERIMENT / 'rust/src/json.rs').read_bytes():
        raise ValueError('Stage 1 requires the unchanged #3 parser')


def checked_output(output):
    # Only a Task #9 leaf can receive build products; preserve sibling tasks.
    if '..' in output.parts: raise ValueError('parent traversal in output')
    absolute = output if output.is_absolute() else REPO / output
    relative = absolute.relative_to(REPO)
    if len(relative.parts) != 3 or relative.parts[:2] != ('.build', 'task9') or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,63}', relative.name):
        raise ValueError('output must be one Task #9 leaf')
    current = REPO
    for part in relative.parts:
        current /= part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise ValueError('unsafe output component')
    return absolute


def build(output, require_empty=False, rust_tests=False):
    output = checked_output(output)
    if require_empty and output.exists() and any(output.iterdir()):
        raise ValueError('fresh output required')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'bin').mkdir(exist_ok=True)
    env = original.controlled_environment()
    commands = []
    attempt = uuid.uuid4().hex
    log_path = output / ('build-log-' + attempt + '.json')
    def run(args, extra=None):
        process = subprocess.Popen([str(arg) for arg in args], cwd=REPO, env={**env, **(extra or {})},
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        stdout, stderr, failure = experiment_cases.capture_bounded(process, 180)
        commands.append({'argv':[str(arg) for arg in args], 'returncode':process.returncode,
                         'stdout':stdout.decode('utf-8', 'replace'), 'stderr':stderr.decode('utf-8', 'replace'),
                         'capture_failure':failure})
        log_path.write_text(json.dumps(commands, indent=2) + '\n')
        if failure or process.returncode: raise RuntimeError('build command failed; see owned build-log.json')
        return stdout.decode('utf-8').strip()
    verify_inputs()
    versions = {name:run(args) for name,args in {
        'clang':['xcrun','clang','--version'], 'sdk':['xcrun','--show-sdk-version'],
        'rustc':['rustc','--version','--verbose'], 'cargo':['cargo','--version'],
        'xcode':['xcodebuild','-version'], 'macos':['sw_vers'], 'machine':['uname','-m'],
    }.items()}
    if versions['machine'] != 'arm64': raise ValueError('native ARM64 host required')
    bridge = output / 'bridge.o'
    flags = ['-arch','arm64','-mmacosx-version-min=26.0','-O2','-std=c11','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations']
    run(['xcrun','clang',*flags,'-c',REPO / 'manager/native/bridge.c','-o',bridge])
    child=output/'bin/fixture-child'
    run(['xcrun','clang',*flags,original.EXPERIMENT/'fixtures/child.c',original.EXPERIMENT/'fixtures/native_bridge.c','-lproc','-o',child])
    child_object=output/'original-child.o'
    run(['xcrun','clang',*flags,'-Dmain=pear_original_main','-c',original.EXPERIMENT/'fixtures/child.c','-o',child_object])
    wrapper=output/'bin/fixture-entry'
    run(['xcrun','clang',*flags,'-I',original.EXPERIMENT/'fixtures',REPO/'tests/manager/fixtures/supervision_entry.c',child_object,bridge,'-lproc','-o',wrapper])
    rust_env = {'CARGO_TARGET_DIR':str(output / 'rust'), 'RUSTC':str(Path.home() / '.cargo/bin/rustc'),
                'PEAR_MANAGER_TEST_FIXTURE':str(child), 'CARGO_ENCODED_RUSTFLAGS':'\x1f'.join(['-C','link-arg='+str(bridge),'-C','link-arg=-lproc'])}
    common = ['--manifest-path',REPO / 'manager/Cargo.toml','--locked','--offline','--release','--target','aarch64-apple-darwin']
    run(['cargo','build',*common,'--bins','--examples'],rust_env)
    run(['cargo','test',*common,*([] if rust_tests else ['--lib'])],rust_env)
    binary = output / 'bin/foundation'
    shutil.copy2(output / 'rust/aarch64-apple-darwin/release/examples/foundation', binary)
    slices = run(['lipo','-archs',binary])
    if slices != 'arm64': raise ValueError('unexpected executable slice')
    # Inspection is separate from authorization; no signing/provisioning operation occurs.
    run(['codesign','--verify',binary])
    signature = subprocess.run(['codesign','-d','--verbose=2',binary],capture_output=True,text=True,timeout=10)
    if signature.returncode: raise RuntimeError('signature inspection failed')
    extra_binaries = {}
    for name in ('fixture-child','fixture-entry'):
        binary_path=output/'bin'/name
        extra_binaries[name]={'sha256':original.digest(binary_path),'slices':run(['lipo','-archs',binary_path]),'dependencies':run(['otool','-L',binary_path])}
    for name, source in [('pear-manager','pear-manager'), ('activation_probe','examples/activation_probe')]:
        destination=output/'bin'/name
        shutil.copy2(output/'rust/aarch64-apple-darwin/release'/source,destination)
        slices_extra=run(['lipo','-archs',destination])
        if slices_extra != 'arm64': raise ValueError('unexpected executable slice')
        run(['codesign','--verify',destination])
        extra_binaries[name]={'sha256':original.digest(destination),'slices':slices_extra}
    fixture=output/'fixtures';fixture.mkdir(exist_ok=True)
    for variant, alternate in [('approved',0),('alternate',1),('external',0)]:
        target=fixture/variant; (target/'lib').mkdir(parents=True,exist_ok=True)
        library=target/'lib/libfixture.dylib'
        run(['xcrun','clang',*flags,'-dynamiclib','-DFIXTURE_ALTERNATE='+str(alternate),REPO/'tests/manager/fixtures/library.c','-Wl,-install_name,@rpath/libfixture.dylib','-o',library])
        entry=target/'entry'
        run(['xcrun','clang',*flags,REPO/'tests/manager/fixtures/entry.c',library,'-Wl,-rpath,@executable_path/lib',*(['-Wl,-rpath,'+str(fixture/'alternate/lib')] if variant=='external' else []),'-o',entry])
        for path in (entry,library):
            if run(['lipo','-archs',path]) != 'arm64': raise ValueError('fixture not native')
            run(['codesign','--verify',path])
            extra_binaries[str(path.relative_to(output))]={'sha256':original.digest(path),'slices':'arm64','dependencies':run(['otool','-L',path]),'load_commands':run(['otool','-l',path])}
    inputs = [path for group in ('manager','tests/manager','tests/contracts','runtime/contracts')
              for path in (REPO / group).rglob('*') if path.is_file() and '__pycache__' not in path.parts]
    inputs += [original.EXPERIMENT / path for path in ('build.py','run_cases.py','fixtures/cases.json','fixtures/native_bridge.c','fixtures/native_bridge.h','fixtures/child.c','rust/src/main.rs','rust/src/supervisor_tests.rs','rust/src/json.rs','rust/Cargo.toml','rust/Cargo.lock')]
    metadata = {'version':1,'stage':3,'fixture_only':True,'runtime_eligible':False,'toolchains':versions,
                'sources':{str(path.relative_to(REPO)):original.digest(path) for path in sorted(set(inputs))},
                'binaries':{'foundation':{'sha256':original.digest(binary),'slices':slices,'size_bytes':binary.stat().st_size,
                    'file':run(['file',binary]),'dependencies':run(['otool','-L',binary]),'signature_inspection':signature.stderr}},
                'c_flags':flags,'rust_environment':rust_env,'locked_offline_rust':True,'build_log':log_path.name}
    metadata['binaries'].update(extra_binaries)
    encoded = json.dumps(metadata,indent=2)+'\n'
    (output / ('build-' + attempt + '.json')).write_text(encoded)
    (output / 'build.json').write_text(encoded)
    return metadata


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--locked',action='store_true',required=True)
    parser.add_argument('--require-empty',action='store_true')
    parser.add_argument('--rust-tests',action='store_true')
    args=parser.parse_args()
    try:
        build(args.output,args.require_empty,args.rust_tests)
        print(json.dumps({'build':'passed','stage':3,'runtime_eligible':False}))
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
        print(json.dumps({'build':'failed','reason':'input_or_build_failure','runtime_eligible':False}))
        return 1
if __name__ == '__main__': sys.exit(main())
