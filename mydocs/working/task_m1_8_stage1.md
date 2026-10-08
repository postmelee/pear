# Task #8 Stage 1 — Coherent Candidate and Device Path

GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Implementation plan: [task_m1_8_impl.md](../plans/task_m1_8_impl.md)
Stage: 1 — complete, October 9, 2026. Issue #8 remains open.

## Stage Purpose

Combine the qualified CPU components and source-built native DXMT/Metal path,
then establish actual x64 D3D11 device creation on the combined candidate.
This is finite synthetic execution, not rendering or Megabonk qualification.

Context used: the approved task/implementation plans, root/runtime/FEX/DXMT/test
rules, architecture and delivery requirements; existing #5/#6 CPU and #7 native
bridge evidence; the plan's pinned Apple Metal validation guidance. Stage-report
and daily-board procedures apply. Existing upstream languages and notices remain.

## Artifacts

| File | Change Summary |
|---|---|
| `tests/dxmt/translated.cpp`, `translated_cases.json` | Original MIT x64 device fixture; declared graphics requirements and full affected regression scope |
| `tools/dxmt/translated_inputs.py`, `translated_build.py`, `translated_loader.py` | Exact input admission, existing 14-file Wine graphics supplement, affected driver/fixture build and corrected #7 loader reuse |
| `tools/dxmt/translated_owner.py`, Wine `0005-fex-caller-without-loader-lock` patch/identity | Replace loader-lock caller lookup with the existing VM image allocation identity query; rebuild only PE ntdll |
| `tools/dxmt/translated_fex.py`, FEX `0003-high-private-allocations` patch/identity | Preserve low guest VA by constraining FEX-private anonymous allocations above 4 GiB; build over final #6 sources |
| `tools/dxmt/translated_runtime.py`, `translated_run.py` | Complete immediate-origin ledger, 41 native ARM64 images, current development signing and bounded owned execution |
| `tools/dxmt/translated_pairing.py`, `translated_regression.py`, `translated_check.py` | Reuse original native/CPU/ordering oracles; final replay requires actual records from one candidate |
| `tests/dxmt/test_translated_*.py` | Twelve focused input, terminal and synthetic-prefix configuration checks |
| [Allowlisted observations](task_m1_8_stage1_observations.json) | Outcome scopes and exact private evidence hashes without private paths or signatures |
| [Investigation notes](task_m1_8_stage1_notes.md) | Preserved failed hypotheses, deciding diagnostics and retention decisions |

## Body Change Scope / Lossless Preservation

The approved locations remain unchanged. The implementation plan records the
implemented full-index checker syntax; the task board records Stage 1 completion.
The DXMT scoped rules now distinguish approved #8 integration from historical #7.
No product guide, public contract, manager/observer subsystem or other task changed.
No GitHub publication or issue closure occurred.

Two integration repairs are selected. First, an FEX memory callback held the
process heap lock and attempted Wine's loader lock through `RtlPcToFileHeader`;
a worker held the loader lock and waited for the heap. The replacement checks
committed image type and allocation base against the same pinned translator.
It introduces no new caller, owner ABI or permission. Second, rpmalloc's 512 MiB
reservation consumed the original CPU fixture's low fixed data address after
integration with #7's heap-exclusion loader. The FEX-private allocation wrappers
now use their existing Windows address-requirement approach to preserve that
address space. Guest allocations and exact CPU PE/expected values are unchanged.
The old WOW64 behavior remains; WOW64 execution is not qualified.

Wine's LGPL and FEX's MIT source notices remain in the corresponding source.
These are downstream changes, not an upstream contribution. Failed diagnostic
patches are retained privately and are not selected for the final runtime.

## Verification Results

Execution context: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113),
existing authorized development profile and normal macOS protections. API and
GPU shader validation were enabled before Metal device creation. These are
instrumented correctness runs; no performance or power claim follows.

Evidence reuse: retain #6's exact native Windows x64 reference PEs/results and
#7's source-built graphics/shader dependencies and corrected loader. Rebuild the
affected Wine driver, PE ntdll and FEX supplement. Loader/memory changes invalidated
CPU runtime acceptance, so the entire declared corpus and ordering checks ran on
this candidate. No historical CPU/graphics execution was relabeled as new evidence.

| Required result | Observed outcome |
|---|---|
| Translated device | x64 fixture completed, exit 42, hardware D3D11 feature level 11_0 |
| Actual route | FEX dispatch; matching loaded D3D11/DXGI/winemetal paths, addresses and bytes; native winemac/winemetal/Metal; intended loader's API/GPU validation banners |
| Native bridge | All 39 original cases; 3 views, 3 layers and 1 proxy physically deallocated; zero final leases/attachments; strict descendant-exit assessment passed |
| CPU comparison | 19 original PEs: 18 matched native reference; AVX lane preservation explicitly unsupported/not exposed, expected exit 77 |
| Ordering | 32,768 measured pairs, 8 joined workers, required effective software-TSO policy and 8 checked worker retirements; no forbidden result |
| Authorization and ownership | Current admission before/after execution; owned cleanup and unrelated-sentinel survival passed |
| Native architecture | 41 signed native ARM64 payload images; every captured native process/image observation was ARM64, with no observed Rosetta execution |
| Focused portable checks | 12 passed; governance check passed; `git diff --check` passed |

Selected local evidence is under ignored `.build/task8/`: `runtime7`, `device7`,
`pairing5`, `cpu7.json`, `ordering7.json` and `stage1`. Their exact identities are
in the linked allowlisted observations. The final checker re-read the raw logs,
replayed every required oracle and checked current authorization without launching
another fixture. Its result is `passed: true`, `stage: 1`.

Executed verification commands (task-relative paths):

```sh
python3 -B -m tools.dxmt.translated_check --qualification .build/task8/qualification1.json --require-stage 1
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_*.py'
python3 -B tools/check_governance.py
git diff --check
```

The selected index names the device/native runs and `final7` CPU/ordering set.
Execution used the existing owned-run functions through the new adapters with
180-second per-fixture bounds. All original failed runs remain separately recorded.

Native pairing and CPU regression use independent copies of this candidate's
initialized synthetic device prefix. For native pairing only, disable the exact
optional XDG menu autorun entry, with before/after hashes; all process-exit checks
remain intact. Cold initialization's unsupported 32-bit helper and the original
XDG helper failure are preserved, not converted into passing observations.

Twelve completed earlier synthetic prefixes were removed after retaining their
registry/configuration bytes, full hashed inventories, raw logs and runtime
records. Completed CPU/ordering prefixes are similarly disposable after successful
assessment. The active seed, candidate and unique construction evidence remain.
Free space was about 22 GiB after cleanup; other tasks' files were untouched.

## Residual Risks

- No rendering/readback, presentation, Unity, Megabonk or Steam execution claim.
- No complete late-loaded module timeline; #10 retains that responsibility.
- AVX exposure, WOW64/cold 32-bit startup and XDG desktop integration remain unsupported or unqualified in this configuration.
- Finite tests do not prove arbitrary workload scale/concurrency or ordinary-user distribution. Existing signing is development authorization only.
- Private raw evidence and required retained dependency worktrees must remain available for subsequent stages; no private files are committed.

## Impact on Next Stage

Stage 2 starts from this combined candidate and its two selected corrections.
Reuse the device/native/CPU evidence while its inputs and claim scope remain valid.
Implement the approved buffer, texture, raster, depth/blend and compute readback
oracles and verify the real shader compiler/backend path. Revalidate only affected
boundaries, with full CPU checks again if a core dependency changes.

## Approval Request

Review the Stage 1 artifacts and verification results and approve Stage 2.
