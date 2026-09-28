# Wine host development

Status: experimental component work under [Issue #4](https://github.com/postmelee/pear/issues/4). The [Stage 1 input/toolchain checks](../../mydocs/working/task_m1_4_stage1.md) passed on the recorded host; this guide does not establish an executable Wine runtime, Rosetta-free Megabonk or an end-user release.

## Scope and inputs

The [architecture](../architecture.md) defines the runtime goal. This component starts from Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892`. The [original source audit](../source-qualification.md) remains complete with a **blocked** combined Wine/FEX/DXMT decision. Its bytes and historical evidence are preserved.

| Record | Role | Boundary |
|---|---|---|
| [Inputs](../../runtime/wine/inputs.json) | Selected Wine source, exact audit reference, dependencies and unresolved ports | Component input facts; no full-runtime approval |
| [Toolchain](../../runtime/wine/toolchain.json) | Exact public tool artifacts and external native tool/SDK identities | Build inputs; no game runtime or independently rebuilt compiler claim |
| [Build configuration](../../runtime/wine/build-config.json) | Native/PE variants, framework and feature decisions | Explicit fixture configuration, not a Steam/game configuration |
| [Patch series](../../runtime/wine/patches/series.json) | Ordered attributable Wine changes | Initially empty; required Darwin ports are not complete |

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

## Interpret results

Successful preparation is not a runtime build. A tool version string is not target support. Passing compiler fixtures is not Windows execution. Required missing tools, incorrect artifacts, skipped checks and unknown facts prevent the relevant gate from passing. Preserve original errors and failed attempts.

The commands use 0 for a passed requested gate, 1 for preparation/operation failures, and 2 for argument usage errors. The check and verification commands use 3 when evidence is rejected or the requested gate is unmet; rejected evidence is never a passing result. Actual subprocess/OS status is recorded separately. The verifier checks required evidence and its identities; it must not accept a caller-provided success flag alone.

Raw local records can include paths and diagnostic details and remain under ignored `.build/`; the owned temporary path aliases described above also remain local. Publish only reviewed allowlisted evidence tied to exact sources/tools/configuration/fixtures/output bytes. No profiles, credentials, account state, saves or game files belong in this workflow.

Required Darwin loader/page, x18, thread/exception and Mac-driver integration remain later #4 stages. FEX execution is #5/#6, graphics pairing #7/#8, full process observation #10, and release/distribution evidence #13 and the separately proposed ordinary-user work. Both observed configure variants reported unavailable EGL development files; EGL remains unqualified. The original combined source decision remains blocked until its owning tasks close their actual inputs and ports.
