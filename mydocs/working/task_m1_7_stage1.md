# Task #7 Stage 1 — DXMT Inputs and Native Build Prerequisites

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Implementation plan: [`task_m1_7_impl.md`](../plans/task_m1_7_impl.md)
Stage: 1 — completed October 2, 2026; Stage 2 is not started.

## Stage Purpose

Close the selected DXMT source/terms, existing tool and Wine-role inventory before reproducing native shader prerequisites. A complete inventory may accurately include unavailable tools; it does not imply shader-build readiness, a built renderer or game compatibility.

Context used: the approved task/implementation plans and their architecture/runtime/source/graphics research references, root/runtime/tests rules and #4 source/build handoff. The requester approved this detailed plan and Stage 1 in the same thread. Reporting follows the [stage procedure](../skills/task-stage-report/SKILL.md), [daily board procedure](../skills/todo/SKILL.md) and central Hyper-Waterfall v0.3.0 template. No GPU/Metal engineering or capture fixture was performed in this metadata stage.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/dxmt/AGENTS.md`, `inputs.json`, `toolchain.json`, `build-config.json` | Scoped exact source/terms, tool candidates, build targets and false readiness/qualification boundaries |
| `tools/dxmt/common.py`, `prepare.py` | Bounded fresh source derivation, exact Git/source policy, literal inventory names and EC-index interpretation |
| `tools/dxmt/check.py`, `verify.py` | Selected Wine/tool bytes, real bounded metadata probes and independent inventory/readiness replay |
| `tests/dxmt/test_stage1_*.py`, `support.py` | 70 portable source/role/format/legacy-mode/command/policy refusal controls |
| [Observations](task_m1_7_stage1_observations.json) | Finite reviewed source/tool/probe outcome export without private paths or raw streams |
| `mydocs/plans/task_m1_7_impl.md`, `mydocs/orders/20261002.md` | Approval, concrete CLI/legacy-format clarifications and synchronized Stage 1 status |

## Body Change Scope / Lossless Preservation

All additions stay in the approved `runtime/dxmt/`, `tools/dxmt/`, `tests/dxmt/` and `mydocs/` locations. No official/product/API document, shared Wine helper, historical receipt or #4 patch/source layer changed. Original caches and unsuccessful attempts remain; no files were deleted for space. Repository artifacts are English.

Retain upstream C/C++/Objective-C and Meson. Nine exact source components are accounted for: DXMT, DirectX headers, conditional NVAPI, native LLVM 15, Wine upstream/interface, LLVM-MinGW source, its LLVM source and MinGW-w64. Only DXMT and required DirectX headers are materialized here. LLVM/NVAPI trees remain inventory observations; literal `%` names and existing symlinks are accounted for without extraction or URL decoding. Selected notices/source checks remain required. LGPL/LLVM/MinGW and contributor-policy observations do not establish release clearance or authorize an upstream submission.

## Verification Results

Execution context: Apple M4 Pro, 24 GiB memory, macOS 26.5.2 (25F84), Xcode 26.6, SDK 26.5, Python 3.13 and existing LLVM-MinGW 20260908 / LLVM 23.1.1. Host metadata observed about 43.7 GiB free before final probes. Native LLVM 15 libraries/headers and prospective large-build peak are **unperformed/unknown**. Developer metadata probes ran; no installation, tool bootstrap, DXMT/LLVM/shader compilation, signing, GPU or guest execution occurred.

Commands executed (private cache/role handles are withheld; raw byte/argument receipts remain in ignored owned outputs):

```sh
python3 tools/dxmt/prepare.py --inputs runtime/dxmt/inputs.json --source-cache <original-read-only-cache> --output .build/task7/stage1-inputs5 --require-empty
python3 tools/dxmt/check.py inventory --inputs runtime/dxmt/inputs.json --toolchain runtime/dxmt/toolchain.json --config runtime/dxmt/build-config.json --prepared .build/task7/stage1-inputs5 --wine-native <retained-native-role> --wine-companion <retained-companion-role> --tools <retained-locked-tools> --output .build/task7/stage1-check3 --require-accounted
python3 tools/dxmt/verify.py inventory --root .build/task7/stage1-check3 --require-accounted
python3 tools/dxmt/verify.py inventory --root .build/task7/stage1-check3 --require-shader-build-ready
python3 -B -m unittest discover -s tests/dxmt -p 'test_stage1_*.py'
python3 tools/check_governance.py
git diff --check
```

- All **nine source components** and exact selected terms/source-check sets passed source preparation and independent replay. DXMT/DirectX source bytes, Git/tree/listing/blob identities and mounts are checked rather than accepted from a `passed` label.
- Exact #4 native and companion build/source/installed-manifest identities and selected Wine files passed. Native import archives contain ARM64 objects; companion archives contain both ARM64 and ARM64EC objects. The bounded `/<ECSYMBOLS>/` metadata reader checks symbol bounds and real member references rather than assigning it a machine type. ARM64EC link compatibility remains **unperformed**.
- Six selected cross tools and notices were reread. The real wrapper-to-Clang alias/driver chain was bound before version probes. All six selected tools had actual executable mode `0755`; the legacy manifest has no historical mode field, so that baseline is explicitly unavailable and current mode observations are replay-bound. This is selected-tool/notice inspection, not a new full toolchain build or distribution proof.
- **Nine bounded native metadata probes** were recorded with exact independent argv/log replay. Git, Python, SDK path/version and three cross-tool versions succeeded. Wrappers use ARM64 `/bin/sh`. `metal` resolution succeeded but functionality is unverified; `metallib` lookup returned **72**.
- **Accounted inventory: exit 0. Shader-build readiness: expected refusal, exit 3.** CMake, Meson and Ninja were unavailable on this task's inspected PATH; no installation/bootstrap occurred. FEX's task-local build tools are separate possible reuse candidates, not automatically qualified #7 tools.
- **70 portable tests passed.** Controls reject altered/missing source policy, objects/gitlinks, unsafe output/materialized paths, source/receipt bytes, wrong or mixed Wine roles, malformed EC indices, tool/alias/mode changes, wrong native commands, SDK changes, incomplete logs and unsupported readiness/qualification claims. Governance passed 22 routed documents and 172 local targets; final plan/report links and staged whitespace are checked before the bundled commit.

Preserved failures exposed literal LLVM `%` inventory names, an EC-index/object classification error and a missing legacy tool-manifest mode field. Their corrections keep strict materialized/output paths, real archive machine facts and the unchanged historical records. No expected readiness refusal is described as a successful shader build.

## Residual Risks

- `shader_build_ready`, `dxmt_built`, `pairing_verified` and `runtime_eligible` remain false. Native LLVM 15, Metal compilation/metallib linking, DXMT cross compilation and Wine ARM64EC import linking remain unperformed.
- The source-inspected private Wine client-view mismatch and missing typed/exported interface still require the later adapter. Numerical private offsets do not become a usable contract.
- Metal toolchain acquisition/qualification and actual LLVM/DXMT build storage must be resolved before dependent commands. Current free space does not establish an unknown build peak.
- No graphics, performance, thermal, Megabonk or ordinary-user distribution result follows from this inventory. The original aggregate source qualification remains unchanged.

## Impact on Next Stage

Stage 2 prepares and verifies task-local native build/shader tools and LLVM 15 prerequisites. Review exact available Metal toolchain actions before any required installation or account/license interaction; preserve normal macOS protections. FEX's pinned task-local CMake/Ninja may be reused only after fresh #7 identity/capability checks. Keep CPU/loader/JIT changes with #5 and graphics/native bridge changes with #7; the combined pair remains a later construction/validation gate.

## Approval Request

Review Stage 1 and approve explicit continuation to Stage 2's already planned native shader prerequisites. Compilation still depends on actual verified tool readiness and measured storage; this approval does not imply Metal installation, GPU/guest execution or release qualification.
