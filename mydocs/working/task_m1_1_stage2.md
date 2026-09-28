# Task #1 Stage 2: Source coverage, existing patches and terms

GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Implementation plan: [`task_m1_1_impl.md`](../plans/task_m1_1_impl.md)
Stage: 2
Date: September 28, 2026

## Stage Purpose

Identify reusable implementation and remaining macOS integration work at the acquired source revisions. Bind implementation, existing-patch and declared-terms findings to inspected bytes, without treating source availability or the completed host probe as a functioning runtime.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/sources/manifest.json` | Updated Stage 2 inventory: 30 components, explicit coverage requirements, existing-patch provenance and scoped terms/evidence references. The additional component records the historical Wine export patch and its original source base. |
| `mydocs/working/task_m1_1_stage2_evidence.json` | New evidence: 181 Git source/notice files, 37 cited implementation ranges, 10 coverage requirements, 22 Git terms records, six bundled-notice groups, one existing patch and the bounded CrossOver archive review. |
| `mydocs/plans/task_m1_1_impl.md` | Recorded Stage 2 authorization and completion; later stages retain approval checkpoints. |
| `mydocs/orders/20260928.md` | Current parallel-task status; task completion and Issue closure are not implied. |
| `mydocs/working/task_m1_1_stage2.md` | This verification and handoff report. |

Source repositories, archive/patch bytes, disposable indexes, selected archive members and raw audit logs remain local under ignored `.build/task1-sources/`. They are inputs for subsequent stages, not release contents.

## Body Change Scope / Lossless Preservation

Only the approved inventory and workflow-record locations changed. Stage 1 evidence and report remain byte-identical historical records. Existing architecture/research documents, Issue #2 evidence, source code, operating manuals and Issue #3 contracts are unchanged in this branch.

The audit retains `audit_complete: false`, `decision: unassessed` and `source_ready: false`. Individual substantiated `needs-port` findings do not prematurely issue the later final audit decision. Conditional excluded dependencies, toolchain compatibility, actual binary contents and fresh acquisition remain unresolved where appropriate.

## Verification Results

The planned source inspection and existing-patch commands were executed with actual acquired inputs. `PEAR_SOURCE_REPO`, `PEAR_SOURCE_COMMIT` and `PEAR_SOURCE_FILE` identified each recorded source row; patch checks used fresh cache-local absolute index paths and the immutable bases listed below. Literal expanded arguments, outputs and identities are preserved in the evidence document.

```sh
git -C "$PEAR_SOURCE_REPO" show "$PEAR_SOURCE_COMMIT:$PEAR_SOURCE_FILE"
shasum -a 256 "$PEAR_PATCH_FILE"
GIT_INDEX_FILE="$PEAR_SOURCE_INDEX" git -C "$PEAR_SOURCE_REPO" read-tree "$PEAR_SOURCE_COMMIT"
GIT_INDEX_FILE="$PEAR_SOURCE_INDEX" git -C "$PEAR_SOURCE_REPO" apply --cached --check "$PEAR_PATCH_FILE"
GIT_INDEX_FILE="$PEAR_SOURCE_INDEX" git -C "$PEAR_SOURCE_REPO" apply --cached "$PEAR_PATCH_FILE"
python3 -m json.tool mydocs/working/task_m1_1_stage2_evidence.json > /dev/null
git diff --check
```

The apply command runs only after a successful check. A rejected candidate is preserved as an expected negative observation, as specified by the approved plan.

| Check | Actual result | Scope |
|---|---|---|
| Exact Git source reads and independent byte review | 181 files: sizes, SHA-256 and Git blob IDs match; all 37 cited ranges exist | Fixed source revisions and cited text; no behavioral execution. |
| Evidence-reference audit | 438 references resolve; 250 unique identifiers | Explicit historical Stage 1 versus Stage 2 reference resolution. |
| Existing patch hash | SHA-256 `8a8799de8abee169fe9c22f982871a904d38e163c641633599f051c3023fb0fb` | Exact 3,358-byte patch file. |
| Original-base patch replay | `read-tree`, check and apply exit 0; result equals published tree | Patch `6197fc78f72184b5f8eed5df306f5e4a48c1153f`, base `a365b39f9769ccffeaaf20a45151b671fe763dc3`, resulting tree `ffb8dd5bf8171ec59c40ee3f5d66f17408206890`. |
| Selected Wine patch checks | Both exit 1, documented `does_not_apply`; neither applied | Upstream `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` and DXMT-linking candidate `87ba10bb3aa8ea636dff5c2030b376da1627910a`. |
| CrossOver archive review | 16 selected regular members hash-rechecked; 10,124 text files scanned | Archive SHA-256 `ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872`; 962 NUL-containing files excluded, links not followed, no source executed. |
| JSON syntax, whitespace and privacy review | Exit 0; no private absolute paths or payloads found in committed artifacts | Both JSON files parse. This is not the Stage 3 inventory validator. |
| Historical preservation | Stage 1 evidence/report unchanged | No retroactive rewriting of previous observations. |

### Findings and downstream obligations

| Area | Reuse and remaining work |
|---|---|
| Loader and memory — #4 | Wine has native loader/reservation machinery. Its selected Mac linker settings use 4 KiB PAGEZERO, while the measured host route preserved 64 KiB. Reconcile actual signed layout and child creation. The optional Intel Mac preloader's unsupported-CPU branch does not prove it must be used for ARM64. |
| ABI, signals and JIT — #4/#5 | Wine already contains Apple ARM64 signal context and x18-related assembly. Custom-x18 transitions, callbacks, 4 KiB process geometry, code-cache policy, exceptions and asynchronous execution still need integrated implementation and tests. Exact-token absence is bounded evidence, not proof that no alternate implementation exists. |
| Translator host services — #5 | FEX provides Windows ARM64EC/WoW64 modules and a UnixLib boundary. Its inspected host implementation uses Linux `prctl`, `.so` targets and `rt`; macOS needs a compatible host implementation. Hardware TSO selection must cover actual participating threads or retain the appropriate software path. |
| Graphics driver interface — #7 | DXMT supports a function-table path and individual-symbol fallback. The historical export patch is not directly applicable to the selected candidates. Their window-data layout also differs from DXMT's expected fields, so symbol visibility alone is insufficient. |
| Shader/native pairing — #7 | ARM64EC PE and native ARM64 shader/Metal build paths exist. Exact LLVM/tool/SDK pairing, callbacks and real output correctness remain unverified. |
| Published comparison sources | The inspected CrossOver Wine subtree contains useful Apple ARM64 handling and identifies Wine 11.0. It does not establish a complete reproducible ARM64 Preview patch series. The selected Wine 11.2 publisher explicitly describes that release as for DXMT linking, not a working runtime. |

The selected DXMT revision declares LGPL-2.1-or-later; an older version's MIT label must not be copied forward. FEX's inspected principal license is MIT, while bundled files retain their own notices. FEX and DXMT upstream contribution policies restrict AI-generated code submissions; these are distinct from downstream license permissions, and no upstream submission occurred. Wine's current external submission-policy page could not be fully retrieved. DirectX header notice reconciliation, selected bundled exceptions and actual release payload obligations remain explicit.

## Residual Risks

- No Wine/FEX/DXMT source was configured, built or executed. Patch applicability and source inspection cannot qualify gameplay, performance, signing or distribution.
- Public merge-request/policy retrieval was incomplete. Do not interpret the audit as proof that no other relevant public patches exist.
- The CrossOver scan is limited to the stated archive, Wine text scope and reviewed members; it is neither an aggregate license clearance nor a complete Preview implementation inventory.
- Toolchain/build closure, conditional dependencies, exact linked notices and the ordinary-user distribution path remain open. Terms observations are bounded engineering records, not blanket release approval.
- The Stage 3 inventory validator and Stage 4 fresh acquisition/final decision have not run.

## Impact on Next Stage

Stage 3 pins candidate installed tool/SDK metadata and adds the bounded inventory validator and rejection tests. It must distinguish a valid incomplete or negative audit from source readiness, resolve both evidence generations and check the newly acquired patch input. The named #4/#5/#7 requirements are future implementation gates; this report neither starts those issues nor changes their scope.

## Approval Request

Review the Stage 2 evidence and expected negative findings. Approval to proceed authorizes Stage 3's toolchain inventory and source-provenance validator/tests within the approved implementation plan. Stage 3 has not started; no game execution, runtime port or distribution qualification follows from this stage.
