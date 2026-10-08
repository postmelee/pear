# Task #8 Plan — Translated Direct3D 11 through Native Metal

GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Work branch: `codex/task8`
Planning date: October 8, 2026. Status: task plan awaiting approval.

## Purpose

Qualify a finite, redistributable x64 Direct3D 11 suite through the final Pear
Wine/FEX CPU path and source-built DXMT/native Metal components. Demonstrate
expected rendering/readback, presentation and lifecycle behavior, with evidence
of the actual loaded backend. This is the graphics prerequisite for Megabonk;
a successful device or visible triangle alone does not complete the task.

## Background

Read the [README](../../README.md), [documentation index](../../docs/README.md),
[architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md),
[runtime contracts](../../docs/runtime-contracts.md),
[graphics research](../../docs/research/graphics-and-game-integration.md),
[CPU guide](../../docs/development/fex-host.md),
[DXMT guide](../../docs/development/dxmt-build.md), applicable root/runtime/DXMT/
tests/docs rules, task/Git workflow and document structure procedures.
`task-start` and `todo` apply now; stage/final-report procedures apply later.

- #6 is CLOSED: [PR #38](https://github.com/postmelee/pear/pull/38) merged as
  `d019a6efb202615e84cbcb9be63e5f55ba7f44c1` at 19:01 KST. Its four stages
  and ten publication CI jobs passed. The [final report](../report/task_m1_6_report.md)
  records 18 CPU/boundary passes, explicit AVX/WoW64 limits and finite ordering.
- #7 is CLOSED: [its final report](../report/task_m1_7_report.md) records four
  constructed ARM64X graphics DLLs, native ARM64 winemetal, exact 2,878-entry
  reconstruction and two 39-case ordinary native runs. Those runs did not execute
  translated x64 D3D11 or the ARM64X graphics dispatch path.
- #8 therefore has completed acceptance prerequisites, but combining the two
  component sets needs fresh interface/payload admission and affected execution.
  Copying libraries into an old prefix cannot inherit either qualification.
- #9 has a separate active worktree and plan for the native manager/profile.
  Preserve its sources, contracts and task-board row on later integration. #8
  reuses current bounded development supervision; it does not implement #9/#10.
- Main `master` is updated and its untracked `analysis/` and `research/` are
  unchanged. Retained #1/#3/#5/#6/#7 worktrees remain dependency/evidence inputs.
  #6's work/publication branches were deleted after merge; its exact checkout
  remains detached at `d9b43ef` because its ignored evidence is needed by #8.

## Scope

### Included

- Pair the final #6 FEX with #7 graphics through one explicit Wine configuration,
  preserving ordered supplements, source/tool identities and authorization.
- Reuse suitable DXMT x64 tests; define bounded expected results for device,
  buffers/textures, shaders/compute, depth/blend, staging readback, swapchain,
  resize and present. Extend only missing acceptance judgments.
- Exercise native/guest callback boundaries, GPU/CPU lifetime synchronization and
  repeated device creation/teardown on that same candidate.
- Identify actually loaded D3D11/DXGI, winemetal and required native dependencies;
  reject missing proof or silent substitution by WineD3D, DXVK or another backend.
- Capture and review targeted Metal validation diagnostics on required cases;
  distinguish correctness settings from later performance settings.
- Reduce and fix failures inside existing Wine/FEX/DXMT architecture, rebuilding
  only changed components and rerunning affected tests. Known required failures
  remain blockers. Broader ABI/owner redesign requires a reviewed amendment.
- If useful after a coherent translated path exists, use the owner's existing
  Megabonk files for a bounded diagnostic startup. This is optional diagnosis,
  not an acceptance substitute or a normal Steam/gameplay support claim.

### Excluded

- D3D12, Vulkan/MoltenVK, a new shader translator or CPU engine, Rust rewrites,
  performance/thermal claims, exhaustive graphics conformance or every Mac/OS.
- Production supervisor, full process observer, official Steam onboarding,
  20-minute gameplay/save qualification, app installer and community UI.
- New system/toolchain installation, changed signing permissions or security
  bypasses. Existing development authorization must be checked before use.
- Proprietary game assets, authenticated prefixes, signing material or raw private
  captures in Git; generated upstream contributions contrary to source policy.

## Design Direction

Keep upstream languages and existing component boundaries. Work under new #8
output identities; do not modify source caches, final #6/#7 receipts or historical
reports. Freeze the combined dependency closure before accepting execution.

| Existing work | Reuse decision | Missing qualification |
|---|---|---|
| #6 final FEX DLL `2925abaafea4d4c3293c30e778629208b507d9690e7d2b128e9b500733608364` and four CPU patches | Reuse exact current C++/ASM implementation, actual policy and admission | ARM64X graphics calls, callbacks and combined runtime still unperformed |
| #7 final graphics/typed bridge and corrected native loader | Reuse current artifacts where compatible; merge source supplements when a shared Wine build is required | Revalidate changed interfaces and final identities; old native results are not translated-rendering evidence |
| DXMT `tests/dx11` at `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` | Adapt C++/HLSL demo setup rather than write another unrelated renderer | Bounded execution, readback oracles, repeatable lifecycle and actual backend proof |
| Existing `tools/dxmt/` pairing/evidence and `tools/cpu/` execution readers | Reuse source/build/signing/ownership checks through narrow #8 adapters | New fixture IDs, combined candidate provenance and GPU results must be admitted explicitly |
| Existing native pairing fixture | Reuse relevant callback and physical lifetime observations/controls | Run affected boundaries on the combined translated route; native-only results stay native-only |

Planning inspected retained DXMT `tests/dx11/meson.build`, triangle device/shader/
resize/present code and cube operation sites. The build lists cube, BPL, triangle
and two HDR demos, with D3D11/DXGI/d3dcompiler dependencies. Triangle uses a message
loop, runtime HLSL compilation and interactive error dialogs; it lacks the bounded
result/readback contract needed here. Stage 1 will inspect complete selected
functions and per-file provenance before adaptation. Compile success or COM
Release return values alone cannot prove output correctness or physical cleanup.

Prefer original analytic expected pixels/buffer values where deterministic;
freeze comparison regions, formats and necessary tolerances before execution.
Avoid undefined rasterization edges or deriving golden output from the candidate.
Review existing suitable fixtures before adding missing compute/depth/blend cases.
A native Windows graphics reference is useful only for an ambiguous contract,
not a reason to require a new remote GPU service for every deterministic test.

DXMT's checked license is LGPL-2.1-or-later; preserve per-file notices and inspect
any borrowed shader/asset terms. Prefer procedurally generated data over demo
textures/models with unclear provenance. The pinned CONTRIBUTING policy rejects
AI/LLM-authored upstream contributions; this task is downstream Pear work.

For actual Metal validation, apply the [Pear Apple-tooling router](../skills/pear-apple-tooling/SKILL.md)
and existing [guide](../../docs/development/apple-tooling.md). Select
`using-metal-validation` at Apple revision
`4f42344c90be22112f46becc3fb9687f423f2f88` (plugin `1.0.0-beta.1`) and read its
original source before implementation. Select presentation/lifetime or rendering
experts only for a concrete boundary or failure. Planning read the router/guide;
no expert execution, capture, plugin installation or Apple porting lifecycle
has been applied. Recheck local tools and ensure settings reach the Metal device
process; newer CLI availability must not be assumed from pinned documentation.

## Document Location Judgment

| File | Classification | Audience | Selected location | Alternative | Reason |
|---|---|---|---|---|---|
| Translated graphics reproduction and limits | Official technical guide | Contributors/testers | Extend `docs/development/dxmt-build.md` | New graphics-test guide | Existing component guide owns this handoff; avoid duplicate instructions |
| CPU integration changes if required | Official technical guide | Integrators | Existing `docs/development/fex-host.md` | New CPU guide | Update only affected final-candidate requirements |
| Scoped DXMT ownership clarification | Agent implementation rules | Contributors/agents | Existing `runtime/dxmt/AGENTS.md` | Root expansion | Existing text is #7-specific; acknowledge approved #8 supplements without changing #9 ownership |
| Fixture contracts and notices | Executable test metadata | Test authors/tools | `tests/dxmt/` | `mydocs/` | Keep inputs and expectations beside fixtures |
| Plans/reports/sanitized observations | Task artifacts | Reviewers | Existing `mydocs/` folders | Official docs | Dated evidence remains separate from supported-product claims |

No roadmap, schema or document relocation is proposed. If integration requires
changing a #9-owned contract, resolve the scope conflict before editing it.

## Expected Changed Files

New: a small `translated_*` group in `tests/dxmt/` and `tools/dxmt/` for fixture
metadata, source adaptation and combined-runtime execution/comparison. Reuse
existing modules instead of duplicating a generic builder, runner or observer.
Required graphics fixes belong in attributed supplemental `runtime/dxmt/` patches;
CPU/Wine fixes belong in their existing component patch locations.

Modified only as needed: existing component adapters and the official guide/rules
listed above. New untracked evidence stays in `.build/task8/`. No source changes
or implementation plan are made before task-plan approval.

Task artifacts: `mydocs/orders/20261008.md`, this plan, later
`mydocs/plans/task_m1_8_impl.md`, `mydocs/working/task_m1_8_stage{N}.md` and
`mydocs/report/task_m1_8_report.md`.

## Tentative Stages

1. **Combined candidate and fixture contract:** admit #6/#7 inputs; map shared
   Wine/Metal interfaces and missing dependencies; freeze the bounded fixture
   suite/oracles and prepare a coherent candidate. Verify actual translated
   device creation/backend selection before expanding rendering coverage.
2. **Deterministic rendering and readback:** implement/adapt the minimum buffer,
   texture, shader/compute, depth/blend cases. Check exact/toleranced expected
   output and targeted diagnostics; reduce required failures to a small fixture.
3. **Presentation and lifetime:** bounded window callbacks, present/resize and
   repeated device/resource teardown with GPU completion and physical cleanup;
   collect actual backend/module evidence. Retain incomplete observation as a gap.
4. **Integrated qualification and handoff:** bind all required results to the
   final candidate; rerun only invalidated coverage; publish reproduction and
   limitations, final report and reviewable PR. Diagnostic game startup remains
   optional and cannot replace or block the declared fixture acceptance.

## Verification Plan

Planning availability: original-path #6/#7 artifacts and DXMT source are retained;
about 34 GiB free observed. This is not a fresh byte-for-byte admission. Prior
reports record Apple M4 Pro/macOS 26.5.2, Xcode 26.6 and installed Metal tools;
actual availability/signing and dependency identities will be rechecked in Stage 1.
No new build, guest/GPU run, validation capture or game launch occurred in planning.

### Stage Verification

| Stage | Required result | Retained evidence |
|---|---|---|
| 1 | Source/license/fixture contract complete; coherent shared dependencies; actual x64 device path and selected backend | Input/patch/tool hashes, inspected imports and exports, signed payload and initial module/architecture observations |
| 2 | Declared rendering/readback values match independent expected contracts; shaders/compute and depth/blend exercise actual GPU work | Exact fixture/shader inputs, expected/actual values, targeted validation settings/log assessment and reduced failures |
| 3 | Bounded presentation/resize/callbacks and repeated lifecycle pass with completed work and physical cleanup | Outcome counts, observed modules, lifetime records, original errors, owned cleanup and sentinel survival |
| 4 | All three Issue criteria satisfied on the final candidate, with explicit unsupported/unperformed categories | Combined identity, coverage summary, reproducible commands, sanitized diagnostics and final report |

### Integrated Verification

- Expected image/readback and lifecycle checks must complete; missing terminals,
  failed HRESULTs, timeouts, absent oracles and unsupported required features fail.
  Test the new result reader with a wrong pixel/value and incomplete run, not a
  test for every implementation branch.
- Static DLL names or environment overrides alone are insufficient: bind actual
  loaded guest modules/native Metal dependencies to the intended DXMT payload.
  Missing relevant backend evidence blocks #8; broader complete process coverage
  remains #10 and must not be silently claimed here.
- Confirm validation enabled on the process creating Metal work and review actual
  diagnostics. Keep required errors, unknowns and unavailable tools explicit.
  A clean log alone cannot establish correct output. Later performance runs must
  exclude these correctness layers.
- Preserve before/after authorization, bounded owned processes/output, unrelated
  sentinel survival and successful cleanup from existing execution tooling.
- Reuse #6/#7 evidence only for unchanged input/claim scope. A changed FEX, Wine
  loader/bridge or DXMT payload invalidates affected CPU/native/graphics results.
  Run the necessary integration checks once after the final relevant change;
  no blanket compiler, CPU or graphics rebuild merely for report wording.
- Serial heavy builds; reuse verified LLVM/shader tools; set a preflight disk
  budget before building. Delete completed owned scratch only after retaining
  failures and needed receipts. Do not remove dependency worktrees to gain space.
- Governance/local links and `git diff --check` pass; task worktree clean before
  PR publication. Repository writing stays English; user discussion stays Korean.

## Risks

- **Shared Wine incompatibility:** native #7 and translated #6 use distinct
  historic constructions. Verify coherent source/ABI/configuration rather than
  swapping DLLs by filename; rebuild the minimum shared closure if necessary.
- **False graphics success:** a visible triangle or successful Present return
  misses shader/readback/backend/lifetime errors. Use explicit independent output
  and completion evidence; record display/observation limitations.
- **Shader compilation dependencies:** upstream demos depend on d3dcompiler_47;
  verify the source-built compiler/import path or deterministic redistributable
  shader generation rather than silently borrowing a proprietary installation.
- **Coverage and scale:** finite fixtures do not prove Unity/game-scale behavior,
  arbitrary concurrency or every GPU feature. Required failures remain blockers.
- **Storage and concurrent work:** keep unique failures and #6/#7 inputs; #9's
  changes and later board merge must preserve both tasks. No whole-cache copies.

## Approval Request

Approve this #8 scope, reuse direction, four stages, document locations and
necessary-test strategy. Then prepare the detailed implementation plan; Stage 1
implementation follows its approval. This request does not reopen #6/#7 or
request approval for the already authorized #6 merge.
