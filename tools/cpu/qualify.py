#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Re-admit complete CPU evidence and bind fixture bundles to one component set."""
from pathlib import Path
import argparse
import sys
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.results import read,require,digest,canonical
from tools.cpu.corpus import REPO
from tools.cpu.compare import compare as compare_isa
from tools.cpu.ordering import compare as compare_ordering
from tools.fex import memory_wine_runtime as signing

CONFIGURATION=('baseline_build_sha256','baseline_input_receipts','baseline_loader_capacity',
    'cpu_correction','dependency_closure','entrypoints','input_receipts','memory_profile',
    'prior_runtime_sha256','source_ledger','test_instrumentation')

def same_configuration(left,right):
    require(left.get('passed') is True and right.get('passed') is True and
            left.get('kind')==right.get('kind')=='cpu_corpus_development_runtime','candidate_kind')
    for key in CONFIGURATION:
        require(key in left and key in right and left[key]==right[key],'candidate_configuration_'+key)
    require(left['cpu_correction']['scope']=='arm64ec_fex_only','candidate_component_scope')

def normalized_inventory(value):
    # Called only after current inventory admission and actual Mach-O code-origin
    # comparison. Only declared PE fixtures and their signature fields can vary.
    fixtures={Path(f['path']).relative_to(signing.BUNDLE).as_posix() for f in value['fixtures'].values()}
    require(all(p.startswith('Contents/Resources/runtime/libexec/pear-cpu/') for p in fixtures),'fixture_path_scope')
    natives={Path(p['path']).relative_to(signing.BUNDLE).as_posix() for p in value['native_images']}
    result={}
    for original in value['bundle_inventory']:
        row=dict(original);path=row['path']
        require(path not in result,'duplicate_inventory_path')
        if path in fixtures:continue
        if path in natives or path=='Contents/_CodeSignature/CodeResources':
            require(row['kind']=='file','signature_file_kind')
            row.pop('sha256');row.pop('size_bytes')
        result[path]=row
    return result

def bind_candidates(isa_root,ordering_root,reuse):
    left=read(isa_root/'runtime.json');right=read(ordering_root/'runtime.json')
    same_configuration(left,right)
    helpers,_=signing.signing_helpers(reuse);reader=helpers.legacy(REPO)
    for root,value in ((isa_root,left),(ordering_root,right)):
        require(reader.inventory(root/signing.BUNDLE)==value['bundle_inventory'],'candidate_inventory_changed')
        require(digest((root/'authorization.json').read_bytes())==value['authorization_sha256'],'candidate_authorization_changed')
    auth_left=read(isa_root/'authorization.json');auth_right=read(ordering_root/'authorization.json')
    require(auth_left['capture']['sha256']==auth_right['capture']['sha256'] and
            auth_left['claims']==auth_right['claims'] and auth_left['identity']==auth_right['identity'],'candidate_authorization_mismatch')
    images={p['path'] for p in left['native_images']}
    require(images=={p['path'] for p in right['native_images']},'candidate_native_image_set')
    for path in sorted(images):reader.verify_code_origin(isa_root/path,ordering_root/path)
    require(normalized_inventory(left)==normalized_inventory(right),'candidate_payload_mismatch')
    dll='Contents/Resources/runtime/lib/wine/aarch64-windows/xtajit64.dll'
    actual=digest((isa_root/signing.BUNDLE/dll).read_bytes())
    require(actual==left['cpu_correction']['dll_sha256'] and
            actual==digest((ordering_root/signing.BUNDLE/dll).read_bytes()),'candidate_fex_mismatch')
    return dict(fex_dll_sha256=actual,fex_build_sha256=left['cpu_correction']['build_sha256'],
                input_receipts=left['input_receipts'],native_code_origins=len(images),
                same_runtime_configuration=True,same_authorization=True,
                fixture_bundle_sha256=[digest((root/'runtime.json').read_bytes()) for root in (isa_root,ordering_root)])

def qualify(build,reference,candidate,ordering_reference,ordering_candidate,output):
    require(not output.exists(),'output_exists');output.mkdir(parents=True)
    result=dict(scope='declared_x64_cpu_qualification',passed=False,game_qualified=False)
    try:
        compare_isa(REPO/'tests/cpu/corpus.json',build,reference,candidate,output/'isa')
        compare_ordering(ordering_reference,ordering_candidate,output/'ordering')
        isa_index=read(candidate);ordering_index=read(ordering_candidate)
        require(isa_index['signing_source']==ordering_index['signing_source'],'candidate_signing_source')
        identity=bind_candidates(Path(isa_index['runtime']),Path(ordering_index['runtime']),Path(isa_index['signing_source']))
        isa=read(output/'isa/comparison.json');ordering=read(output/'ordering/comparison.json')
        require(len(isa['cases'])==19 and len({c['id'] for c in isa['cases']})==19,'qualification_case_count')
        unsupported=[c['id'] for c in isa['cases'] if c['status']=='unsupported_not_exposed']
        require(all(c['status'] in ('passed','unsupported_not_exposed') for c in isa['cases']) and
                unsupported==['avx-lane-preservation'],'qualification_declared_coverage')
        observed=ordering['candidate']
        require(observed['rounds']==4 and observed['iterations_per_mode']==2048 and
                observed['measured_pairs']==32768 and observed['checked_worker_retirements']==8,'qualification_ordering_budget')
        result.update(passed=True,component_identity=identity,passed_cases=18,unsupported_cases=unsupported,
            ordering_pairs_per_host=32768,worker_lifetimes=8,checked_worker_retirements=8,
            corpus_sha256=digest((REPO/'tests/cpu/corpus.json').read_bytes()),
            isa_comparison_sha256=digest((output/'isa/comparison.json').read_bytes()),
            ordering_comparison_sha256=digest((output/'ordering/comparison.json').read_bytes()),
            unsupported=['AVX exposure','i386/WoW64 execution'],
            unperformed=['complete late-loaded image coverage','Steam','D3D11 integration','Megabonk gameplay','independent Mac reproduction','ordinary-user distribution'])
    except Exception as exc:
        result['error']=dict(type=type(exc).__name__,code=str(exc) if isinstance(exc,ValueError) else 'qualification_error')
        raise
    finally:(output/'qualification.json').write_bytes(canonical(result))
    print(canonical(result).decode())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('build','reference','candidate','ordering-reference','ordering-candidate','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();qualify(a.build.resolve(),a.reference.resolve(),a.candidate.resolve(),a.ordering_reference.resolve(),a.ordering_candidate.resolve(),a.output.absolute())
