# Source qualification

Pear's September 28, 2026 source audit is **complete with a `blocked` decision**. The selected public source identities reproduce, but the assembled Wine/FEX/DXMT candidate is not source-ready for a reproducible runtime build. Required Darwin integration is still `needs-port`; missing or conflicting build inputs and the final dependency/notice closure remain explicit blockers. This is not a claim that the design is impossible.

The [inventory](../runtime/sources/manifest.json) is the factual source of truth. [Stage 4 evidence](../mydocs/working/task_m1_1_stage4_evidence.json) records repeat acquisition; [Stage 2 evidence](../mydocs/working/task_m1_1_stage2_evidence.json) records the inspected source ranges, terms and patch observations; [Stage 3 evidence](../mydocs/working/task_m1_1_stage3_evidence.json) records installed-tool metadata and validator scope. Runtime, game and distribution qualification remain unassessed. Issue closure does not change this decision.

## Scoped Wine component update — October 1, 2026

[Issue #4](https://github.com/postmelee/pear/issues/4) now has [independently verified fresh Wine-component reconstruction](../mydocs/working/task_m1_4_stage6_observations.json): two ARM64 native builds, a compile-only ARM64EC companion, strict unsigned comparison, actual development signing, and finite native bootstrap/API/ABI/thread/Win32-Cocoa fixtures. The [development guide](development/wine-host.md) documents the exact tested configuration and permissions; the [Stage 6 report](../mydocs/working/task_m1_4_stage6.md) records failures, limits and integration handoff.

This dated component result preserves the September 28 audit and its blocked aggregate decision. Darwin FEX host services, translated execution, Wine/DXMT pairing, final dependency/notice closure, Steam/game qualification and general-user distribution still require their own evidence. Same-host fresh directories and a reverified compiler cache do not establish clean-machine or independent-compiler reproduction.

## Scoped Wine/FEX component update — October 8, 2026

[Task #5 Stage 6](../mydocs/working/task_m1_5_stage6.md) freshly rebuilt the selected Wine/FEX pair and passed five original x64 lifecycle/API fixtures from empty synthetic prefixes on this development Mac. Current authorization, ARM64 observations and cleanup passed; native caller refusal and Darwin service controls also passed. See the [FEX development guide](development/fex-host.md) for exact scope and prepared-input requirements.

This is separate component evidence, preserving the original blocked audit and source inventory. It does not qualify broader CPU behavior, graphics/Steam/Megabonk, full module observation, independent reproduction or ordinary-user distribution.

## Selected input set

All pins below identify source. They do not identify a built or supported runtime.

| Component | Immutable Git commit | Role |
|---|---|---|
| Wine upstream | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` | Windows API, ARM64/ARM64EC loader and Darwin integration candidate |
| FEX | `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` | Windows translator modules and host-service boundary candidate |
| DXMT | `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` | D3D11, ARM64EC PE and native Metal/shader source |
| Wine DXMT interface | `87ba10bb3aa8ea636dff5c2030b376da1627910a` | Source corresponding to a publisher's link-only release label; not a working runtime |
| LLVM shader library | `8dfdcc7b7bf66834a761bd8de445840ef68e4d1a` | LLVM 15.0.7 native shader-library source |
| LLVM-MinGW build source | `030097eeee87fcfd0f3bfe536b21cbd6e5d3b324` | 20260908 source defaults; not proven release-binary provenance |
| LLVM cross compiler | `6dfe1677ab8dffbc6ec13d53a1e0215d75147689` | LLVM 23.1.1 default selected by those build scripts |
| MinGW-w64 | `9f55f4a2d3b9783dab76d9808be3d6279b99ec2a` | Windows headers and runtime source selected by those scripts |

The full set contains 30 component records: 22 acquired Git repositories, one acquired archive and seven explicitly excluded, conditional gitlink inputs. Every declared gitlink is accounted for, including optional and nested inputs. The manifest records each exclusion's configuration condition; these exclusions must be revisited when a build configuration is chosen. This audit does not establish the final transitive build or shipped-payload closure.

The official CrossOver 26.3.0 FOSS archive has exact downloaded-byte SHA-256 `ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872` (149,054,023 bytes). Its inspected Wine subtree and bounded text scans do not establish complete ARM64 Preview source, an exact upstream base, or an ordered port patch series. No commercial preview binary is an accepted substitute.

Git commit/tree IDs use Git SHA-1. A `git_tree_listing_bytes` SHA-256 hashes the exact NUL-separated `git ls-tree` representation of mode/path/object identities, not concatenated file contents. `downloaded_archive_bytes`, `archive_member_metadata_json_bytes`, `archive_member_bytes` and `patch_file_bytes` are separate scopes. Both acquisitions used the same host and public HTTPS origins; matching identities are not independent publisher authentication. No commit/tag signature or independently published archive checksum was verified.

## Reproduce the source inputs

Run these commands from a Pear checkout. They use installed Python 3 and Git, download only the manifest's selected public inputs, and keep data in an ignored cache. They never check out source, invoke configure/build/install scripts, or recursively initialize submodules. Required submodule pins are acquired as separate bare repositories by the same loop. Do not mutate the cache while validation is running.

The example uses a new `.build/task1-sources/contributor-reproduction/inputs` directory and refuses to reuse an existing one. Keep previous acquisitions for comparison. The audit's actual second acquisition used `.build/task1-sources/reproduction/inputs` with this same relative layout. Exact expanded commands and observed identities are preserved in Stage 4 evidence.

```sh
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

manifest = json.loads(Path('runtime/sources/manifest.json').read_text())
cache = Path('.build/task1-sources/contributor-reproduction/inputs')
cache.mkdir(parents=True, exist_ok=False)
env = {key: value for key, value in os.environ.items()
       if not key.startswith('GIT_')}
env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null',
           GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0',
           GIT_LFS_SKIP_SMUDGE='1', LC_ALL='C')
git = ['git', '-c', 'core.hooksPath=/dev/null',
       '-c', 'protocol.ext.allow=never', '-c', 'protocol.file.allow=never',
       '-c', 'submodule.recurse=false', '-c', 'credential.helper=',
       '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']
curl = ['curl', '--silent', '--show-error', '--fail', '--location',
        '--proto', '=https', '--proto-redir', '=https',
        '--connect-timeout', '20', '--max-time', '600']

def run(args):
    return subprocess.run(args, env=env, check=True,
                          stdout=subprocess.PIPE, timeout=900).stdout

def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(data)
    return result.hexdigest()

for component in manifest['components']:
    if component['acquisition']['status'] != 'acquired':
        continue
    source = component['source']
    target = cache / component['acquisition']['cache_path']
    target.parent.mkdir(parents=True, exist_ok=True)
    if source['kind'] == 'git':
        commit = source['commit_object_id']
        depth = '2' if component['component_id'] == 'wine-macdrv-export-patch' else '1'
        run(git + ['init', '--bare', str(target)])
        base = git + ['-C', str(target)]
        run(base + ['fetch', '--no-tags', '--depth=' + depth,
                    '--no-recurse-submodules', source['url'], commit])
        run(base + ['update-ref', 'refs/heads/source', commit])
        run(base + ['symbolic-ref', 'HEAD', 'refs/heads/source'])
        assert run(base + ['rev-parse', '--verify', commit + '^{commit}']).decode().strip() == commit
        assert run(base + ['rev-parse', '--verify', commit + '^{tree}']).decode().strip() == source['tree_object_id']
        assert run(base + ['rev-parse', '--show-object-format']).decode().strip() == source['object_format']
        run(base + ['fsck', '--full', '--no-reflogs'])
        listing = run(base + ['ls-tree', '-r', '-z', '--full-tree', commit])
        pin = component['content_digests'][0]
        (cache / pin['cache_path']).write_bytes(listing)
    else:
        run(curl + ['--output', str(target), source['url']])
        archive_pin = component['content_digests'][0]
        assert sha256(target) == archive_pin['value']
        members = []
        # Stream metadata only; do not extract archive paths or links.
        with tarfile.open(target, mode='r|gz') as archive:
            for member in archive:
                members.append({'name': member.name, 'size': member.size,
                                'kind': member.type.decode('ascii', errors='replace'),
                                'link': member.linkname or None})
        listing_pin = component['content_digests'][1]
        (cache / listing_pin['cache_path']).write_text(json.dumps(members, indent=2) + '\n')
    for pin in component['content_digests']:
        assert sha256(cache / pin['cache_path']) == pin['value']
    print(component['component_id'], 'matched')

for patch in manifest['patch_inventory']:
    target = cache / patch['cache_path']
    run(curl + ['--output', str(target), patch['source_url']])
    assert sha256(target) == patch['digest']['value']
    assert target.stat().st_size == patch['size_bytes']
    print(patch['patch_id'], 'matched')
PY
```

The manifest and scripts are repository-controlled instructions that contributors should review. A failed download, object check or hash assertion is a reproduction failure. Preserve it, report it and review the changed representation or source availability; do not update a pin simply to make the check pass.

### Repeat the existing patch experiment

The sole existing patch is `6197fc78f72184b5f8eed5df306f5e4a48c1153f`, SHA-256 `8a8799de8abee169fe9c22f982871a904d38e163c641633599f051c3023fb0fb`, 3,358 bytes. Its original parent is `a365b39f9769ccffeaaf20a45151b671fe763dc3`. It applies there and produces tree `ffb8dd5bf8171ec59c40ee3f5d66f17408206890`. It fails with exit 1 on both selected Wine candidates. This is a reproduced incompatibility, not a runtime patch series.

The following uses fresh indexes only. It applies the patch solely to its historical parent and leaves the selected runtime candidates unchanged. It writes Git objects to the disposable reproduction cache when producing the historical result tree; it does not check out or build source.

```sh
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess

manifest = json.loads(Path('runtime/sources/manifest.json').read_text())
cache = Path('.build/task1-sources/contributor-reproduction/inputs').resolve()
indexes = cache.parent / 'patch-indexes'
indexes.mkdir(exist_ok=False)
components = {item['component_id']: item for item in manifest['components']}
patch = manifest['patch_inventory'][0]
patch_file = cache / patch['cache_path']
env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null',
           GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0', LC_ALL='C')
for expectation in patch['applicability']:
    target = expectation['target']
    component_id = patch['component_id'] if target == 'original-parent' else target
    repo = cache / components[component_id]['acquisition']['cache_path']
    env['GIT_INDEX_FILE'] = str(indexes / (target + '.index'))
    git = ['git', '-c', 'core.hooksPath=/dev/null', '-c', 'protocol.allow=never',
           '-c', 'submodule.recurse=false', '-C', str(repo)]
    def run(args, check=True):
        return subprocess.run(git + args, env=env, check=check,
                              capture_output=True, timeout=120)
    run(['read-tree', expectation['base_commit']])
    check = run(['apply', '--cached', '--check', str(patch_file)], check=False)
    assert check.returncode == expectation['check_exit_code']
    if check.returncode == 0:
        assert target == 'original-parent'
        run(['apply', '--cached', str(patch_file)])
        tree = run(['write-tree']).stdout.decode().strip()
        assert tree == expectation['result_tree']
    print(target, check.returncode, expectation['status'])
PY
```

## Validate and interpret the result

```sh
python3 -m unittest discover -s tests/sources -p 'test_*.py' -v
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/contributor-reproduction/inputs --require-complete
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/contributor-reproduction/inputs --require-source-ready
```

| Check | Expected result for this audit |
|---|---|
| Unit tests | All owned source/negative fixtures pass |
| Complete-audit gate | Exit 0; `record_valid: true`, `audit_complete: true`, `decision: blocked`, `source_ready: false` |
| Source-ready gate | **Exit 3**, `requested_gate_not_met`; this is an intentional refusal and does not pass source readiness |
| Any invalid/mismatched input | Exit 1 with bounded errors; stop and inspect |
| CLI misuse | Exit 2 |

The standard-library validator performs bounded local Git/content/reference checks. It makes no network requests and does not execute commands recorded in evidence. It requires the evidence documents in this checkout and exact cache-relative input paths. It checks acquired Git objects, source blobs, archive members, scoped hashes, gitlinks, patch provenance and decision consistency. Historical patch applicability is checked against recorded facts; the separate experiment above actually replays it. Directory reads by Git are not an atomic snapshot of a cache controlled by another writer.

`record_valid` describes consistency and the inspected bytes. `audit_complete` means every declared requirement is accounted for, including failures and blockers. `source_ready` is true only for a complete `go` decision with all required source prerequisites satisfied. None of these fields can qualify a runtime, game or distribution.

## Gaps and downstream obligations

| Area | Reusable evidence | Unmet work and verification owner |
|---|---|---|
| Wine loader and pages | ARM64 loader, reservations and 4 KiB bookkeeping exist | [#4](https://github.com/postmelee/pear/issues/4): reconcile Wine's inspected 4 KiB PAGEZERO with the separate #2 probe's 64 KiB layout; prove process geometry and actual child mappings |
| x18 and host calls | ARM64 entry assembly and Apple signal context code exist | [#4](https://github.com/postmelee/pear/issues/4), [#5](https://github.com/postmelee/pear/issues/5): explicit guest/host transitions, nested callbacks and asynchronous entry under the authorized host mode |
| Translator loading | Wine ARM64EC/WoW64 interfaces and FEX Windows modules exist | #4/#5: match exports/module identities and prove the actual translator selected for required x64/x86 processes |
| FEX host services | Small Windows UnixLib boundary is reusable | #5: replace or correctly disable Linux `prctl`, `.so`/`rt` dependencies; implement Darwin mapping, per-thread memory ordering, JIT cache and lifecycle behavior |
| Signals, SEH and JIT | Existing reconstruction, protection and fault code | #4/#5: actual Windows exception/unwind, guard, suspend/resume, write/execute transitions and precise translated-state tests |
| DXMT driver ABI | Function-table and individual-symbol loading paths exist | [#7](https://github.com/postmelee/pear/issues/7), #4: reconcile `cocoa_view`/`client_cocoa_view` versus `client_view`/`rects`; exporting names alone is insufficient |
| Native shader/Metal pairing | ARM64EC build and native LLVM/Metal rules exist | #7: compatible native/PE outputs, callbacks, shader/readback/synchronization/presentation tests |
| Build tools and SDK | Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0 and ld 1267 observed | #4/#5/#7: select and verify missing CMake/Meson/Ninja/cross compiler/native LLVM library; install authorized Metal Toolchain; replace conflicting Bison 2.3 (Wine requires at least 3.0); reconcile upstream Xcode 16.1 assumptions |
| Dependency and notice closure | Required/conditional gitlinks and selected bundled notices are inventoried | #4/#5/#7 and [#13](https://github.com/postmelee/pear/issues/13): choose actual enabled native libraries and shipped files, then reconcile corresponding source, licenses and notices |
| Vendor Preview comparison | Public 26.3.0 archive was acquired and bounded Wine contents inspected | No complete Preview implementation/patch provenance established. It cannot fill any missing port gate or authorize reliance on opaque binaries |

The measured [host capability evidence](host-capabilities.md) remains useful but finite. It cannot replace integration tests inside Wine/FEX/DXMT. The inventory names ten source requirement areas, including code that is present but behaviorally unverified. No new port patches were authored during this audit.

### Terms and contributions

The manifest's component-level terms and evidence ranges are authoritative for this dated inspection. Wine and the selected DXMT revision declare LGPL-2.1-or-later; DXMT's former MIT license applies only to the older releases described by `LICENSE.OLD`, through v0.80. FEX declares MIT. LLVM uses Apache-2.0 with LLVM exceptions plus legacy/third-party terms; LLVM-MinGW-owned scripts use ISC, which does not blanket-license all bundled compiler/runtime code. MinGW, DirectX headers, NVAPI and FEX dependencies carry their own inspected notices and configuration exceptions.

Preserve the applicable notices and review corresponding-source, modification and replacement/relinking obligations against actual shipped files. This is an engineering inventory, not legal clearance. The full vendor aggregate and future runtime payload were not cleared. The inspected FEX and DXMT contribution policies restrict AI-generated upstream submissions; this differs from downstream source reuse rights. Wine's current external contribution policy was not established by the bounded local scan. No upstream submission was made or authorized by this task.

## Reconsidering the decision

Preparatory work and port implementation in #4/#5/#7 may proceed under their own approved plans. Their affected acceptance gates and all positive build/runtime claims remain blocked.

The current combined candidate remains blocked until its owning tasks select a usable, attributed build input set and account for enabled dependencies and terms. Required Wine/FEX/DXMT ports must then be implemented, pinned and tested; update the manifest with their actual bases, ordered patch bytes, source-built output provenance and verification evidence. A new `go` decision requires a reviewed inventory change and a passing source-ready gate. Completing this investigation, installing one tool or choosing a manager language is insufficient.

The same restrictions continue downstream: retain upstream implementation languages unless a measured reviewed reason justifies replacement, preserve normal macOS security protections, and use a documented signing/provisioning route. Required host processes and modules still need native execution evidence. Steam, Megabonk, save data, credentials and proprietary payloads remain outside this source audit and its Git artifacts.
