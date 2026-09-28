# Task #1 Stage 3: Source provenance and toolchain validation

GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Implementation plan: [`task_m1_1_impl.md`](../plans/task_m1_1_impl.md)
Stage: 3
Date: September 28, 2026

## Stage Purpose

Turn the acquired-source evidence into a repeatable, bounded consistency check, and record actual available build-tool metadata. This stage verifies source bytes and accounting; it does not build components or issue the final source-readiness decision.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/sources/manifest.json` | Adds 17 candidate tool records and their evidence links while retaining incomplete audit/readiness states. |
| `tools/sources/validate_inventory.py` | Standard-library validator for manifest/evidence references, Git objects, source/archive/patch digests, dependency identities and honest decision gates. |
| `tests/sources/test_inventory.py` | 77 tests with owned source repositories and archives, including invalid identities, paths, types, bounds and false readiness. |
| `mydocs/working/task_m1_1_stage3_evidence.json` | Observed tool versions, exact verification commands/results, historical preservation hashes and validator limits. |
| `mydocs/plans/task_m1_1_impl.md`, `mydocs/orders/20260928.md` | Approval, completion and parallel-task status. |
| `mydocs/working/task_m1_1_stage3.md` | This bundled stage report. |

## Body Change Scope / Lossless Preservation

Stage 1 and Stage 2 evidence remains byte-identical to the previous commit. Existing source pins, historical patch observations and Issue #2 host evidence are preserved. Changes are confined to the approved audit, validator, test and workflow-record locations. No upstream code, product architecture, game data or credentials were added. Raw source inputs and logs remain ignored under `.build/task1-sources/`.

The manifest still reports `audit_complete: false`, `decision: unassessed`, and `source_ready: false`. Runtime, game and distribution qualification remain unassessed. A passing default validator result means that this incomplete audit is internally consistent with the inspected bytes.

## Verification Results

The planned commands were executed; expanded metadata and outcomes are retained in the [Stage 3 evidence](task_m1_1_stage3_evidence.json).

```sh
xcrun clang --version
xcrun --show-sdk-version
git --version
python3 --version
python3 -m unittest discover -s tests/sources -p 'test_*.py' -v
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/inputs
git diff --check
```

| Check | Actual result |
|---|---|
| Owned-fixture test suite | 77 passed; final recorded run 3.904 seconds. |
| Actual acquired-cache validation | Exit 0: 30 components, 22 acquired Git repositories, one archive, 24 scoped content digests, 206 unique source blobs, 16 archive members, 20 gitlinks, one patch, 272 evidence definitions and 359 bounded Git commands. |
| Explicit complete-audit gate | `--require-complete` returned expected exit 3, with `record_valid: true` and `requested_gate_not_met`. This is a refusal, not a passed completeness claim. |
| Explicit source-ready gate | `--require-source-ready` returned expected exit 3 with the same valid-but-unready distinction. |
| Type/boundary/privacy checks | Tests reject boolean/float count substitutions, duplicate keys, malformed objects, bad digests, escaped paths, symlinks, nonregular inputs, unsafe Git configuration/storage, missing evidence, Git time/output excess and contradictory readiness. |
| Historical preservation | Stage 1/2 evidence hashes match the preceding commit. Existing patch applicability records were cross-checked, not replayed in Stage 3. |
| JSON syntax and diff | Passed. |

The validator reads installed Git with prompts, hooks, lazy fetching, network protocols and inherited Git overrides disabled. It accepts only a narrow bare-repository configuration, rejects external object stores and bounds JSON, cache bytes, archive expansion, command output and execution. Error results contain fixed codes and optional validated component IDs, not raw command errors or private paths. Killing an owned Git group can be denied on this host; the bounded failure path falls back to terminating and reaping its owned direct child.

### Observed toolchain constraints

| Area | Observation and consequence |
|---|---|
| Host and Apple tools | Native Apple M4 Pro, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0 and ld 1267. These are observed tools, not a proven runtime build combination. |
| Other available metadata | Git 2.53.0 and Python 3.14.4, plus the other individually recorded tools. In total: ten metadata-observed entries. |
| Missing inputs | Six tools were not found on the inspected PATH, including CMake, Meson, Ninja, ARM64EC cross tools and the native LLVM shader-library discovery tool. No automatic installation occurred. |
| Metal | An ARM64 dispatcher exists, but its version invocation fails because the optional Metal Toolchain is absent. Recorded as unavailable. |
| Bison | Installed 2.3 conflicts with selected Wine's declared minimum 3.0. |
| Upstream pairing | Observed DXMT CI uses a different Xcode/tool combination. Compatibility with this host remains unverified and belongs to downstream builds. |

## Residual Risks

- Cache validation requires inputs not to be concurrently modified. Descriptor checks do not make Git's directory reads an atomic snapshot.
- Source hashes establish identity, not publisher trust or legal approval. Tool metadata does not cover every tool dependency or prove ABI/build compatibility.
- Existing patches still require the recorded adaptations; no port implementation or runtime integration occurred.
- The validator has finite per-command and total-count limits, but a complete audit may take substantial time for large inputs. It does not execute recorded evidence commands or download missing content.
- Source, runtime, game and distribution decisions remain separate. Valid fixture tests and #2 host observations cannot fill missing runtime evidence.

## Impact on Next Stage

Stage 4 can reacquire selected inputs into a new cache, compare immutable objects and scoped hashes, replay the planned existing-patch checks, finish requirement accounting and publish an explicit `go`, `needs-port` or `blocked` source decision. The decision must retain the Bison/Metal/cross-tool gaps and actual port obligations. #3 remains independent; its schema or manager experiments cannot promote these inputs to a runnable runtime.

## Approval Request

Approve the Stage 3 artifacts and verification results, then authorize Stage 4 source reacquisition, repeat verification, final source decision and the already approved documentation/report locations. This does not authorize component builds, new ports, game execution or security-policy changes.
