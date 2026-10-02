# Task #7 Stage 3 — ARM64X DXMT and Native Metal Artifact Construction

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Implementation plan: [`task_m1_7_impl.md`](../plans/task_m1_7_impl.md)
Stage: 3 — completed October 3, 2026; Stage 4 is not started.

## Stage Purpose

Construct and independently inspect the pinned DXMT Windows DLLs and native ARM64 Metal bridge using the completed shader prerequisites and exact source-built Wine roles. This establishes artifact construction and static dependency closure. The typed Wine driver interface, graphics execution and Rosetta-free Megabonk remain unverified.

Context used: approved task/implementation plans, root/runtime/DXMT/tests rules, architecture/runtime/source contracts, graphics research and #4's final Wine source/build receipts. Reuse retains upstream C/C++/Objective-C and Meson. Reporting follows the [stage procedure](../skills/task-stage-report/SKILL.md), [daily board procedure](../skills/todo/SKILL.md) and central Hyper-Waterfall v0.3.0 template. The requester explicitly continued after the Stage 2 reports; no GPU capture, Metal validation or lifetime expert procedure applies to this compile-and-inspect stage.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/dxmt/build.py` | 389 lines: strict prerequisite/role replay, owned combined Wine layout, bounded ARM64EC/ARM64X construction and separate compiler/builtin/install evidence |
| `tools/dxmt/inspect.py` | 432 lines: raw hybrid PE inspection, source exports, native static dependency closure, shaders/version/notices and independent output replay |
| `tests/dxmt/test_stage3_build.py` | 154 lines / 9 original builder controls |
| `tests/dxmt/test_artifact_pairing.py` | 403 lines / 30 original metadata and artifact refusal controls |
| [Observations](task_m1_7_stage3_observations.json) | Allowlisted format/count/hash/command outcomes and supplemental deployment metadata |
| `mydocs/plans/task_m1_7_impl.md`, `mydocs/orders/20261003.md` | Concrete CLI/combined-role clarification, explicit continuation and current stage status |

## Body Change Scope / Lossless Preservation

Changes stay in approved `tools/dxmt/`, `tests/dxmt/` and internal `mydocs/` paths. Existing Stage 2 producer files, original source caches, #1 inventory and #4's 23-patch Wine baseline remain unchanged. The inspector deliberately reuses only the unchanged Wine PE class and hybrid-check function through a fixed AST selection and full reader digest. It does not normalize the raw COFF machine or mutate an image to pass inspection. No official product/API document, runtime contract or upstream semantic patch was added.

The new combined layout binds native Wine `winebuild`, `ntdll.so`, `winemac.so` and transitive `win32u.so` separately from the companion ARM64/ARM64EC import libraries. Each copied file retains its exact source/build origin, bytes and mode. The source remains the approved DXMT commit `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` with DirectX headers `9df86f2341616ef1888ae59919feaa6d4fad693d`; 445 materialized files / 8,082,606 bytes are replay-bound. Native LLVM 15 and LLVM-MinGW's cross compiler remain distinct roles. A narrow owned Git adapter returns the full pinned DXMT commit for `describe --always`, avoiding accidental discovery of the parent Pear checkout. It makes no tag/version equivalence claim.

Compiler snapshots precede four explicit Wine builtin operations. The inspector verifies exactly the 32-byte marker replacement at offset 64 and exact installed-byte equality. The native bridge also retains exact build/install equality; no strip or signing operation was performed. Twenty-one selected notice files cover seven used source/tool components; conditional NVAPI and the unimplemented driver layer remain accounted inputs rather than built features. These notices do not complete future release licensing or corresponding-source obligations. Private receipts, raw logs, binaries and supplemental tool output remain ignored. No files were removed for storage.

## Verification Results

Execution context: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple Clang 21, selected Python 3.13.5, native LLVM 15.0.7, LLVM-MinGW 20260908 / LLVM 23.1.1, CMake 3.31.8, Ninja 1.13.1, Meson 1.10.0 and Metal Toolchain 17F109. Builds select native ARM64 and the source ARM64EC cross target with `-marm64x`; no Windows executable wrapper is configured. Operational limits are two jobs, 8 GiB output growth and a 4 GiB free-space reserve, with fresh admission. Observed command growth is not a measured disk or memory peak.

Commands executed (private variables select verified cross-tool and owned Wine-role handles; exact arguments and streams remain in the ignored build receipt):

```sh
python3 -B tools/dxmt/build.py --inputs runtime/dxmt/inputs.json --config runtime/dxmt/build-config.json --toolchain runtime/dxmt/toolchain.json --native .build/task7/stage2-native-shaders1 --prepared .build/task7/stage2-inputs2 --tools .build/task7/stage2-tools2 --cross-tools "$pear_dxmt_cross_tools" --wine-roles "$pear_dxmt_wine_roles" --output .build/task7/stage3-build --jobs 2 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/inspect.py --root .build/task7/stage3-build --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Results:

- Construction and the separate independent artifact gate exited 0. All seven commands succeeded: configure, 131 Ninja build tasks, four builtin operations and installation. No Stage 3 build attempt failed. Build-record SHA-256: `a305ff10161993b0f65ad8c4c2558cefd11d306f6515e69b371da260617e7a5e`; artifact inventory: `eb4d97c4cdaeb6b24fb9652bcf068da59807471961674946b2d5545791dbc599`.
- Four installed DLLs are raw ARM64 outer PE images (`0xaa64`) with verified CHPE code ranges and ARM64X relocation to the alternate AMD64 view (`0x8664`). Raw outer machine, alternate view and configured ARM64EC emission remain separate observations. Nonzero named exports are 2 / 4 / 5 / 145 for `d3d10core.dll` / `d3d11.dll` / `dxgi.dll` / `winemetal.dll`; the respective export-address-table slot totals are 2 / 7 / 9 / 145, including empty ordinal slots. Source definition names/ordinals and required winemetal exports pass.
- Native `winemetal.so` is a thin ARM64 library, 47,161,072 bytes, with expected install name, two loader-relative search paths, Unix call exports and source-bound Wine/System dependency names. The installed set is exactly four DLLs and this library, totaling 61,759,216 bytes. Loader resolution and the typed Mac-driver contract are unperformed.
- Nine generated AIR/header/metallib outputs, the exact pinned-commit version header, 25 generated input files and 21 selected notices passed byte/size/mode replay. External Windows API/CRT imports are explicitly unresolved runtime dependencies; inspection does not invent a supported import set.
- All 195 portable tests passed in 17.771 seconds, including 39 new builder/artifact controls. Controls reject changed source/input/producer/output bytes, incorrect role/target/metadata/export ordinal/search path, builtin mutation outside its marker, omitted shaders/notices, failed/incomplete promotion and rooted file/directory aliases. An initial builder test used an inadmissible fixture location; correcting the fixture preserved production ownership rules. The final builder subset passed 9 tests and inspector subset 30 tests. No unsafe native fault control was executed.
- Governance passed: 22 documents / 172 local targets. Whitespace validation passed. Independent read-only review found no construction-contract defect; the public derivative excludes private roots, profiles, credentials, PE pointers/RVAs and raw diagnostics.
- Supplemental bounded read-only `otool -l` checks bind each inspected native file digest and confirm bridge minimum macOS 14.0 / SDK 26.5, versus minimum macOS 26.5 / SDK 26.5 for `ntdll.so`, `winemac.so` and `win32u.so`. These observations supplement the artifact gate and are labeled separately. They do not establish compatibility with older macOS.
- Compiler logs contain 77 warning occurrences: upstream missing return paths/potential uninitialized values, macOS 15 residency API availability and Wine counterpart deployment-target differences. Existing source semantics were preserved; successful compilation does not resolve possible execution defects.

Native compiler/developer-tool and compiler-sanity execution occurred. GPU, PE/hybrid/guest dispatch, FEX initialization, Steam, game, performance/thermal measurement, signing and ordinary-user distribution qualification were unperformed. `pairing_verified`, `runtime_eligible` and GPU/guest-execution fields remain false.

## Residual Risks

- The typed Wine Mac-driver/DXMT interface is still unimplemented; exported names and static dependencies do not prove ABI, error, ownership or lifecycle compatibility.
- Actual native loader resolution, shader semantics, rendering behavior and warning-related execution defects remain unverified. The mixed deployment targets prevent an older-macOS support claim; this candidate needs later platform/runtime qualification.
- ARM64X metadata construction is not a passed hybrid loader or CPU-translator result. External Windows imports, FEX/CHPE/JIT/exception integration and every required host identity remain later gates with #5/#6.
- Fresh final reconstruction, complete shipped-source/license closure, signing/notarization, hardware/macOS support and ordinary-user installation remain unperformed. No Megabonk, low-power or performance claim follows.

## Impact on Next Stage

Stage 4 can use this constructed pair to implement the separately attributed, shared typed driver boundary and original finite native contract/lifecycle fixtures. It must consume exact CPU-layer identities when available, retain the immutable Wine baseline and complete actual per-executable permission admission before restricted work. Compilation and metadata inspection do not authorize hybrid execution. Root continues to serialize native operations; #5's memory-owner prototype has its own concrete design checkpoint.

## Approval Request

Review Stage 3 and approve continuation to Stage 4 typed-driver pairing and its planned finite native checks. This request does not authorize guest/game execution, final PR publication or distribution. #5 separately requests approval of its concrete executable-memory design before any owner prototype.
