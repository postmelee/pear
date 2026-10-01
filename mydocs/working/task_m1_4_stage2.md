# Task #4 — Stage 2: Authorized native Wine bootstrap

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)
Implementation plan: [`task_m1_4_impl.md`](../plans/task_m1_4_impl.md)
Stage: 2
Status: complete; Stage 3 requires requester approval.
Date: September 29, 2026

## Stage Purpose

Build both selected Wine variants from pinned source, authorize the actual ARM64 macOS loader, and verify native initialization before Windows PE entry. Both builds and all three real bootstrap cases passed their final evidence gates. The executed native process roles reported ARM64 and untranslated execution. No Windows PE, guest x18 initialization, FEX, Steam or Megabonk was executed.

Context used: the approved [task plan](../plans/task_m1_4.md), [implementation plan](../plans/task_m1_4_impl.md), [Stage 1 evidence](task_m1_4_stage1.md), root/runtime/test/documentation rules, and Hyper-Waterfall v0.3.0 [stage-report](../skills/task-stage-report/SKILL.md) and [daily-board](../skills/todo/SKILL.md) procedures. Existing Wine C/assembly/build languages are retained. Pear Apple-tooling is **Not applicable**: this stage performs no Metal rendering, capture or graphics qualification. Apple's provisioning/bundle guidance is linked in the [contributor guide](../../docs/development/wine-host.md); the local `codesign(1)` manual documents the signature-page option used below.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/wine/patches/0001-darwin-loader-layout.patch` | Attributable configure/link-layout changes, native loader re-execution and checked Darwin page-mode requests. |
| `runtime/wine/patches/0002-native-bootstrap-evidence.patch`, `series.json`, `.gitattributes` | Opt-in native Wine observations, real owned-server binding and a stop before PE/guest startup; ordered patch identities and patch-format whitespace rules. |
| `tools/wine/build.py` | Isolated builds, exact command/log/source/tool/output inventories and narrowly checked validation-only completion revisions. |
| `tools/wine/modules.py` | Independent PE parsing and pinned LLVM-reader comparison for seven selected modules, including hybrid metadata. |
| `tools/wine/signing.py` | Actual per-image requirements, dedicated profile verification, inside-out development signing, origin/signature/page checks. |
| `tools/wine/run_fixtures.py` | Bounded real bootstrap, timeout and wrong-prefix cases, native process observations and owned cleanup. |
| `tools/wine/verify.py`, `evidence.py` | Build/run gates and allowlisted public evidence, with original failed builds and failed runtime retained. |
| `tests/wine/cases.json`, `fixtures/bootstrap_native.c`, `fixtures/sentinel.c` | Fixed case definitions and original Pear native launch/sentinel helpers. |
| `tests/wine/test_build.py`, `test_modules.py`, `test_signing.py`, `test_runner.py`, `test_evidence_stage2.py` | Rejection, binary classification, authorization, lifecycle and evidence-integrity tests. |
| [Stage observations](task_m1_4_stage2_observations.json) | Actual build/run identities, signed authorization checks, public source hashes and preserved failure summaries. |
| `docs/development/wine-host.md`, task plans, daily board | Reproduction instructions, measured limits, actual output substitutions and Stage 3 checkpoint. |

## Body Change Scope / Lossless Preservation

The approved official documentation location remains `docs/development/wine-host.md`; this report and its sanitized observations use the approved `mydocs/working/` paths. No official documentation was moved into workflow manuals. Plan edits record execution, helper decomposition and preserved output names without expanding the approved stage. The task remains in progress because Stages 3–6 are unfinished.

The original Wine/FEX/DXMT audit remains **blocked** and byte-for-byte unchanged. Prepared source/tool inputs were verified and copied before patching. Both successful build variants use Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892`, the same patch/config/tool/SDK inputs and the same final patched-source manifest. Generated `configure` changes correspond to the reviewed `configure.ac` changes. Wine's existing license and notices are retained; the new Wine diagnostic header carries LGPL attribution.

Earlier failed output directories, original producer snapshots, logs and signing revisions remain local. Validation-only recovery preserves the original failed build record separately and never reruns or fabricates a successful compilation. The old failed signed runtime is not promoted by the later successful attempt. Game files, authenticated prefixes, saves, profiles, credentials and raw diagnostic identifiers are excluded from Git.

## Verification Results

Execution context: native Apple M4 Pro, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), Apple clang 21.0.0 and SDK 26.5. Cross-tools are the pinned LLVM-MinGW 20260908 publisher archive with clang 23.1.1; Bison 3.8.2 was built locally in Stage 1. Native build commands select ARM64. Large builds were serialized with at most four jobs. These are same-host development and correctness observations, not performance measurements or independent-machine reproduction.

### Commands and retained output names

The original `.build/task4/build-arm64` configure failure remains retained. After registering the added Wine header correctly, the full native build ran in `.build/task4/build-arm64-attempt2`; the full companion ran in `.build/task4/build-arm64ec`. Both completed all seven patch/configure/build/install/helper commands with exit 0. Their first driver records failed installed-output validation, for the reasons below. Corrected validation-only completion checked existing bytes and retained original failed records and producer snapshots. The final build gate passed independently.

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-arm64-attempt2 --jobs 4
python3 tools/wine/build.py --variant arm64ec-build --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-arm64ec --jobs 4
python3 tools/wine/build.py --finalize-only .build/task4/build-arm64-attempt2
python3 tools/wine/build.py --finalize-only .build/task4/build-arm64ec
python3 tools/wine/modules.py --build .build/task4/build-arm64-attempt2 --output .build/task4/build-arm64-attempt2/modules.json
python3 tools/wine/modules.py --build .build/task4/build-arm64ec --output .build/task4/build-arm64ec/modules.json
python3 tools/wine/verify.py build --root .build/task4/build-arm64-attempt2 --companion .build/task4/build-arm64ec --require-complete
python3 tools/wine/signing.py inspect --build .build/task4/build-arm64-attempt2 --output .build/task4/signing-requirements.json
python3 tools/wine/signing.py prepare --build .build/task4/build-arm64-attempt2 --local-input .build/task4/private/signing.json --output .build/task4/signed-page4k --require-empty
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed-page4k --output .build/task4/runs-stage2-page4k --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage2-page4k --suite bootstrap --require-complete
python3 tools/wine/verify.py inputs --inputs runtime/wine/inputs.json --config runtime/wine/build-config.json --toolchain .build/task4/toolchain-check.json --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git apply --stat --whitespace=error runtime/wine/patches/0001-darwin-loader-layout.patch runtime/wine/patches/0002-native-bootstrap-evidence.patch
git diff --check
git diff --cached --check
```

Unified-diff context markers triggered the initial staged whitespace check. Patch-local attributes exclude those required format bytes from ordinary file indentation checks; `git apply --stat --whitespace=error` checks the added source lines, and the staged check then passes. Neither patch was rewritten, so built-source identities remain unchanged.

This block records the relevant invocations, not a script to overwrite retained evidence. Fresh reproduction uses new destinations and the current complete recipe; it should not need validation-only recovery. Source/test hashes in the observations distinguish executed producer revisions from the final reviewed tools.

### Builds and module inspection

| Verification | Actual Result |
|---|---|
| Native build | Passed final gate: 37 ARM64-only Mach-O images, 746 executable PE images and 10 separate WinMD metadata containers. |
| ARM64EC companion | Passed final gate: 37 ARM64-only Mach-O images, 749 executable PE images and 10 WinMD containers; not executed. |
| Common input binding | Both variants share exact source, ordered patches, configuration, fixture, tool and SDK identities. |
| Selected module inventory | Seven modules per variant independently parsed and cross-checked against actual pinned LLVM output: `ntdll.dll`, `kernel32.dll`, `kernelbase.dll`, `win32u.dll`, `winemac.drv`, `wineboot.exe`, `wow64.dll`. |
| Signing | Dedicated Wine-loader profile matched the application, platform, device, certificate and restricted grant. All 37 copied native images passed effective-signature and source-origin checks. |
| Stage 1 regression | Passed: original 34 checks / 58 commands remain bound; original combined source audit remains blocked. |
| Unit tests | `Ran 236 tests` / `OK`; negative-path fixtures do not substitute for actual restricted execution. |
| Governance and whitespace | `PASS: 22 documents, 153 local targets; skill routing and source inventory consistent (offline)`; `git diff --check` passed. |

The native module inventory records import/delay-import/export counts respectively: ntdll 0/0/1479, kernel32 2/0/1355, kernelbase 1/0/1428, win32u 1/0/1540, winemac 5/0/0, wineboot 7/8/0 and wow64 1/0/28. Forwarders, RVAs and raw reader logs remain hash-bound locally. This is a selected binary-structure inventory, not proof that all imported Windows APIs execute.

The companion's hybrid files reside under `aarch64-windows`. Five selected modules contain verified ARM64X metadata; wineboot and wow64 remain ordinary ARM64. Three other exact EC-only outputs (`dpnsvr.exe`, `vcruntime140_1.dll`, `xtajit64.dll`) have AMD64 PE headers with independently checked CHPE v2 executable code ranges. The classifier accepts those exact cases only in the companion variant; it does not accept arbitrary x64 images or infer an Intel macOS host process. The ten WinMD containers have no executable code and are validated as CLR/Windows Runtime metadata separately.

### Real native execution

| Case | Expected and Observed Result | Cleanup |
|---|---|---|
| Native bootstrap | Passed: actual loader re-execution, owned server peer and reciprocal initialization handshake, measured native initialization, stop before PE entry; exit 0. | All owned children reaped; sentinel survived. |
| Intentional timeout | Passed: real handshake reached, declared hold armed, 1.5-second timeout observed and bounded shutdown completed. | All owned children reaped; sentinel survived. |
| Wrong-prefix server | Passed: actual loader rejected the mismatched owned server/prefix without falling back to an unowned server; no accepted handshake. | All owned children reaped; sentinel survived. |

Each case owns three process roles: server, loader and sentinel. The bootstrap helper becomes the Wine loader through SETEXEC within the loader PID; Wine then performs its own observed generation-0 to generation-1 re-execution. The helper, loader, server and sentinel each supply native/untranslated observations for their actual executable role. No missing or denied translation query can pass.

The loader observed 4 KiB user/VM pages over 16 KiB kernel pages. Ordinary server/helpers retained native 16 KiB geometry. The loader's 64 KiB PAGEZERO was unreadable at both tested ends. Wine's actual shared-data address `0x7ffe0000` was a read-only 4 KiB mapping. The successful normal case enumerated 348 loaded loader images and 45 server images. All reported images had ARM64 headers. Owned images were UUID/hash-bound to the signed bytes; system images had structurally valid observed UUIDs and paths restricted to the allowed OS locations, without an independent OS image inventory comparison. These counts describe this host's finite loaded-image snapshot, not every possible runtime dependency.

The exercised path reaches `__wine_main`, native virtual/environment initialization, the AppKit main-thread run loop, Wine's initialization thread, native pthread TLS and `server_init_process`. The hook stops before PE load, later shared-data remapping and guest x18 startup. Future Windows child-process routes are source changes only at this stage; nested guest callbacks and x18 mode transitions remain unexecuted.

### Preserved failures and correction

| Attempt | Failure and Resolution |
|---|---|
| Initial native configure | Wine's build metadata omitted registration of the added diagnostic header. Register it in `include/Makefile.in`, retain the failed tree/logs and build a fresh native output. |
| Native post-build validation | The validator expected the wrong Mac-driver `.so` basename. Require actual `winemac.so` and `win32u.so`; preserve the complete build and original failure, then validate exact bytes without rebuilding. |
| Companion post-build validation | The original classifier did not account for the pinned source's narrow EC-only PE images and non-executable WinMD metadata. Parse their actual metadata and executable ranges, reject arbitrary wrong architectures, preserve the original failure and apply a validation-only completion revision. |
| Companion module-reader output | Genuine hybrid metadata exceeded the initial reader output bound. Raise this tool's finite cap to 1 MiB, retaining a 60-second deadline and native reader identity; runtime output limits remain unchanged. Prior native module inventory and producer bytes are retained. |
| Initial profile | The Host Probe profile did not match the Wine-loader App ID and was rejected before restricted execution. The requester supplied the dedicated Wine-loader profile; its actual checks passed. |
| First signed runtime | All three loader cases terminated with SIGBUS before any loader event; server/helper startup and owned cleanup succeeded. Retain this complete failed run and old signing producer. The matched owned-process crash identified a kernel code-signature rejection during initial dyld image inspection. |
| Corrected signed runtime | Default development signing had changed the 4 KiB-segmented loader's CodeDirectory to 16 KiB signature pages. Apply `codesign --pagesize 4096` to the actual loader app and verify the reported signature page size. The same compiled code and effective grants then passed all three real cases. |

Strict disk signature checks had passed even for the first failed runtime. The observed fix concerns the kernel loading this executable layout on this host; it is not a claim about every signature or macOS version. No platform protection was disabled, no broad entitlement was added, and no JIT entitlement was requested. Hardened Runtime and library validation remain enabled. Only the actual loader receives the cross-architecture claim; ordinary helpers and the server do not inherit it.

The [public observations](task_m1_4_stage2_observations.json) include three failed build records and the original failed native suite. Historical records are hash-checked without pretending that the old signing bytes pass the current runtime gate. Missing historical evidence stays explicitly partial; altered retained bytes are rejected. Public output includes role/count/hash/outcome fields, not raw logs, PIDs, nonces, device/team/certificate identifiers or local paths.

### Evidence identities

| Record | SHA-256 |
|---|---|
| Native final build | `065a2952850624ce281252bb5cb17e4c7c368481a768720c7255bc3351e6a2a6` |
| Companion final build | `a337f81981349eaa01f4f87f8d147c68e3ab27c767f808d8fedb03ac461e6409` |
| Final signed runtime | `804b5f89564da3a7c2b3ae3fa4bb6521a3cbf40d52cc11383dbcbf547d28674f` |
| Passing native suite | `3074ace745b410d8b510b5c6bf08251f6f6b53aab304b7997d053eb14afed93d` |
| Unit-test log | `0160fc491b9a76fe5bdc682206bf8c80d10b59bb532c39507f513f3f6f89e8bf` |
| Public stage observations | `cadb3514d41506d07387b7f7b14db1fb9fae2025b0cc801d0e2d1ba6e2ac2d86` |
| Governance log | `3da10d058ed351b8ac6116c4d30657562861743bc9ee637ef9ecb94bc75aa120` |

Complete producer/finalizer, patched-source, input, tool, module, command and case identities are in the observations and retained ignored records. The original source-audit SHA-256 remains `535cdcb7b2e76d4bc536d63ad7d17d31f562f438b7850a75a0ace1b9c88466b8`.

## Residual Risks

- No Windows PE/API, guest x18 transition, exception, GUI callback, translator, renderer or game has been qualified. The ARM64EC companion is build-only evidence.
- Process observation covers the finite directly owned bootstrap roles. Post-spawn observer registration and possible escaped-session descendants are not a general game-process coverage claim. Unknown membership, output overflow, cleanup gaps or surviving children fail the controlled run.
- The development bundle retains Wine's relative runtime layout under `Contents/Resources/runtime`. This is a tested local development arrangement, not qualified public distribution, notarization or a user-facing installer. Profile expiration and actual device/certificate authorization are rechecked before execution.
- Optional networking/authentication, codecs, audio, external font backends, Vulkan, X11/Wayland and unavailable EGL remain outside this fixture configuration. Steam/game use needs a reviewed configuration and new evidence.
- Apple tools/SDK remain external prerequisites; the LLVM archive is publisher-produced. The recorded same-host results do not reproduce the compiler or independently qualify another Mac/macOS version.
- Existing full builds were validated with narrowly corrected output classifiers. Fresh complete reconstruction using the final source recipe remains Stage 6; exact producer revisions are not concealed.
- Preserve task-owned temporary path aliases while generated build files or the Bison installation reference them. Do not remove source caches, prior failures or signed outputs required by the next stage.

## Impact on Next Stage

Stage 3 can use the verified source/tool inputs, real loader authorization, 4 KiB code-signature requirement and controlled runner. It must create fresh build/sign/run outputs, execute self-owned ARM64 Windows PE/API fixtures, and implement and verify the actual Wine guest/host x18 transitions and nested callbacks. Changed code invalidates earlier binary-bound runtime evidence; repeat the affected native bootstrap checks on those new bytes.

The dedicated local Wine profile can be reused only while all actual validation checks continue to pass. Do not transfer these results to a different executable, copy the host probe's grant assumptions, or use native initialization as PE/API acceptance. FEX/DXMT and Steam/game work remain separate. Issue #4 remains open; no PR is published at this stage boundary.

## Approval Request

Approve these Stage 2 artifacts and results to enter **Stage 3 — PE/API execution and x18 callbacks** under the existing implementation plan.
