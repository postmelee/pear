# Wine host development

Status: experimental component work under [Issue #4](https://github.com/postmelee/pear/issues/4). The [Stage 1 input/toolchain checks](../../mydocs/working/task_m1_4_stage1.md) and [Stage 2 native bootstrap](../../mydocs/working/task_m1_4_stage2.md) passed on the recorded host. The [Stage 3 original ARM64 Windows API/ABI fixtures](../../mydocs/working/task_m1_4_stage3.md) and [Stage 4 finite thread, memory and exception checks](../../mydocs/working/task_m1_4_stage4.md) also passed. The [Stage 5 finite Win32/Cocoa callback and teardown checks](../../mydocs/working/task_m1_4_stage5.md) passed on the same development host. Historical Stage 2 stopped before PE entry; general Windows application support, Rosetta-free Megabonk and an end-user release remain development goals.

The [Stage 6 fresh reconstruction evidence](../../mydocs/working/task_m1_4_stage6_observations.json) passed on October 1, 2026. Two native ARM64 builds and one compile-only ARM64EC companion were rebuilt from the current 23-patch series, with 44 successful commands each. Independent replay verified the source/tool/build/signing records, the separate six-case native prerequisite, all three bootstrap controls and the normal API/ABI/thread/20-window suite on one newly signed native candidate. Complete unsigned-install comparison covered 2,729 files: 1,959 exact and 770 explained metadata differences, with no unexplained difference.

The lifetime correction preserves the original startup publication point while giving caller and callback independent ownership; no launch-readiness handshake was added. Prior failures, diagnostic-only successes and their limitations remain in the [diagnostic history](../../mydocs/plans/task_m1_4_impl.md#stage-6-retained-reconstruction-and-runtime-diagnostics) and [Stage 6 report](../../mydocs/working/task_m1_4_stage6.md). These finite passes do not isolate the cause of historical AppKit failures or establish general startup reliability. Reconstruction used fresh directories on the same development Mac and a reverified compiler cache. FEX/x64 execution, graphics pairing, Steam, Megabonk and ordinary-user distribution remain unqualified.

## Scope and inputs

The [architecture](../architecture.md) defines the runtime goal. This component starts from Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892`. The [original source audit](../source-qualification.md) remains complete with a **blocked** combined Wine/FEX/DXMT decision. Its bytes and historical evidence are preserved.

| Record | Role | Boundary |
|---|---|---|
| [Inputs](../../runtime/wine/inputs.json) | Selected Wine source, exact audit reference, dependencies and unresolved ports | Component input facts; no full-runtime approval |
| [Toolchain](../../runtime/wine/toolchain.json) | Exact public tool artifacts and external native tool/SDK identities | Build inputs; no game runtime or independently rebuilt compiler claim |
| [Build configuration](../../runtime/wine/build-config.json) | Native/PE variants, framework and feature decisions | Explicit fixture configuration, not a Steam/game configuration |
| [Patch series](../../runtime/wine/patches/series.json) | Ordered attributable Wine changes | Stage 2 bootstrap, Stage 3 PE/API/ABI, Stage 4 finite thread/memory/exception and Stage 5 finite Win32/Cocoa scope verified; required Darwin ports are not complete |

The native host target is ARM64 macOS. `arm64` selects aarch64 PE components; `arm64ec-build` selects aarch64 plus ARM64EC components with an auxiliary x86_64 PE compiler. The latter is a build candidate, not evidence of FEX or x64 execution. Compiler-only x64/i386 fixtures are never executed in Stage 1.

The bounded fixture configuration retains the Mac driver, pthreads, CoreText and required SDK frameworks. It explicitly excludes optional networking/authentication, codecs, audio, Vulkan, X11/Wayland and external font backends. Wine's built-font generation is also disabled by that selection. No font-rendering result follows from CoreText linkage. The SDK matrix includes the default native modules' CoreFoundation, CoreServices, DiskArbitration, SystemConfiguration and ApplicationServices dependencies as well as the Mac-driver frameworks. Changing those settings requires new dependency and execution evidence before a later Steam/game configuration can be qualified.

## Tool provenance and permissions

The selected cross-tool archive is the publisher's [LLVM-MinGW 20260908 macOS universal release](https://github.com/mstorsjo/llvm-mingw/releases/tag/20260908), with downloaded-byte SHA-256 `d1dc5d1ecf3a3ced5ed5544c72f1acd0c8e84eb3024d520ecc6b143eec62a149`. The release is attributable to the pinned LLVM-MinGW source and publisher workflow recorded in the lock. This is not an independent reproduction of that binary. Its universal tools must contain and actually select an ARM64 host slice; Windows PE machine types are checked separately.

[Bison 3.8.2 source](https://lists.gnu.org/archive/html/bug-bison/2021-09/msg00056.html), SHA-256 `9bba0214ccf7f1079c5d59210045227bcf619519840ebfa80cd3849cff5a5bf2`, supplies the parser generator required by Wine. The system Bison 2.3 does not meet Wine's >=3.0 requirement. Bison is installed only into the owned task tool directory. Apple Xcode/SDK and recorded native tools remain external prerequisites; their recorded identities describe the tested host rather than a universal end-user requirement.

Preserve the archives' actual LLVM/MinGW and Bison notices, including applicable generated-output exceptions. Wine retains its LGPL-2.1-or-later terms. These component records are an engineering inventory, not a new Pear license or blanket redistribution clearance. No commercial Wine binary is a dependency.

Stage 1 executes only ordinary native build tools and a self-owned native compiler fixture. It does not execute PE fixtures, Wine loader/server processes or restricted capability trials. Later Wine execution must independently validate its real bundle/executable authorization; the [host probe's](../host-capabilities.md) development profile and results do not automatically transfer. Keep normal macOS protections enabled.

## Reproduce the Stage 1 checks

Run from the Pear task checkout after reviewing its pinned records and scripts. Use a new owned output directory; preserve earlier evidence. The stage report records the completed commands, 34 actual checks, 58 successful commands and 95 unit tests.

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

Before the preparation commands, acquire the two public archives at the lock's `download_path` locations. Preparation is offline and does not download missing archives. From a fresh task checkout, the following uses the reviewed lock, refuses occupied files, and verifies both size and digest before any extraction or execution:

```sh
python3 - <<'PYTHON'
import hashlib
import json
from pathlib import Path
import urllib.request

lock = json.loads(Path("runtime/wine/toolchain.json").read_text())
for artifact in lock["artifacts"]:
    destination = Path(artifact["download_path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with destination.open("xb") as output:
        with urllib.request.urlopen(artifact["url"], timeout=60) as response:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > artifact["size_bytes"]:
                    raise ValueError("Archive exceeds the locked size")
                digest.update(chunk)
                output.write(chunk)
    if size != artifact["size_bytes"] or digest.hexdigest() != artifact["sha256"]:
        raise ValueError("Archive identity does not match the reviewed lock")
PYTHON
```

Keep any failed or partial download for diagnosis and choose a fresh destination through a reviewed lock change; do not execute it or replace the expected digest with its observed digest. These commands use the exact Xcode/SDK/tool identities in the lock. A different host/tool version needs its own reviewed lock and verification results; copying the original hashes does not qualify it.

The source cache can be acquired using the original [source qualification procedure](../source-qualification.md#reproduce-the-source-inputs). Preparation verifies the selected original objects and materializes a separate source tree; it does not mutate the audit cache. Input paths and output identities must match the actual run.

Tool preparation checks archive hashes, member paths/links and expansion size before use. Plan disk space for the tools, source and retained outputs; do not delete unrelated data to make a build fit. Do not invoke LLVM-MinGW's release script or unreviewed build-all script: those have output/deletion/universal-build assumptions outside this procedure. Wine's internal shell/make path handling must also be tested; outer argument quoting is not sufficient for a checkout containing spaces. The helper creates owned `/private/tmp/pear-task4-*/workspace` symlinks pointing back to the corresponding task output. It verifies the targets before using these paths without spaces. Keep those aliases while their Bison installation or generated build files are in use: configured paths can refer to them. They are local setup state, never release contents. Clean up only the exact owned aliases when their dependent outputs are retired.

The compiler checks cover native C and SDK framework linkage; PE compilation/linking, actual imports/exports/resources, C++17, and ARM64/ARM64EC/x64 unwind metadata. ARM64EC linkage uses the locked LLVM-MinGW archive's real ARM64EC members in `aarch64-w64-mingw32/lib/libmingwex.a`; the tests require nonzero CHPE metadata pointers in both linked images. No substitute dispatcher or invented runtime metadata is supplied. These link observations do not validate guest startup or dispatch execution. The resource test checks both ID 101 and the complete six-byte payload. The i386 assembler check does not claim x64-style SEH. Wine configure and its native build helpers may run to validate the selected inputs and generated make paths, but no Wine runtime target or PE guest is executed.

## Stage 2 native build and authorization

Stage 2 passed for the recorded development configuration. Both variants built; the native variant completed actual Wine bootstrap, an intentional timeout and a wrong-prefix refusal with owned cleanup. Its scripts and diagnostic hooks remain experimental. Build completion, authorization and execution are separate gates; the ARM64EC companion has not been executed.

`build.py` rechecks the prepared source and tools, copies the source into a fresh owned directory, applies the ordered patches with exact before/after identities, and performs configure, make and local installation. It does not launch Wine. Native Mach-O outputs must contain only ARM64. PE machine types and module paths are assessed separately; a PE file's existence does not establish execution support. Both variants retain the same source, patch and tool inputs. Keep the complete logs and failed attempts.

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-arm64 --jobs 4
python3 tools/wine/build.py --variant arm64ec-build --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-arm64ec --jobs 4
python3 tools/wine/modules.py --build .build/task4/build-arm64 --output .build/task4/build-arm64/modules.json
python3 tools/wine/modules.py --build .build/task4/build-arm64ec --output .build/task4/build-arm64ec/modules.json
python3 tools/wine/verify.py build --root .build/task4/build-arm64 --companion .build/task4/build-arm64ec --require-complete
python3 tools/wine/signing.py inspect --build .build/task4/build-arm64 --output .build/task4/signing-requirements.json
```

The module inventory inspects seven selected PE modules' headers, imports, delay imports, exports and hybrid metadata with the pinned LLVM reader. This is a finite binary-structure inventory, not proof of a resolved Windows API/runtime dependency closure. Upstream WinMD metadata containers are classified separately from executable PE modules. The companion places ARM64X hybrid modules under `aarch64-windows`; there is no required separate `arm64ec-windows/ntdll.dll`. Its three EC-only outputs have AMD64 PE headers but verified CHPE code ranges. These are Windows binary-format observations, not Intel macOS processes or translated-execution evidence.

Use new output names when the example destinations already exist. Do not run both large builds concurrently. The requirements inspection maps the actual built loader, server, libraries and ordinary helpers before requesting a profile. It does not sign or execute them.

The verified development bundle identifier is `io.github.postmelee.pear.wine-loader`. Create a dedicated explicit macOS App ID with **Cross-architecture Compatibility Framework** enabled, then a [Mac App Development provisioning profile](https://developer.apple.com/help/account/provisioning-profiles/create-a-development-provisioning-profile) for the current device and an available Apple Development identity. An existing host-probe profile is not automatically valid for this loader. The checks require an unexpired, matching, device-bound profile, an available certificate, and the actual restricted grant. Keep the profile, private key and identifiers out of Git.

The local signing input is an ignored file such as `.build/task4/private/signing.json`:

```json
{
  "schema_version": 1,
  "record_kind": "wine_local_signing",
  "scope": "wine_component",
  "profile_path": "/absolute/local/path/to/wine-loader.provisionprofile",
  "bundle_identifier": "io.github.postmelee.pear.wine-loader"
}
```

After the actual profile checks pass, `signing.py prepare` copies the installation into a development bundle, signs its native images from the inside out, and verifies the effective signatures and original code/data identities. Only the actual Wine loader receives the cross-architecture claim. The ordinary server and bootstrap/sentinel helpers receive no restricted claims. Hardened Runtime and library validation remain enabled; Stage 2 does not request JIT access. The `bin/wine` wrapper is not an authorized Stage 2 entrypoint.

The restricted loader requires **4 KiB code-signature pages**, explicitly selected by the final app signing command with `codesign --pagesize 4096`. On the recorded host, default development signing produced 16 KiB signature pages for the 4 KiB-segmented Wine loader: strict disk verification passed, but the kernel rejected its initial image before Wine entry. Keeping the same code and effective grants and re-signing with 4 KiB pages passed all three bootstrap cases. The signer checks the actual reported page size; it does not infer it from the requested flag. Code-signature page granularity, user-visible VM pages and kernel VM pages are separate observations.

```sh
python3 tools/wine/signing.py prepare --build .build/task4/build-arm64 --local-input .build/task4/private/signing.json --output .build/task4/signed --require-empty
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed --output .build/task4/runs-stage2 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage2 --suite bootstrap --require-complete
```

The diagnostic uses the actual Wine loader and server handshake, then stops before PE startup and guest x18 initialization. The measured loader uses 4 KiB user pages over 16 KiB kernel pages, with a 64 KiB unreadable null guard and Wine's read-only 4 KiB shared-data mapping. Ordinary server/helpers retain native page geometry. It measures native process/page/module facts. A native result does not qualify a Windows API, translator, renderer or game. The runner creates fresh synthetic prefixes, bounds output and execution time, checks process identity before signaling, retains failures, and tests an unrelated sentinel's survival. Unknown observations cannot pass.

The development bundle preserves Wine's runtime directory layout under `Contents/Resources/runtime` so its native path discovery remains testable. This is an experimental local packaging choice, **not a qualified distribution layout**. Apple provides separate guidance for [bundle content placement](https://developer.apple.com/documentation/bundleresources/placing-content-in-a-bundle) and [nonstandard code structures](https://developer.apple.com/documentation/xcode/embedding-nonstandard-code-structures-in-a-bundle). Distribution, notarization and the user-facing launcher remain later work.

## Stage 3 PE/API and x18 boundary checks

Current gate (September 30, 2026): [Stage 3 passed](../../mydocs/working/task_m1_4_stage3.md) for the recorded development configuration. Original ARM64 Windows API/ABI fixtures, two actual PE placements and SecurityCookie initialization passed independent verification; all three bootstrap controls passed on the same final signed native Wine artifact. The standalone native prerequisite separately passed 4 KiB code/data separation, rollback, exhaustion, retirement/reuse and four matched protection-fault controls. These prototype results do not claim integrated Wine fault injection or exhaustion. Earlier failures and partial successes remain preserved in the [implementation plan](../../mydocs/plans/task_m1_4_impl.md). The commands below are the verification procedure; game support remains unqualified.

Stage 3 adds self-owned ARM64 Windows programs and explicit Darwin x18 transitions to the actual Wine syscall, Unix-call, callback and initial-thread paths. The original Wine implementation languages are retained. The fixture suite is experimental; game and ordinary-user support require later evidence.

The API fixture checks Unicode and space arguments, a fixed environment value, allocation/TLS, an owned file's write/read/hash and deletion, a missing-file error, and a real `CreateProcessW` child returning 37. It also queries the actual `SystemSupportedProcessorArchitectures` class 181 result used by Wineboot, requiring the native ARM64 entry, expected flags and a complete terminating entry. Class 181 filters AMD64 on ARM64 in this upstream source; this check does not independently cover every architecture-query API. The ABI fixture uses Wine's exported Unix dispatcher and its actual `KeUserModeCallback`/`NtCallbackReturn` machinery. Its declared results are 64 round trips, 32 nested callbacks, 16 injected error returns and 128 gateway/native calls, with real TEB/x18, stack-frame and preserved-register checks. Calling `NtCallbackReturn` without an active callback must return `STATUS_NO_CALLBACK_ACTIVE`.

Two concurrently loaded, byte-identical owned DLL copies must occupy different nonpreferred bases. The host binds their original export RVAs and DIR64 entries to actual indirect code/data access, four probe observations and two retirements. A real PE load-config pointer exercises Wine's SecurityCookie initialization in both copies: nonzero, nondefault, below-48-bit values must remain stable across four observations. Public records omit cookie values and addresses. Two actual named/ordinal import failures and 32 callback-held unload/reload rounds also pass. The stable single-thread callback table and already pinned main-executable continuation limit this lifetime evidence; it does not establish arbitrary concurrent unloading.

The selected native publisher owns one bounded `MAP_JIT` allocation with fixed code/data classes and 4 KiB page W^X. Relocations and loader-data validation precede immutable-code publication. The final loader receives public `allow-jit` in addition to its verified cross-architecture grant; ordinary helpers receive no restricted claims. The native baseline also passed without the added claim, so its empirical necessity is not established. Dynamic generated code, mixed writable/executable images and incompatible reuse remain outside this verified path. Hardened Runtime and library validation stay enabled.

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage3 --jobs 4
python3 tools/wine/abi_review.py --build .build/task4/build-stage3 --output .build/task4/build-stage3/abi-review.json
python3 tools/wine/signing.py prepare --build .build/task4/build-stage3 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage3 --require-empty
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed-stage3 --output .build/task4/runs-stage3-bootstrap --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage3-bootstrap --suite bootstrap --require-complete
python3 tools/wine/run_fixtures.py --suite api-abi --runtime .build/task4/signed-stage3 --output .build/task4/runs-stage3 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage3 --suite api-abi --require-complete
```

Before interpreting the two-placement results, also inspect the actual built DLL with the pinned ARM64 reader and the finite fixture checker. This step is separate from the automatic exporter:

```sh
python3 -B - <<'PYTHON'
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, 'tests/wine')
from test_relocation_fixture import inspect_relocation_indirection
sys.path.insert(0, 'tools/wine')
from api_runner import relocation_image
root = Path('.build/task4/build-stage3')
dll = root / 'install/libexec/pear-stage3/lifetime-arm64.dll'
reader = Path('.build/task4/tools/llvm-mingw/bin/llvm-objdump')
result = subprocess.run(['/usr/bin/arch', '-arm64', str(reader),
    '--disassemble-symbols=PearRelocationAccess,PearRelocationProbe', str(dll)],
    text=True, capture_output=True, check=True, timeout=30)
print(inspect_relocation_indirection(dll.read_bytes(), result.stdout))
print(relocation_image(dll.read_bytes()))
PYTHON
```

Retain the final build, DLL, reader, checker and disassembly hashes locally, as in the [Stage 3 report](../../mydocs/working/task_m1_4_stage3.md). The checker proves only its declared original-fixture instruction/operand patterns. Actual Wine execution must independently bind runtime addresses, initialized cookies, file identities and retirement generations. Use fresh output names for every run; the report records the actual `attempt12` substitution and the complete `evidence.py --stage 3` export command. Export requires API/ABI and bootstrap on identical signed bytes plus all three retained native prerequisite attempts. This report export packages historical receipts, including two fixed failed source revisions; the commands above alone do not recreate those retained local inputs. The Stage 6 coordinator below reconstructs the current selected page-W^X prerequisite separately, with current source and actual profile/bundle/signature bindings. It preserves all three historical receipts and does not rerun the obsolete failed policies. Copied historical hashes do not qualify a new run.

The assembly review binds the final native `ntdll.so` bytes and symbol table to reproduced output from the pinned LLVM disassembler. It checks six declared entry contracts and two mode helpers, including spills and the pre-resolved getter/setter targets. It does not prove arbitrary Wine control flow, signal-context restoration, unwind behavior or runtime execution. A minimal signal gateway enters host mode before invoking the existing Wine handlers. The separate Stage 4 checks below exercise declared thread, fault and exception paths; general signal and unwind behavior remains unqualified.

Real prefix initialization and Windows child creation are retained. An opt-in diagnostic protocol registers Wine-created native descendants before continuation, checks live peer/process identity, supplies a separate event pipe and keeps those descendants in the root process group for bounded cleanup. Native external execution is refused. The root remains unreaped until its owned group has been cleaned up. There is an acknowledged native interval between fork and registration. This instrumented fixture containment is not a general-purpose game process supervisor. Loaded-image snapshots also do not establish an exhaustive load/unload timeline.

The fixed `native-api-abi-no-mono-v1` fixture policy applies Wine's documented `mscoree=` override only to the owned API/ABI loader and its descendants. It disables CLR loading and registration in those disposable native-test prefixes, avoiding an optional Mono installer wait. Genuine Wineboot and INF prefix creation remain required. The case and run records bind the exact policy and passed loader environment; bootstrap settings and future game configuration do not inherit it. CLR and Mono support are untested.

Each API/ABI case receives a fresh synthetic home, prefix, working directory and nonce. The 180-second case deadline includes real prefix initialization; cleanup has separate bounded grace, termination, kill and drain intervals. Output, process and event counts are bounded. Early descendant crashes, missing observations, wrong page geometry, unexpected native images, lost sentinels and incomplete cleanup fail the gate. Keep actual failures and choose new output names for retries.

The build also produces x64 and i386 PE controls, whose actual headers and hashes are verified. The runner rejects both targets before execution because no translator is qualified. This does not test a translator's behavior. The Stage 2 ARM64EC companion remains historical build evidence; it has not been rebuilt or executed with these Stage 3 patches. Stage 6 must reconcile final companion and native inputs.

The pinned Wine loader selects `xtajit64.dll` for ARM64EC/x64 translation, with an `HKLM\Software\Microsoft\Wow64\amd64` override. Its i386-on-ARM64 WOW64 route selects `xtajit.dll`. Neither translator is installed in this native build. The selected source's `xtajit64` implementation terminates its unimplemented emulation entry points; its presence in an ARM64EC companion would not qualify FEX execution. Issue #5 must integrate and verify the actual emulator contract.

## Stage 4 thread, exception and memory checks

The [Stage 4 report](../../mydocs/working/task_m1_4_stage4.md) records passing same-host checks on September 30, 2026. Stage 4 adds a finite `threads-memory-exceptions` suite. Its acceptance requires the existing API/ABI cases, the new combined fixture and all three bootstrap controls on identical signed bytes. The first execution attempts and their parser corrections remain in the [implementation plan](../../mydocs/plans/task_m1_4_impl.md#stage-4-retained-diagnostic-history-2026-09-30); a diagnostic or a fixture's own success flag cannot substitute for the complete independent gate.

The original C/ARM64 fixtures reuse Wine's actual thread startup, TLS/TEB initialization, vectored exception dispatch, signal handlers, context capture, suspend/resume and virtual-memory APIs. Two Wine-created workers exercise distinct TEB/TLS values, initialization, two injected error returns, Windows thread-handle waits, native exit-entry observations and handle cleanup. The native half independently observes the Wine thread ID; the private signal target is a retained `pthread_t`. The protocol's `native_tid` field is not a Darwin kernel thread ID.

Two explicit SIGUSR1 deliveries target labeled guest and native instruction windows. A third observation belongs to a handshake-controlled suspend/resume operation. Captured PC, SP, x18 and x19, handler host mode and return mode must agree with independently recorded native observations. `GetThreadContext` explicitly requests the ARM64 x18 flag in addition to full context. Thirty-four native record parts bind startup, three signal observations and exit to the worker identities and actual signed PE/native instruction ranges. Formatting occurs outside signal handlers, and each native pipe record is bounded below the host's 512-byte atomic-write limit.

Two ordered vectored handlers observe a software exception, three recovered access faults, a guard fault followed by a successful retry, and a separate child's terminating access fault. Hardware faults bind the access kind, owned address, exact labeled instruction and recovery PC to the signed fixture. The terminating child deliberately calls `TerminateProcess` after both handlers observe the matching fault. Its Windows status is `0xc0000005`, its signed native status is `-1073741819`, and its process exit byte is `5`. This is a controlled fault-derived termination; default unhandled-exception policy and general unwinding remain untested.

An owned three-page region tests ordinary 4 KiB reserve/commit/protect/decommit/recommit behavior, neighboring sentinels, zeroed recommit and guard semantics. Dynamic code uses eight separate 64 KiB slots in the same single `MAP_JIT` allocation as the immutable PE arena. It does not reuse immutable PE slots or create a second JIT mapping. The fixture explicitly reserves executable intent, commits RW, publishes RX with `VirtualProtect` and `FlushInstructionCache`, executes a return value of 42, rewrites while RW, republishes RX and executes 84. It also tests decommit, zeroed recommit, release and compatible reuse. The protocol rejects RWX, dynamic guards, fixed-address reservations and ordinary anonymous RW-to-RX promotion. This fixed original ARM64 code does not qualify translated guest code or a general FEX JIT service.

Fixture cleanup first allows bounded natural client completion, then uses SIGTERM/SIGKILL only for the retained owned loader group while the server remains alive. Server shutdown follows observed client completion. Sending loader SIGINT would invoke Wine's Windows CtrlRoutine path; signaling the server too early can instead terminate its remaining clients with status 1. Unexpected nonzero exits remain failures. Forced disposal of these synthetic prefixes is not evidence of graceful game shutdown.

Native dynamic events use their own sequence and allocation generations. The reader requires the actual loader handoff, arena reservation, dynamic budget and PE publication order. Private Stage 4 stdout uses a strict 3,072-byte flat-record decoder for unsigned 64-bit register and code-hash fields; shared manifest/helper/native-event JSON limits remain unchanged. Missing, duplicated, reordered or malformed observations fail verification. Public export selects finite counts, identities expressed as hashes and declared limitations, omitting private addresses, process/account identifiers, paths, profile contents and raw diagnostics.

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage4 --jobs 4
python3 tools/wine/abi_review.py --build .build/task4/build-stage4 --output .build/task4/build-stage4/abi-review.json
python3 tools/wine/signing.py prepare --build .build/task4/build-stage4 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage4 --require-empty
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed-stage4 --output .build/task4/runs-stage4-bootstrap --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage4-bootstrap --suite bootstrap --require-complete
python3 tools/wine/run_fixtures.py --suite threads-memory-exceptions --runtime .build/task4/signed-stage4 --output .build/task4/runs-stage4 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage4 --suite threads-memory-exceptions --require-complete
python3 tools/wine/stage4_evidence.py --build .build/task4/build-stage4 --runs .build/task4/runs-stage4 --bootstrap-runs .build/task4/runs-stage4-bootstrap --output mydocs/working/task_m1_4_stage4_observations.json
```

Use fresh output names for retries. The passing report uses `runs-stage4-attempt4` and `runs-stage4-bootstrap-attempt2`; the earlier runs remain retained failures or historical evidence. Substitute those actual roots when inspecting the retained results. The exporter independently checks the complete suites, exact build/signed identities, actual assembly review and current producer hashes. It refuses diagnostic-only runs. These are same-host development checks with the existing loader authorization and protections. A native Windows reference, arbitrary asynchronous suspension, native-created callback threads, concurrent code mutation, x64 translation, games and ordinary-user distribution are outside this finite scope.

## Stage 5 Mac-driver protocol

The [Stage 5 report](../../mydocs/working/task_m1_4_stage5.md) records the passing final commands and exact retained output names. Use new empty output directories for another run; the public exporter rejects diagnostic-only or mixed-runtime evidence.

The `mac-driver` suite requires the existing API, ABI and thread/memory/exception cases plus an original ARM64 window fixture. All four cases and the separate three bootstrap controls must pass on identical signed bytes. The observer reuses Wine's real C/Objective-C driver and existing PE/native callback gateways. Its diagnostic patch is enabled only for the owned window case; it does not assert a newly discovered production driver defect.

The guest loads the actual `winemac.drv` PE module and calls its fixture export through a separate native Unix-call entry. Native initialization binds the real `winemac.so` image, Windows thread/TEB, Darwin thread and loaded AppKit/CoreFoundation images. Each of twenty sequential tool-window lifetimes follows this path:

1. Create a Win32 window and observe the corresponding Cocoa window on AppKit's main thread.
2. Invoke that Cocoa window's `performClose:` through Wine's main-thread request queue. Its ordinary close delegate places `WINDOW_CLOSE_REQUESTED` in the actual `WineEventQueue`.
3. At dispatch of that exact owned event, deliver the deterministic application message through `NtUserMessageCall` and Wine's normal guest callback gateway. The guest WNDPROC changes the title, re-enters native code and returns the expected token.
4. Continue the original close-event handler through `SC_CLOSE`, `WM_CLOSE` and `DestroyWindow`. Observe Cocoa close and queue discard.
5. Post a tagged, windowless AppKit application-defined event using the upstream query-wakeup pattern, and observe its consumption after normal superclass dispatch. If the window remains alive, post another only after the preceding turn is consumed, with at most one in flight and 100 turns within the existing drain bound. The first turn is mandatory even after early deallocation; further posting stops once deallocation is observed. Bind each turn to its cycle and contiguous ordinal. Require actual post-super object deallocation, every posted turn to be consumed, and a subsequent main-thread barrier, no active Wine event frame, the matching owner queue, its directly observed empty array and an empty signaling FD before starting the next lifetime. The readiness result from `macdrv_ProcessEvents(QS_ALLINPUT)` alone is insufficient when a nested event frame suppresses dispatch. Independently repeat the queue checks at finalization.

The guest and native observations must agree; guest stdout alone cannot pass the gate. Image hashes, actual exported entry points and executable sections, immutable PE publications, thread ownership, native x18 host mode, per-lifetime identities, callback results and teardown order are bound independently. Reused object addresses do not merge different lifetimes. Both PE images must be published before observer initialization and remain live through the final barrier. The tagged event advances the fixture run loop; it is not a keyboard/mouse event and does not target a window. Native records distinguish posting, consumption and the subsequent barrier. This is an instrumented fixture scheduling requirement, not a claim that an AppKit event strongly owns a closed window or that production Wine leaks it. The observer adds no persistent retain to a Cocoa window or event queue. Wine's per-thread queue and explicit driver-module reference intentionally last for the process.

The native observation count is bounded by the lifecycle protocol: `527 + 4 * barriers + 4 * event_turns` atomic record parts, at most 16,527 parts. Only the trusted window-loader case receives a 12 MiB event limit and a 32 MiB/2,000,000-node saved-case JSON limit. Other processes retain their 2 MiB event limits; other cases retain 16 MiB/1,000,000-node limits. The shared 32 MiB event budget, per-line bounds and timeout/cleanup checks remain in force. Exceeding any bound fails verification; a saved record cannot select its own larger allowance.

The finite no-late-callback observation ends at the final main-thread barrier and event drain. Normal process exit is verified separately; this is not observation of every possible event after that barrier. Local close/teardown loops check five-second deadlines and at most 100 drain attempts, while the separate 180-second host deadline also bounds blocked native calls through owned-process cleanup. The 320-by-180 windows use no-activation styles but can briefly overlap desktop content; do not interact with them during verification. No keyboard/mouse injection, display-mode change or screenshot is required.

The accepted local graphical runs observed the main display awake, active and online before, during and after execution. A graphical session alone was insufficient in retained controls; asleep/inactive or headless behavior remains unqualified. A finite, owned `/usr/bin/caffeinate -d -u -t 7200` assertion maintained the tested condition without changing persistent power settings. The local wrapper recorded five-second CoreGraphics samples and terminated/reaped the assertion on completion. Independently review those private context records: the reconstruction exporter does not validate them. Samples are finite observations, not a guarantee of continuous state between samples, and this assertion is unsuitable for a power benchmark.

## Native driver interface handoff to #7

This is a dated source/compile inspection of Wine base `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` with the recorded Pear patches and DXMT `7c8dee1c2d73415301ceb7d1fa810861cef4cd67`, reviewed September 30, 2026. It is not renderer execution or a stable public Wine API.

Wine's `dlls/winemac.drv/macdrv.h` defines `struct macdrv_win_data` as `hwnd`, `cocoa_window`, `client_view`, then `rects`, at native ARM64 offsets 0, 8, 16 and 24. DXMT's `src/winemetal/unix/winemetal_unix.c` copies four pointer fields and reads `client_cocoa_view` at offset 24. That reads this Wine version's rectangle bytes as a pointer. The selected Wine source does not provide DXMT's `macdrv_functions` table, and the retained Stage 4 native driver does not publicly export the requested accessors/view functions. Recheck exports on the actual future paired artifact; adding exports alone cannot repair the structure mismatch.

Relevant selected Wine declarations use the native Darwin C ABI:

| Declaration | Contract |
|---|---|
| `struct macdrv_win_data *get_win_data(HWND)` | Returns data with the driver mutex held; invalid HWND returns null without a held lock |
| `void release_win_data(struct macdrv_win_data *)` | Unlocks only; does not retain or release Cocoa objects |
| `WineWindow *macdrv_get_cocoa_window(HWND, bool require_on_screen)` | Returns a borrowed pointer after unlocking |
| `WineContentView *macdrv_create_view(CGRect)` / `void macdrv_dispose_view(WineContentView *)` | Creates/disposes the client view through Wine's main-thread queue |
| `MTLDevice_id macdrv_create_metal_device(void)` | Native device type is `id<MTLDevice>` in Objective-C, opaque in C |
| `WineMetalView *macdrv_view_create_metal_view(WineContentView *, MTLDevice_id)` | Can return a cached view without an extra retain on repeated acquisition |
| `CAMetalLayer *macdrv_view_get_metal_layer(WineMetalView *)` | Returns a borrowed layer |
| `void macdrv_view_release_metal_view(WineMetalView *)` | Removes and releases the view on the main thread |
| `void OnMainThread(dispatch_block_t)` | Uses Wine's request queue; waiting can process query events and re-enter code |

The selected native `bool` is one byte; Win32 `WINBOOL` is four. DXMT's particular native table spells the parameter `BOOL`, but that translation unit is compiled as Objective-C and imports Cocoa. The selected Apple ARM64 compile check confirms its Cocoa `BOOL` is type-compatible with one-byte `bool`. That spelling alone is not a demonstrated ABI mismatch. A PE `LRESULT (CALLBACK *)(HWND, UINT, WPARAM, LPARAM)` remains a different execution boundary and must use Wine's established callback and x18 transitions.

The renderer client surface owns `client_view`, assigns it during presentation and clears it during detach. A plain window may have no such view. Copying the pointer after unlocking is not a lifetime guarantee. DXMT's current private-structure path also lacks a null check after `get_win_data`; missing exports can yield null outputs with a success status. #7 must define explicit error behavior and test missing/destroyed HWND, absent view, repeated acquisition, resize/detach/destroy races and balanced release on the actual selected pair.

Reuse Wine's C/Objective-C implementation and scheduling. A typed, versioned opaque adapter or source-matched bridge must establish these contracts before renderer integration; a copied private structure or new language does not establish them. The signatures and view ownership above come from source inspection, not Metal execution. A passing window/event fixture does not qualify DXMT, D3D, FEX, game graphics or distribution.

## Fresh reconstruction of the final fixture configuration

The Stage 6 coordinator reconstructs both Wine variants in empty owned directories from the original pinned source cache and the final ordered patch series. It reuses the verified local compiler/tool cache; it does not independently rebuild the publisher's compiler, copy an earlier Wine installation into a new build, or establish a second-machine result. Use the pinned input acquisition and actual loader authorization procedures above first.

The coordinator creates two separate native ARM64 builds for unsigned comparison, then a companion build. All three invoke `/bin/sh ../source/configure` from their own `objects` directory and record `source_argument_policy: stable_relative_v1`. Stable relative source arguments prevent temporary absolute paths from changing Clang's anonymous-namespace names. An absent policy in historical records means legacy absolute invocation; an unknown or mismatched policy is rejected. Sources, patches, compiler options and feature settings retain their recorded identities. The fresh native reference is compiled and inspected only; the candidate is the sole signed and executed Wine build. The companion is also compile/inspect-only.

The retained Stage 5 native build and public evidence remain historical context. The local experiment expects their original record identities and preserves their bytes, but does not claim byte or semantic equivalence to that older absolute-path configuration. An earlier complete-install diagnostic found path-dependent symbol names alongside real ICU code/data/relocation changes; those differences remain rejected by the strict comparator. Their complete causal or semantic equivalence is not established. They are not discarded as metadata. A public historical report cannot replace retained local evidence, and adapting these exact historical bindings elsewhere needs review.

```sh
(
  umask 022
  python3 tools/wine/reproduce.py --inputs runtime/wine/inputs.json --toolchain runtime/wine/toolchain.json --config runtime/wine/build-config.json --source-cache .build/task1-sources/inputs --tools .build/task4/tools --local-signing .build/task4/private/signing.json --output .build/task4/reproduction --require-empty
)
python3 tools/wine/verify.py reproduction --root .build/task4/reproduction --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Use child umask 022 for source derivation: patch-created files must retain the declared 0644 modes. A private launch wrapper may keep its own records restrictive while explicitly selecting this mask for the coordinator child. Retained `reproduction2` failed before configure when an inherited 077 mask produced twelve 0600 files; the content gate was not relaxed.

For that output, fresh source, native reference, native candidate and companion directories are the siblings `reproduction-inputs`, `reproduction-anchor6`, `reproduction-native6` and `reproduction-companion6`. The source sibling preserves the materializer's immediate-child ownership restriction. Tool checks, the standalone native prerequisite, Wine signing, suites and reconstruction receipts remain inside `reproduction`. Existing destinations are refused. Failed outputs are retained; a retry needs a new reviewed empty layout rather than overwriting or resuming an incomplete record.

The accepted local final run used `.build/task4/reproduction3` and `.build/task4/tools-stage6-mtime`, with child umask 022 and the observed awake-display context above. Its independent verifier emitted the allowlisted public observations; the reviewed output was preserved byte-for-byte without rerunning the same validation solely for export. The earlier `reproduction` and `reproduction2` outputs remain failed historical attempts.

The coordinator requires at least 26 GiB of free space and runs all three large builds and native suites serially. The estimate includes retained-reference and fresh-output headroom but is not a guarantee against unrelated disk growth. Before the Wine builds, it recompiles the current standalone page-W^X prerequisite and runs its two positive and four fault-control cases in `native-arena`; the wrapper independently validates current inputs, actual profile and bundle bytes, signatures, raw lifecycle/fault observations and cleanup. This prerequisite is a separate native fixture, not a test of the final Wine binary. The final Wine runtime's cumulative `mac-driver` suite contains API, ABI, thread/memory/exception and window cases; the separate bootstrap suite adds its normal, timeout and wrong-prefix controls. Every Wine case must bind to the same freshly signed Wine artifact. Neither the companion nor the x64/i386 refusal controls become executable by passing a build gate. The companion's ARM64X outer images exceed the current native publication arena's intended scope; their measured requirements are reported separately, without weakening or enlarging the native runtime gate.

Here, unsigned comparison means before Pear development signing; compiler/linker-generated ad-hoc Mach-O signatures may already exist and are checked as part of those bytes. The comparison retains raw file hashes, permissions, symlinks and every difference. Only differences explained by checked binary-format metadata or recorded build paths may pass; arbitrary changed code cannot be discarded as nondeterminism. Development signing creates a separate identity and is revalidated from actual authorization. A completed coordinator ledger is insufficient by itself: the independent verifier rechecks sources, tools, build outputs, signatures, suites and comparison evidence. Private records remain under `.build/`; publish only reviewed allowlisted observations.

## Integration handoff

The fresh module inspector covers `ntdll.dll`, `kernel32.dll`, `kernelbase.dll`, `win32u.dll`, `winemac.drv`, `wineboot.exe` and `wow64.dll`, preserving actual exports/imports and hybrid metadata in each private `modules.json`. In this pinned fixture build, the PE data exports `__wine_unix_call_dispatcher` and `__wine_unixlib_handle` select the native `ntdll` Unix-call table. Its fixture-only entries are `pear_abi_unix_entry` at index 8 and `pear_stage4_unix_entry` at index 9. `PearStage5Control` in `winemac.drv` uses `MACDRV_CALL(pear_stage5, request)` / `unix_pear_stage5` at index 2 to enter `pear_stage5_window_control`. These indexes describe this exact source/patch set, not a stable public translator API.

The finite assembly gate inspects `__wine_syscall_dispatcher`, `__wine_syscall_dispatcher_return`, `__wine_unix_call_dispatcher`, `call_user_mode_callback`, `user_mode_callback_return` and `signal_start_thread`, plus `pear_x18_enter_host` / `pear_x18_enter_guest` and their pre-resolved getter/setter pointers. Mach-O symbol names carry the platform's leading underscore. Preserve the existing Wine callback return and signal-context machinery; translating a new guest architecture requires its own register, stack, thread and exception mapping evidence.

| Owner | Reusable evidence and required next work |
|---|---|
| #5 / #6, translator integration | Reuse the selected PE-module inventory, Wine Unix-call gateways, native/guest x18 transitions and finite thread/exception fixtures. Resolve actual x64 dispatch, translated context, unwind and executable-memory lifetime before executing a translator. Native `pear_pe_plan_read` rejects nonzero CHPE metadata, non-ARM64 image mapping remains refused, and the selected `xtajit64` paths still report unimplemented x64 emulation. ARM64EC compilation does not close these gaps. |
| #7 / #8, graphics | Reuse the actual Win32/Cocoa callback and lifetime fixture and the ABI/ownership table above. Resolve the pinned Wine/DXMT private-structure and export pairing through a typed, source-matched boundary. Client-view availability, borrowed lifetimes, null/error handling, detach and renderer races need actual pair testing. Metal and D3D have not been exercised here. |
| #10, observation | Preserve bounded process registration, exact image-byte binding, required exit receipts, sentinel survival and cleanup failures. These snapshots do not cover a complete load timeline, arbitrary external process escape or future callbacks after the finite observation interval. Correctness instrumentation does not establish performance or power consumption. |
| #13, distribution | Reuse source/tool/patch records and per-executable development signing checks. Independently resolve redistribution, general-user authorization, packaging, notarization and installation/recovery. Device-bound development success does not establish an ordinary-user release. |

Keep the original #1 combined source decision blocked and #2 host-probe observations limited to their actual finite scope. The selected patch series now corrects the upstream Cocoa startup request lifetime: caller and callback own independent references, cancellation detaches only pending work, and the callback releases the request before using its cached application-loop decision. The original publication point remains before `NSApp.run`; no launch-notification readiness contract was added. Passing source-bound checks, the earlier normal candidate and the final fresh cumulative run do not identify the cause of historical AppKit faults or qualify arbitrary startup/timeout behavior.

## Interpret results

Successful preparation is not a runtime build. A tool version string is not target support. Passing compiler fixtures is not Windows execution. Required missing tools, incorrect artifacts, skipped checks and unknown facts prevent the relevant gate from passing. Preserve original errors and failed attempts.

The commands use 0 for a passed requested gate, 1 for preparation/operation failures, and 2 for argument usage errors. The check, verification and reconstruction commands use 3 when evidence is rejected or the requested gate or reconstruction operation fails; rejected evidence is never a passing result. Actual subprocess/OS status is recorded separately. The verifier checks required evidence and its identities; it must not accept a caller-provided success flag alone.

Raw local records can include paths and diagnostic details and remain under ignored `.build/`; the owned temporary path aliases described above also remain local. Publish only reviewed allowlisted evidence tied to exact sources/tools/configuration/fixtures/output bytes. No profiles, credentials, account state, saves or game files belong in this workflow.

The native loader/page bootstrap, original ARM64 PE/API, guest x18 callbacks, Windows child processes and Stage 4 thread/memory/exception cases are verified only for the recorded finite scope. General thread/exception and dynamic-code semantics remain unqualified. The finite Mac-driver boundary passed Stage 5 and the final Stage 6 reconstruction; these remain development-component observations. FEX execution is #5/#6, graphics pairing #7/#8, full process observation #10, and release/distribution evidence #13 and the separately proposed ordinary-user work. Both observed configure variants reported unavailable EGL development files; EGL remains unqualified. The original combined source decision remains blocked until its owning tasks close their actual inputs and ports.


## October 4, 2026: Graphics supplement follow-up

The earlier ABI-mismatch analysis and #4 fixture results above remain dated
Wine evidence. Task #7 adds a separately maintained, typed Wine/DXMT supplement;
it does not alter #4's historical patch series or reinterpret a window-only
fixture as a graphics test. See [DXMT build and Wine Metal pairing](dxmt-build.md)
for the exact supplement, rebuild, authorization and native evidence procedure.

The historical #7 Stage 4 candidate passed 39 ordinary ARM64/native boundary
cases, including actual view/layer lifetime and diagnostics checks. Current
deterministic reconstruction requires two freshly compiled graphics pairs,
strict byte comparison and new finite native execution on the final candidate.
The full retained Wine payload is reused with explicit graphics overlays; this
is not a new build of every Wine module. #5/#6 still own FEX, translated context,
CHPE loading and x64 execution, and #8 owns the eventual translated D3D11 tests.
No game, general rendering or ordinary-user distribution result follows from
these component observations.


## October 5, 2026: ARM64 native heap reservation dependency

Task #7 isolated a Foundation/Swift low-address lifetime failure and completed
its final native pairing with a source-built loader correction. The independent
[loader patch](../../runtime/wine/patches/0004-arm64-native-heap-reservation.patch)
reuses Wine's zero-fill reservation before framework initialization, preserving
PIE, the 64KiB null guard and guest-address availability. It remains separate
from #4's historical 23-patch series. See the [DXMT contributor handoff](dxmt-build.md#october-5-loader-handoff-to-5-and-8)
for its common baseline, required link flags, source/output hashes and exact
finite verification. #5 must integrate and revalidate affected low mappings,
MAP_JIT and metadata admission on its combined candidate; #7 does not qualify
FEX, translated context or its allocation budget. Earlier #4 observations remain
historical and are not retroactively expanded by this correction.
