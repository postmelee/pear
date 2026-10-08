# Task #8 Stage 2 — Deterministic Rendering and Readback

GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Implementation plan: [task_m1_8_impl.md](../plans/task_m1_8_impl.md)
Stage: 2 — complete, October 9, 2026. Issue #8 remains open.

## Stage Purpose

Qualify the five declared D3D11 rendering cases through translated x64 execution
and native Metal, with independent numerical results and actual pipeline validation.
This is bounded synthetic rendering. Megabonk has not been run or qualified here.
An unhandled CPU alignment case discovered during this work remains unresolved.

Context used: the approved #8 task/implementation plans; root/runtime/FEX/DXMT/test
rules; architecture and runtime evidence boundaries; existing #5/#6/#7 sources and
Stage 1 results. The Pear Apple-tooling router selected `using-metal-validation`
at `4f42344c90be22112f46becc3fb9687f423f2f88` (plugin `1.0.0-beta.1`). Local
`MetalValidation(1)` and the installed SDK's pipeline-state properties were checked.
Apple's [shader-validation guide](https://developer.apple.com/documentation/xcode/validating-your-apps-metal-shader-usage)
was consulted when the documented UID logs did not appear. Stage-report and daily
board procedures apply; no extra plugin/toolchain was installed.

## Artifacts

| File | Change Summary |
|---|---|
| `tests/dxmt/translated_rendering.cpp`, `translated.hlsl` | Original MIT x64 fixture and four Shader Model 5.0 entry points; seven readbacks across five cases |
| `tests/dxmt/translated_cases.json` | Input patterns, formats, pixel regions, blend tolerance and compute formulas frozen before execution |
| `tools/dxmt/translated_render_build.py` | Fixture-only compilation with pinned x64 compiler and embedded exact HLSL |
| `tools/dxmt/translated_render_runtime.py` | Development-signed overlay, complete inventory, CPU-code preservation and current ARM64 dependency closures |
| `runtime/dxmt/patches/0002-pipeline-validation-observation.patch` | Read-only query of actual created render/compute pipeline validation state; no descriptor or ownership change |
| `tools/dxmt/translated_pipeline_build.py` | Recompile one native object and relink winemetal using verified retained headers/objects/archives |
| `tools/dxmt/translated_run.py`, `translated_check.py`, `translated_render_check.py` | Existing owned supervisor, shared backend proof, mathematical oracle, shader/pipeline identity and mandatory native recheck |
| `tests/dxmt/test_translated_results.py` | Twelve focused terminal/readback/validation refusal tests, including the five existing device controls |
| [Allowlisted observations](task_m1_8_stage2_observations.json) | Exact evidence identities, results, original failure and limits without private paths or signing material |

## Body Change Scope / Lossless Preservation

All changes remain in the existing approved test/tool/runtime-patch/task-document
roots. No official product documentation, manager contract or other task changed.
The plan records concrete commands, pipeline observation and the CPU limitation.
No GitHub publication, issue closure or Stage 3 implementation occurred.

Retain upstream C/C++/Objective-C and source notices. DXMT's pinned triangle setup
informed API/compiler usage; fixtures/shaders are original Pear MIT code. The
source-built Wine `d3dcompiler_47` compiled four actual DXBC blobs. Its imported
`wined3d` supplies compiler functions; it is not the selected D3D11 renderer.
Actual D3D11/DXGI/winemetal paths, addresses and installed bytes are checked.
Compiler dependency paths/bytes are also checked against the signed payload.

The first fixture generated texture bytes at runtime. Its compiler emitted a
valid x64 word store crossing a 16-byte boundary, which reached the current
unimplemented delivered-unaligned-repair path (`0x80000002`, fixture RVA `0x1bb2`).
All four shaders and the buffer readback had already succeeded. The run then
timed out in Wine's debugger; owned cleanup and sentinel protection passed.
This original failure is preserved and is **not fixed or reclassified as a pass**.
The identical texture bytes are now immutable compile-time data, isolating the
approved GPU cases from that CPU preparation path. No numerical oracle, TSO policy
or exception handling was weakened. General x64/game readiness remains blocked
by this limitation until the actual exception path is implemented and verified.

## Verification Results

Execution context: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), existing
authorized development signing and normal macOS protections. Metal API/shader
validation is enabled before device creation, with shader error reporting and
zero-fill mode. These are correctness runs; no performance or power claim follows.

Evidence reuse: Stage 1 (`b049adf`) supplies unchanged CPU/FEX/Wine/loader code and
its 19-case CPU corpus plus ordering results. This stage does not rerun or expand
those CPU claims. Only the x64 fixture and the native winemetal observation change.
Therefore the device path and original 39-case native bridge oracle were rerun
on the exact final signed candidate. Existing static archives were reused; there
was no full Wine/FEX/DXMT rebuild. All signed dependency closures are recalculated
at the final runtime location, rather than retaining parent paths and hashes.

| Required result | Observed outcome |
|---|---|
| Buffer update/copy/map | All 64 uint32 values exactly matched, including endpoints |
| Texture upload/copy and point sampling | Both 8×8 RGBA8 readbacks exactly matched all texels; observed row pitch 32 |
| Raster VS/PS | 3,584 required pixels matched analytic interior/clear regions; declared raster-edge band excluded |
| Depth and blending | 4,096 pixels each; LESS/write occlusion matched red, half-alpha blend matched within one UNORM unit |
| Compute | All 64 structured-buffer uint32 results matched `(i ^ 0xa5) * 3 + 7` |
| Actual pipeline validation | 25 created pipelines reported enabled; four render pipelines matched the fixture VS identity and one compute pipeline matched its CS identity |
| Device and backend | Hardware feature level 11_0; actual FEX/DXMT/native Metal route, exact module bytes and intended loader's API/GPU banners |
| Native bridge recheck | All 39 original cases passed; physical lifetime observed balanced under the existing oracle |
| Authorization and ownership | Before/after admission, bounded execution, normal guest exit 42, cleanup and unrelated-sentinel survival passed |
| Native architecture | 41 signed ARM64 payload images; every captured native process/image observation was ARM64 and no Rosetta execution was observed |
| Focused checks | Twelve result/negative-control tests passed; full translated portable set had 19 tests after the final pipeline control; governance and diff checks passed |

Final retained selection: ignored `.build/task8/render-runtime4`, `render-build2`,
`pipeline-build3`, `rendering5`, `device8` and `pairing6`. The stage checker replayed
raw observations and required both rendering and native pairing; it returned
`passed: true`, `stage: 2`, `cases: 5`. Exact identities are in the observations.
The original failure remains under `rendering1` and `render-build1`, including the
original PE, hash-verified original source snapshot, logs and bounded stack sample.

Verification commands:

```sh
python3 -B -m tools.dxmt.translated_check --run .build/task8/device8 --runtime .build/task8/render-runtime4
python3 -B -m tools.dxmt.translated_check --run .build/task8/rendering5 --runtime .build/task8/render-runtime4 --pairing .build/task8/pairing6 --require-stage 2
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_results.py'
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_*.py'
python3 -B tools/check_governance.py
git diff --check
```

The plan records the corresponding actual run commands and pairing invocation.
The first two pipeline-build preparations failed before compilation (JSON-list
reader and compiler-wrapper argument index); these were corrected before the
successful one-object build. Four existing upstream deployment-target availability
warnings remain recorded; they do not establish support for older macOS versions.

The documented pipeline UID output was absent in retained/live system logs.
Direct public `shaderValidation` queries resolved the required instrumentation
question without changing pipeline policy. The final run does not need an extra
log-stream process. A cold-prefix optional media registration reported a missing
`winegstreamer` dependency; it did not affect these completed cases and remains
an explicit media-support gap. No required Metal validation error was observed.

After final verification, three superseded successful synthetic prefixes were
removed, retaining their full inventories and raw outcomes. This retired about
2.36 GiB of logical files; approximately 14.5 GiB was free afterward. Original
failure data, final prefixes, source/build artifacts and signing records remain.
No proprietary game files, authenticated prefixes, saves or other-task data were
accessed or removed.

## Residual Risks

- Delivered unaligned x64 access repair remains unavailable. Preserve the failing
  instruction and inputs; reuse the existing finite FEX snapshot/preparation and
  owner mechanisms when designing its real exception-path integration. Raw
  upstream JIT writes must not bypass Pear's write/execute ownership protocol.
- Rendering readbacks do not establish screen presentation, resize callbacks or
  translated physical resource destruction. Those remain Stage 3 requirements.
- Observed native execution is Rosetta-free; complete late-load observation,
  Steam/i386 helpers, Megabonk execution and ordinary-user distribution remain
  unqualified. The existing unsupported AVX lane claim is unchanged.
- Current development authorization and this host's successful execution are not
  evidence of distribution eligibility or support on other Macs/macOS versions.

## Impact on Next Stage

Carry the final candidate, its exact fixture/bridge sources and current dependency
closures into Stage 3. Implement the approved three device/window cycles and 18
presents with resize, actual presentation observation, GPU completion and physical
teardown. Reuse unaffected evidence; rerun only boundaries changed by the new
fixture/bridge. Track the discovered CPU failure as a real game-readiness dependency,
not an optional warning hidden behind the rendering result.

## Approval Request

Review this bounded Stage 2 result and approve proceeding to Stage 3. No broader
game-support claim is requested.
