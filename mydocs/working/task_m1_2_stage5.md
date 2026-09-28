# Task #2 — Stage 5 report

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Implementation plan: [task_m1_2_impl.md](../plans/task_m1_2_impl.md)
Stage: 5 — Reproduction and capability decision
Date: September 28, 2026

## Stage Purpose

Reproduce the complete native host suite from fresh build outputs and decide whether the bounded Issue #2 acceptance criteria pass. The maintainer explicitly approved this stage after Stage 4. The result is a host capability decision for a declared development configuration, not a working Windows runtime or game.

## Artifacts

| File | Change Summary |
|---|---|
| [Stage 5 evidence](task_m1_2_stage5_observations.json) | Fresh build, 38 source/test hashes, five binary inspections, full signed results, semantic comparisons and platform protections |
| [Contributor guide](../../docs/host-capabilities.md) | Reproduction recipe, passing host configuration and remaining qualification boundaries |
| [Historical host audit](../../docs/research/macos-runtime-audit.md) and [documentation index](../../docs/README.md) | Dated evidence link and updated guide description |
| [Final report](../report/task_m1_2_report.md) | All three Issue acceptance criteria mapped to evidence and follow-up dependencies |
| Implementation plan and [daily board](../orders/20260928.md) | Stage 5 approval, concrete commands and completion status |

## Body Change Scope / Lossless Preservation

No implementation or test source changed in Stage 5. All 38 hashes match Stage 4 commit `7fb66dd892ddbe9d44e0e853c3ab0e5eff446959`. With no owned probe still running, the previous ignored output directory was moved to a dated sibling and preserved. `make` started with no `.build/host-probe` directory and built all five targets. Every rebuilt binary's SHA-256 matches Stage 4 before identity signing. Fresh signed bundles bind their new signatures to those exact inputs. Their signature bytes are not required to match earlier bundles.

The disassembly also matches the reviewed Stage 4 output exactly. Process and ABI records match previous semantics after excluding execution timing and the permitted variation in baseline reordering counts. Original reports remain unchanged. The historical research gained only a dated follow-up; no old finding was rewritten. All documents use the approved locations. Raw profiles, identity/device strings, generated bundles and private local results remain outside Git.

## Verification Results

After preserving earlier outputs, the implementation plan's commands were run:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
.build/host-probe/pear-host-probe > .build/host-probe/stage5-observations.json
.build/host-probe/pear-baseline-probe > .build/host-probe/stage5-baseline.json
xcrun llvm-objdump --disassemble --no-show-raw-insn .build/host-probe/pear-process-probe
python3 host/probe/hardened_baseline.py > .build/host-probe/stage5-hardened.json
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" > .build/host-probe/stage5-process.json
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" --suite abi > .build/host-probe/stage5-abi.json
git diff --check
```

| Check | Result |
|---|---|
| Declared environment | Apple M4 Pro; macOS 26.5.2 / 25F84; Apple clang 21.0.0 (`clang-2100.1.1.101`); SDK 26.5; Python 3.14.4; Make 3.81 |
| Fresh build | Passed; five ARM64-only outputs; warnings treated as errors; all pre-signing hashes and inspected SDK contract hashes match Stage 4 |
| Complete regression suite | `Ran 126 tests in 14.218s` / `OK` |
| Ordinary observations and baseline | Native current-process translation query false; memory/protection/JIT passed; baseline low-address unavailability retained |
| Hardened controls | Positive JIT returned 42; matched negative retained failed MAP_JIT allocation, errno 22 and baseline CLI exit 1; paired assessment passed |
| Provisioning/signing | Real unexpired profile, registered device, matching development certificate, exact effective claims and strict signatures passed again |
| Process suite | All four layout/page-mode assessments passed; independent middle-page protection, reserved recommit and expected faults passed in 4 KiB modes |
| ABI suite | All four assessments passed; each completed 64 roundtrips, 32 nested callbacks, 16 injected error returns and both signal entry cases with restoration |
| Per-thread policy | Every tested worker explicitly initialized, enabled, restored and joined; no policy getter or inherited state assumed |
| Lifecycle | 4 baseline + 8 hardened + 28 process + 24 ABI = 64 dedicated children reaped; no owned probe left running; fixture children are separate |
| Protections | SIP and Gatekeeper enabled after execution; no protection changes made |
| Evidence hygiene | Source/binary/signature bindings, numeric results, redaction and local document links checked; diff hygiene passed |

The CPU-brand query was denied inside the tool sandbox. That result is retained separately from the successful ordinary-host query; it was not coerced into a hardware value.

Fresh message-passing results:

| Configuration | Baseline trials / forbidden observations | Enabled trials / forbidden observations |
|---|---|---|
| Standard / default pages | 10,000 / 3 | 10,000 / 0 |
| Standard / 4 KiB pages | 10,000 / 6 | 10,000 / 0 |
| Emulation / default pages | 10,000 / 0 | 10,000 / 0 |
| Emulation / 4 KiB pages | 10,000 / 0 | 10,000 / 0 |

Forbidden means flag=1 with data=0 after writer data=1 then flag=1. Baseline counts are observations, not required positive controls. The enabled total is 0/40,000, which is finite evidence and not a universal ordering proof.

## Capability Decision

Issue #2's bounded host gate passes on the declared configuration using the authorized development path. The selected layout uses `-Wl,-x86_64_layout_emulation,-pagezero_size,0x10000`, retains a protected 64 KiB null region, and requests 4 KiB user pages; kernel pages remain 16 KiB. Low mapping at `0x20000000`, memory/protection/recommit, JIT publication and the finite ABI/thread cases pass. Standard-layout low mapping remains unavailable and is not the selected prerequisite.

The [final report](../report/task_m1_2_report.md#verification-results) maps the three Issue criteria individually. Completion of this host task does not complete G0 source qualification, M1, or general distribution. Issue #2 remains open pending review/merge; its status is not changed by this report.

## Residual Risks

- This is fresh-output reproduction on the same host and installed toolchain, not a clean-machine or independent-tester result.
- Controlled nesting, SIGUSR1 and explicit error returns do not qualify Windows SEH, general unwinding, arbitrary callbacks or every asynchronous interruption point.
- Accepted policy requests plus finite litmus behavior do not expose a hardware mode bit or prove the translator's memory model.
- The tested low address and reserved middle-page replacement do not establish Wine's complete address-space contract or physical-memory reclamation.
- Development registration, current authorization and local signatures without timestamps do not establish notarization or an ordinary-user installation path.
- Wine/FEX/DXMT integration, the complete game process tree, Steam, gameplay, saves and performance remain untested by this task.

## Impact on Next Stage

All five planned stages are complete. Preserve the committed evidence and local signed artifacts for review. Subsequent runtime integration can use this tested host boundary, but must retain its own source, ABI, CPU, graphics and full-process evidence gates. No new Issue is started here.

## Approval Request

Review the final report and the Open PR prepared under `task-final-report`, then approve merge. Do not close the Issue or remove its active review worktree before approval or a confirmed merge.
