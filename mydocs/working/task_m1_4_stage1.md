# Task #4 — Stage 1: Wine inputs and native cross-toolchain

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)
Implementation plan: [`task_m1_4_impl.md`](../plans/task_m1_4_impl.md)
Stage: 1
Status: complete; Stage 2 requires requester approval.
Date: September 29, 2026

## Stage Purpose

Close the selected Wine component's input and compiler-tool gate before building or executing the Wine runtime. The actual source preparation, compiler fixtures, dependency configuration and evidence checks passed. No PE guest, Wine loader/server, Steam or Megabonk was executed.

Context used: the approved [task-plan background and reuse decisions](../plans/task_m1_4.md#background), [implementation plan](../plans/task_m1_4_impl.md), root/test/documentation rules, and the new scoped [runtime rules](../../runtime/AGENTS.md). Completion follows the installed Hyper-Waterfall v0.3.0 [stage-report](../skills/task-stage-report/SKILL.md) and [daily-board](../skills/todo/SKILL.md) procedures. Pear Apple-tooling is **Not applicable**: SDK Metal framework linkage does not perform graphics execution, validation or rendering qualification.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/AGENTS.md` | Scoped source, execution, identity and evidence boundaries for runtime work. |
| `runtime/wine/inputs.json`, `toolchain.json`, `build-config.json`, `patches/series.json` | Pinned source/tool/dependency records, two explicit configurations, and an empty patch series with unfinished ports. |
| `tools/wine/common.py`, `prepare.py` | Bounded exact-byte records, isolated Git materialization and complete prepared-source verification. |
| `tools/wine/toolchain.py` | Verified archive extraction, native Bison build, compiler/dependency checks and real Wine configure checks. |
| `tools/wine/verify.py`, `evidence.py` | Required observation, artifact/log/source identity checks and privacy-preserving evidence export, including failed attempts. |
| `tests/wine/fixtures/` | Eight original Pear C/C++/assembly/Objective-C/resource/import-export fixtures. |
| `tests/wine/test_*.py` | 95 tests covering input/preparation rejection, tool/archive checks, log integrity, qualification interpretation and privacy. |
| `docs/development/wine-host.md` | Exact acquisition/setup workflow, observed scope and unresolved runtime work. |
| [Stage observations](task_m1_4_stage1_observations.json) | Allowlisted actual results, 34 artifact hashes, source/tool/configuration identities and six failed attempts. |
| `mydocs/plans/task_m1_4*.md`, `mydocs/orders/20260929.md` | Approval/progress records and the next-stage checkpoint. |

## Body Change Scope / Lossless Preservation

All new files use the locations approved in the task and implementation plans. The contributor guide remains in `docs/development/`; no product documentation was placed in `mydocs/manual`. Plan changes record approval and current progress without rewriting the approved technical scope. Official documentation index and historical-audit links remain Stage 6 work.

The original source inventory and its **blocked** combined Wine/FEX/DXMT decision remain unchanged. Wine source was exported from the preserved audit cache into a distinct ignored directory. Every one of its 12,457 regular files, totaling 400,666,524 bytes, was checked against the original Git objects; subsequent verification checks content, executable modes, tree/listing identities, exact inventory and aliases. The original cache fingerprint remained unchanged during preparation.

No existing host probe, runtime-contract schema, manager prototype or roadmap implementation was changed. No upstream Wine patch was applied. Build tools, generated binaries, raw records and downloaded archives remain outside Git. Source/archive notices and their exact hashes are retained in the component records and local extraction.

## Verification Results

Execution context: native Apple M4 Pro, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), Apple clang 21.0.0 and macOS SDK 26.5. The SDK's observed metadata identity is in the sanitized observations. The cross-compiler is the pinned publisher LLVM-MinGW 20260908 universal archive with clang 23.1.1. Every recorded compiler/configure command explicitly selects ARM64 host execution. Universal tools and bundled native dependencies were inspected for their ARM64 slices; produced host fixtures and locally built Bison are ARM64-only.

These are same-host component/compiler observations, not benchmarks, an independently rebuilt LLVM/Apple toolchain, a complete Wine build or game support.

### Exact planned verification commands

The preparation commands were run once into fresh destinations; the final gate subsequently revalidated their existing bytes instead of overwriting occupied output directories.

```sh
python3 tools/wine/toolchain.py inspect --output .build/task4/tool-inspection.json
python3 tools/wine/prepare.py --inputs runtime/wine/inputs.json --source-cache .build/task1-sources/inputs --output .build/task4/inputs --require-empty
python3 tools/wine/toolchain.py prepare --lock runtime/wine/toolchain.json --output .build/task4/tools --require-empty
python3 tools/wine/toolchain.py check --lock runtime/wine/toolchain.json --inputs .build/task4/inputs --config runtime/wine/build-config.json --tools .build/task4/tools --fixtures tests/wine/fixtures --output .build/task4/toolchain-check.json
python3 tools/wine/verify.py inputs --inputs runtime/wine/inputs.json --config runtime/wine/build-config.json --toolchain .build/task4/toolchain-check.json --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

| Verification | Actual Result |
|---|---|
| Source preparation | Passed; 12,457 files and original object/tree/listing identities verified. |
| Tool preparation | Passed; both downloaded archives match their locked size/hash and validated member graph; Bison configure/build/install each exited 0. |
| Native fixture | Passed; ARM64-only executable returned the exact JSON value 42. |
| SDK frameworks | Passed; all 14 declared frameworks linked into an ARM64-only fixture; that fixture was not executed. |
| Windows compiler targets | Passed; aarch64, ARM64EC, x64 and i386 C/C++17, assembler, DLL/EXE, import/export and exact resource payload checks. |
| Unwind metadata | Passed for ARM64, ARM64EC and x64. i386 is an assembly/machine-type control and makes no equivalent SEH claim. |
| ARM64EC support | Passed using the locked archive's genuine `libmingwex.a` ARM64EC members; both linked images contain nonzero CHPE metadata pointers. No dispatcher substitute was introduced. |
| Wine configuration | Both variants passed real configure and a generated `make -n tools/winebuild/winebuild` query. Configure executed its native build helpers; no Wine runtime target or guest was run. |
| Final evidence gate | Passed: 34 required checks and 58 successful commands, tied to current producer/fixture/configuration/source/tool/artifact/log bytes. |
| Unit tests | `Ran 95 tests` / `OK`. |
| Governance | `PASS: 22 documents, 152 local targets; skill routing and source inventory consistent (offline)`. |
| Whitespace | `git diff --check` passed. |

The `arm64` configuration generated `HOST_ARCH=aarch64` and `PE_ARCHS=aarch64`. The companion generated `PE_ARCHS=aarch64 arm64ec` and the required auxiliary x86_64 cross-compiler. Both selected the exact pinned `clang` invocation, retained Mac-driver rules, AppKit and CoreText, and omitted FreeType, Fontconfig and CoreAudio libraries as declared. Both reported **EGL development files not found**. This is an explicit unqualified optional capability, not a silent passing feature. Font rendering, built fonts, audio, network authentication, codecs, Vulkan and X11/Wayland remain outside this fixture configuration.

The ARM64EC object machine is `0xA641`; its linked PE image header uses `0x8664`. This is Windows artifact metadata and does not imply an Intel macOS process. None of the four PE target fixtures was executed.

### Identities and preserved failures

The [sanitized observations](task_m1_4_stage1_observations.json) bind all current producer/test source hashes, fixtures, prepared sources/tools, configuration, SDK metadata and output artifacts. The final raw check SHA-256 is `81bdc87e4d2b33ee3327520190d1ec8954975fd0c147a3a93b169a68de678bbe`. Original audit SHA-256 remains `535cdcb7b2e76d4bc536d63ad7d17d31f562f438b7850a75a0ace1b9c88466b8`.

Raw commands, diagnostic streams and identities remain in `.build/task4/`. Public export contains allowlisted role IDs/counts/hashes only; it rejects an unexpected command ID and rebinds exported bytes to the assessed record. Tests are synthetic only where exercising rejection paths; actual compiler/host observations come from real subprocesses and files.

| Preserved Attempt | Observed Failure and Resolution |
|---|---|
| 1–2 | Resource compiler treated the absolute input as an option. Use its supported joined `/FO` output and `--` input separator; retain the complete resource-content assertion. |
| 3 | ARM64EC assembler selected the x64 source branch. Match the compiler's actual `__arm64ec__` macro. |
| 4 | ARM64EC links lacked dispatcher support. Link the genuine ARM64EC members already present in the pinned `libmingwex.a`. |
| 5 | Driver raised an uncaught path-type error before compiling the proposed support source. Preserve the transcribed original traceback/exit 1 in a distinct driver-failure record; no completed check report is invented. Fix variable handling and failure capture. The final route uses the bundled CRT. |
| 6 | i386 export naming required LLD's GNU/MinGW linker mode. Use the supported `/lldmingw` mode for that control target. |

A pre-final complete run, attempt 7, is retained separately (SHA-256 `22a6b98931a2d898ce6766549da75149208fdcf99cc53c4d52c78f26733fd28a`). It exposed a compiler basename alias issue in discovery; the final run above verifies the corrected explicit invocation. An earlier fixture-authoring compile without an explicit SDK failed to find `stdio.h`; its record is retained at `.build/task4/fixture-author-check-native/command-0.json`, SHA-256 `c7e43222b206848708dffabf159e509889a98c9c3d0a4ddac587347d1103bfca`. The integrated checks use the explicit SDK and pass.

Final unit-test log SHA-256: `c0d24e914836e1ebfc26b2e4f8bf3ab8cf7eac5d74dea4f04132d00e51ceaac9`.
Governance log SHA-256: `e9d34398a3e7b8e43f1331750dae1c76553f404966bf9f60d578fccd5436c221`.

## Residual Risks

- Wine is configured, not fully built or executed. Darwin loader/page layout, actual executable authorization, x18 transitions, thread/exception handling and Cocoa callback behavior still require the remaining #4 stages.
- ARM64EC link/metadata success does not validate loader initialization or translated x64 execution. FEX and DXMT integration remain separate tasks; the combined source decision stays blocked.
- The tool archive is publisher-produced; Apple tools/SDK remain external prerequisites. SDK metadata and selected versions are bound, but this does not independently reproduce or hash every Apple SDK file.
- This is a same-host setup. A different tool/SDK version needs a reviewed lock and new observations. Fresh final component reproduction remains Stage 6.
- The configured path adapters use retained owned `/private/tmp/pear-task4-*/workspace` aliases. Their Bison/build dependents may still reference them; preserve exact aliases until those outputs are retired.
- Optional feature exclusions must be revisited before Steam/game support. Neither normal-user packaging nor permission inheritance is established here.

## Impact on Next Stage

Stage 2 can start from the verified source/tool directories and two explicit configurations, with at most four build jobs and separate output directories. It must materialize fresh patchable source, build the real ARM64 Wine host, implement loader/bootstrap changes as attributable patches, and check actual per-executable signing/provisioning before restricted operations. No #2 authorization may be assumed to transfer to the new Wine executable.

The existing audit cache, failed attempts and private local outputs remain available for diagnosis and subsequent work. #4 stays open; no PR publication or merge is part of this stage boundary.

## Approval Request

Approve these Stage 1 artifacts and results to enter **Stage 2 — Native build, loader and authorization** under the existing implementation plan.
