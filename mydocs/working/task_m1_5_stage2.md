# Task #5 Stage 2 — Darwin Services and FEX Module Construction

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Implementation plan: [`task_m1_5_impl.md`](../plans/task_m1_5_impl.md)
Stage: 2 — completed October 2, 2026; Stage 3 is not started.

## Stage Purpose

Build the selected FEX Windows CPU modules and their Darwin UnixLib boundary, then verify ordinary native host services before designing executable-memory ownership. Compilation and service execution do not initialize FEX, execute Windows PE code or qualify Megabonk.

Context used: approved task/implementation plans, root/runtime/FEX/tests rules, runtime contracts, source qualification and the retained #4 Wine handoff. Reuse preserves pinned FEX C++/assembly, its eight-call ABI, custom CRT and notices. Reporting follows the [stage procedure](../skills/task-stage-report/SKILL.md), [daily board procedure](../skills/todo/SKILL.md) and central Hyper-Waterfall v0.3.0 template. The requester explicitly approved Stage 2 after the completed Stage 1 report/commit. No Metal/GPU guidance applies to these ordinary native services.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/fex/patches/0002a-*.patch` through `0002e-*.patch`, `series.json`, `.gitattributes` | Five attributed, ordered FEX supplements: Darwin services, conservative CPU features, static ABI link order, enforced configuration and qualified generator interpreter |
| `tools/fex/build.py`, `check.py` | Fresh native/full custom-CRT PE construction and current source, tool, archive, compile, link-map, export and dependency inspection |
| `tools/fex/sign_services.py`, `services.py`, `verify.py` | Ordinary development signing, live preflight, finite native service execution, independent replay and allowlisted export |
| `tests/fex/services/native_services.cpp`, `test_stage2_*.py` | Original native service/policy/ownership fixture and portable construction, malformed-evidence and signing/error controls |
| [Observations](task_m1_5_stage2_observations.json) | Reviewed component digests and outcomes without private profile/device/path/PID data or raw streams |
| `mydocs/plans/task_m1_5_impl.md`, `mydocs/orders/20261002.md` | Stage authorization, actual split CLI clarification and progress |

## Body Change Scope / Lossless Preservation

Changes stay in the approved `runtime/fex/`, `tools/fex/`, `tests/fex/` and internal `mydocs/` locations. No official product/API documentation, original source cache, historical report, #4's 23-patch Wine layer or shared Wine implementation changed. Repository text is English. Private builds, provisioning/signature records and raw logs remain ignored; no credentials, game data or saves are included. No artifacts were deleted for storage. The existing Wine patch directory's scoped attributes are reused for FEX unified-diff context markers; all five patches separately passed `git apply --stat --whitespace=error` and added-source trailing-whitespace checks. This preserves canonical patch bytes and does not suppress source-file checks.

The standalone Darwin UnixLib build leaves upstream's full-root Linux host restriction intact. Eight service ordinals, argument layouts and signed NTSTATUS returns are preserved. File mapping consumes only the caller-transferred duplicate descriptor on every path, verifies size/type/overflow, initializes outputs, uses a read-only mapping and cleans up; the caller's original descriptor survives. PID returns the actual native process ID. Hardware TSO, Linux kernel controls/advice, VMA naming and disabled statistics return explicit unsupported status.

The conservative CPU policy uses the observed 128-byte cache line and source-defined Wine processor-count provider; unavailable ID/MIDR registers stay unavailable, and optional instruction acceleration remains disabled. Nine ordering/cache/profiling settings are enforced before engine initialization; conflicting application/environment entries are rejected before mutation. The native fixture checks policy acceptance/refusal; owned native workers check unsupported hardware-TSO replies and the software-ordering fallback decision, without claiming translated-thread or hardware-TSO behavior. The full PE link retains FEX's custom CRT and uses separate static libc++abi before libc++; selected linker members establish the local `GetSystemInfo`/`NtQuerySystemInformation` provider without widening bootstrap imports.

## Verification Results

Execution context: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), Xcode 26.6/SDK 26.5, Python 3.13, task-local CMake 3.31.8/Ninja 1.13.1 and retained LLVM-MinGW 20260908. Native service targets use deployment 26.5. Construction ran serially with one job and current disk admission; observed admission does not establish an exact build peak. Native images and developer tools selected ARM64; the PE formats retain their distinct Windows ABI roles.

Commands executed (variables represent verified private paths/fresh owned outputs; exact arguments and streams remain private):

```sh
python3 -B tools/fex/build.py modules --phase complete --inputs runtime/fex/inputs.json --config runtime/fex/build-config.json --prepared .build/task5/stage1-inputs3 --tools .build/task5/stage1-tools5 --host-metadata .build/task5/stage2-host-metadata1/observations.json --cross-tools "$pear_fex_cross_tools" --wine-roles .build/task5/stage1-wine-roles.json --output .build/task5/stage2-modules3 --require-empty
python3 -B tools/fex/verify.py modules --root .build/task5/stage2-modules3 --require-complete
python3 -B tools/fex/sign_services.py --build .build/task5/stage2-modules3 --profile "$pear_fex_service_profile" --output .build/task5/stage2-service-sign1 --require-empty
python3 -B tools/fex/services.py run --authorization .build/task5/stage2-service-sign1 --output .build/task5/stage2-services1 --require-empty
python3 -B tools/fex/verify.py stage2 --root .build/task5/stage2-modules3 --services-root .build/task5/stage2-services1 --require-complete
python3 -B -m unittest discover -s tests/fex -p 'test_*.py'
python3 -B tools/check_governance.py
git diff --check
```

- All **nine construction/inspection commands exited 0**; final independent module and combined Stage 2 replay passed. The final source-bound build receipt contains 28 artifacts, 208 ARM64EC and 207 WoW64 source objects, two ARM64 Mach-O UnixLibs, one ARM64 native fixture and both full PE modules. ARM64EC's AMD64 outer PE header is checked with its source-defined CHPE metadata; it is not relabeled as a native ARM64 PE. WoW64's module is ARM64 PE; i386 guest execution remains unperformed.
- Required module exports are closed against pinned source: **20 ARM64EC / 23 WoW64**. Import/delay-import, actual compile arguments, SDK/toolchain/cache options, Ninja link edge, static archive member and selected link-map provider checks passed. A pure-EC archive's empty ordinary symbol tables are accepted only with a valid positive EC index and real member references. CMake array records use a bounded strict reader; other component records retain object-only decoding.
- The exact native fixture/libraries were signed with the existing genuine Host Probe development profile, same-team Apple Development signatures and Hardened Runtime. Only ordinary application/team claims were requested; no architecture/JIT/library-validation exception was requested. Exact unsigned code/data origin and current signatures/profile were replayed; a fresh live preflight preceded execution. Successful signing establishes this development fixture, not distribution permission.
- Both **actual native service runs exited 0**. Each verifies eight services, seven mapping controls, 20 policy controls and two owned/joined workers. Unsupported operations returned `STATUS_NOT_SUPPORTED` (`0xC00000BB`); duplicate-descriptor ownership, mapping cleanup, policy defaults and empty owned output directories passed. These workers never call FEX process/thread/core initialization.
- **110 portable tests passed.** Controls cover source/patch/tool changes, full custom-CRT link proofs, malformed compile/export/archive records, source policy, service/error/cleanup observations, code-origin/signature/profile mismatch and failed signing/preflight evidence. Failed attempts retain actual logs, attempted commands and unavailable exit status; failed preflights cannot be promoted to positive replay. Governance passed 22 routed documents/172 local targets; final report links and staged whitespace are checked before commit.

The accepted build receipt is `0a2c854c0c42484ace9c077b8fb69a73b6e8a323d0b2a8b5e7c8cead90fb21ed`; the accepted service receipt is `7a1f2ee38d7b56687be6dd780adf0fc92c20bc9bb0d219fbda62c0e825b53580`. Exact module/native byte identities are in the observations export. Earlier native checkpoint and unsuccessful full builds remain preserved: one exposed a space-sensitive absolute link-map path, and another completed all compiler/link commands but failed the object-only JSON reader on CMake's valid array. Their records were not rewritten or promoted; final verification uses a fresh build from the corrected producers.

## Residual Risks

- FEX initialization, JIT/publication/backpatch/retirement, Windows PE and x64/i386 guest execution are **unperformed**. The processor-count provider and half-barrier/split-lock ordering suitability inside translated execution remain unverified. Conservative source defaults are not a performance or game claim.
- Executable-memory ownership, macOS authorization for the actual loader/JIT, ARM64EC registration, exceptions/suspension/invalidation and final Wine/FEX integration still require later stages. #4's RWX refusal and native CHPE guard remain unchanged.
- Runtime, Megabonk and ordinary-user distribution qualification remain false. These tests establish finite ordinary-native service behavior on this configuration only; reproduction and wider compatibility remain separate gates. No upstream submission or Pear release/license clearance is claimed.

## Impact on Next Stage

Stage 3 must inventory every executable allocator/dispatcher/bitmap/backpatch path and present a concrete capacity, ARM64EC registration, synchronization, publication and retirement design for explicit review **before any owner prototype**. The retained eight-slot Wine probe is not a complete FEX allocator. Keep persistent cache/profiling disabled, software ordering required and the normal macOS permission boundary intact. Stage 4/5 engine and translated-thread work cannot begin from this service result alone.

## Approval Request

Review Stage 2 and approve continuation to Stage 3's concrete executable-memory inventory/design review. Prototype/integration remains subject to explicit approval of that completed design; no Issue closure, PR publication, merge or game execution is requested here.
