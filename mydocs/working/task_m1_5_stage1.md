# Task #5 Stage 1 — FEX Source and Target-Build Contract

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Implementation plan: [`task_m1_5_impl.md`](../plans/task_m1_5_impl.md)
Stage: 1 — completed October 2, 2026; Stage 2 is not started.

## Stage Purpose

Establish the exact selected FEX source/dependency/tool closure and real native ARM64, ARM64 PE and ARM64EC PE compilation prerequisites before porting Darwin services. This is source inspection and original compile/link fixture evidence. It does not build or execute a FEX module, translate x64 code or qualify Megabonk.

Context used: the approved task/implementation plans, root/runtime/tests rules, architecture/runtime contracts and #4 handoff referenced by those plans. The requester approved this detailed plan and Stage 1 in the same thread. Reporting follows the [stage procedure](../skills/task-stage-report/SKILL.md), [daily board procedure](../skills/todo/SKILL.md) and central stage template from Hyper-Waterfall v0.3.0. Metal engineering guidance is not applicable to this source/compiler stage.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/fex/AGENTS.md`, `inputs.json`, `toolchain.json`, `build-config.json` | Scoped source, target, terms, tool and configuration contracts; no runtime eligibility |
| `tools/fex/common.py`, `prepare.py` | Fresh owned derivation, full Git/blob/mount/notice/interface closure and bounded private operation receipts |
| `tools/fex/tools.py`, `byte_readers.py` | Exact task-local ARM64 build-tool preparation/replay and component-local reuse of Wine binary readers |
| `tools/fex/check.py`, `verify.py` | Real compile/link probes, bounded PE/COFF/ARM64EC/EC-index readers and closed independent evidence replay |
| `tests/fex/test_stage1_*.py`, `capabilities/*.cpp` | 59 portable refusal/closure controls and four original compile-only source fixtures |
| [Observations](task_m1_5_stage1_observations.json) | Reviewed finite public export; no private roots, raw logs, credentials or signing material |
| `mydocs/plans/task_m1_5_impl.md`, `mydocs/orders/20261002.md` | Approval and actual recipe clarifications; synchronized Stage 1 status, Issue still in progress |

## Body Change Scope / Lossless Preservation

All additions use the approved `runtime/fex/`, `tools/fex/`, `tests/fex/` and `mydocs/` locations. No official/product/API document, shared Wine helper, #4 patch series or historical #1 source decision changed. Preserve original source caches, builds and all unsuccessful attempts; no requester or other worker artifacts were removed. Repository documents and comments are English.

Reuse retains FEX C++/assembly, its enabled gitlink graph and MIT/dependency notices. Seven exact components were derived: FEX, cpp-optparse, fmt, range-v3, rpmalloc, unordered_dense and xxHash. Disabled/root-only gitlinks retain explicit decisions. Existing Wine data helpers and bounded binary readers were reused at their actual component boundary; no Rust rewrite, Linux userspace port or upstream submission was made.

## Verification Results

Execution context: Apple M4 Pro, 24 GiB memory, macOS 26.5.2 (25F84), Xcode 26.6, SDK 26.5, Apple Clang 21 and Python 3.13. Existing LLVM-MinGW 20260908 / LLVM 23.1.1 was fully checked against the locked archive/current extracted files. Host metadata observed about 43.7 GiB free before final probes; a full FEX build peak is still unknown. Only approved developer tools ran; PE DLLs, Wine, UnixLib services, FEX, Steam and game code did not run.

Commands executed (private cache/role handles are withheld; exact argument arrays and raw streams remain in ignored owned receipts):

```sh
python3 tools/fex/tools.py prepare --toolchain runtime/fex/toolchain.json --output .build/task5/stage1-tools5 --artifact-cache .build/task5/stage1-tools/downloads --source-cache .build/task5/stage1-tools2/ninja.git --require-empty
python3 tools/fex/prepare.py --inputs runtime/fex/inputs.json --source-cache <read-only-selected-cache> --output .build/task5/stage1-inputs3 --require-empty
python3 tools/fex/check.py capabilities --inputs runtime/fex/inputs.json --config runtime/fex/build-config.json --prepared .build/task5/stage1-inputs3 --tools .build/task5/stage1-tools5 --cross-tools <verified-locked-tools> --wine-roles <verified-local-Wine-role-record> --output .build/task5/stage1-capabilities6 --require-empty
python3 tools/fex/verify.py stage1 --root .build/task5/stage1-capabilities6 --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_stage1_*.py'
python3 tools/check_governance.py
git diff --check
```

- Source preparation/replay passed: **6,948 files**, **40,203,909 source bytes**, **45,864,960 archive bytes**, seven exact components and 37 bounded source operations. All source/mount/terms/producer identities are closed.
- Task-local **CMake 3.31.8** passed actual pinned publisher checksum/payload/full-extraction/native-slice and version checks. **Ninja 1.13.1** was built as ARM64 from commit `79feac0f3e3bc9da9effc586cd5fea41e7550051`, tree `28c433f85d2a313387f32724bae3e08c6bbf0b0b`; source/archive/blob/mode/notice identity is independently replayed. SDK path and version matched the selected lock.
- Required capabilities and independent replay passed: **4 required checks, 17 recorded commands, 15 compile-only artifacts**. Native ARM64 and both PE targets compiled all eight service ordinals and all seven argument structure sizes/alignments from the actual selected header, plus selected offsets. Module source exports number 20 ARM64EC and 23 WoW64; TEB CPU-area offset is `0x1788`. These are inspected/compiled contracts, not live service or module results.
- Each real DLL linked static libc++, libc++abi, libunwind and compiler builtins. COFF `/map` tied required clock/guard/unwind/division symbols to actual archive members. The source-derived ntdll import archive and actual `NtYieldExecution` import/export were inspected; dynamic C++ runtime DLL dependencies were refused.
- ARM64EC output has an AMD64 outer PE header and positive **Version 1 CHPE** with inspected ARM64EC and x64 thunk ranges. This matches the default MinGW `chpe.S` DLL form. It is not native x64 proof, guest execution or permission to weaken #4's loader guard.
- **59 portable tests passed.** Required refusal controls cover source/mount/blob changes, malformed archives and EC indices, escaping/cyclic aliases, wrong targets/metadata, incomplete tools/commands/logs, altered configuration and nested execution/private-field overclaims. Governance passed 22 routed documents and 172 local targets; final plan/report links and staged whitespace are checked before the bundled commit.

Preserved failures informed the accepted recipe: Git-path resolution, framework directory aliases, an omitted SDK during Ninja bootstrap, an incomplete standalone CRT link, a bundled ABI copy shadowing the separate archive, and the earlier executable-specific CHPE/range predicate. The final fixture uses the toolchain's complete default DLL CRT and source-matched DLL metadata. It does **not** establish the full FEX `-nostdlib -nostartfiles -nodefaultlibs`/custom-CRT build, which remains Stage 2.

## Residual Risks

- FEX root CMake still lacks the selected Darwin port. Full modules/custom CRT, host features, native services, hybrid loading, JIT ownership, translator initialization and guest dispatch remain unperformed.
- Matching header layouts do not establish cross-platform C++ object ABI or live callback behavior. Companion Wine archives contain ARM64 and ARM64EC members; broader library pairing still needs actual component construction.
- Disk cache/profiling stay disabled and software TSO stays enabled. Effective Darwin CPU features and per-thread behavior are unperformed; no invented hardware TSO capability is claimed.
- The original aggregate source-ready decision remains blocked. Runtime, game and distribution qualification are all false.

## Impact on Next Stage

Stage 2 may use the verified source/tool contract to implement and test the selected Darwin UnixLib services and construct native/Windows modules. Recheck real storage and per-executable authorization before dependent operations. Do not call `ProcessInit`, `ThreadInit`, `InitCore` or `CreateThread` before the later executable-memory owner gate; even initialization may allocate executable memory. Stage 3's concrete measured JIT design still requires separate requester review before a prototype. Preserve independent CPU and graphics patch ownership and the retained #4 baseline.

## Approval Request

Review Stage 1 and approve explicit continuation to Stage 2, limited to the already planned Darwin services and module construction. This does not authorize the unresolved JIT prototype, guest dispatch, Steam/game execution or distribution.
