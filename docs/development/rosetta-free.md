# Contributing to the Rosetta-free goal

Pear's final goal is an owned Windows Steam game experience on Apple Silicon
without Rosetta in any required host process or library. There is **no player-ready
Rosetta-free preview**. The [Rosetta Preview](../rosetta-preview.md) is a separate
interim path; improving it does not automatically qualify native execution.

## Start with a bounded task

Run the [portable first checks](getting-started.md) and read the [architecture](../architecture.md).
Inspect open Issues and their latest evidence before proposing overlapping work.
Examples of current engineering areas (Issue state remains authoritative):

| Area | Read first | Work tracking |
|---|---|---|
| Native host observations | [Host capability evidence](../host-capabilities.md) | [#10](https://github.com/postmelee/pear/issues/10) |
| Steam and game startup | [FEX integration](fex-host.md) | [#11](https://github.com/postmelee/pear/issues/11), [#46](https://github.com/postmelee/pear/issues/46) |
| Owned-game qualification | [Delivery criteria](../delivery-plan.md) | [#12](https://github.com/postmelee/pear/issues/12), [#16](https://github.com/postmelee/pear/issues/16) |
| Reproducible runtime assembly | [Source qualification](../source-qualification.md), [Wine](wine-host.md), [DXMT](dxmt-build.md) | [#13](https://github.com/postmelee/pear/issues/13) |
| Portable regression evidence | Existing test fixtures and [contracts](../runtime-contracts.md) | [#14](https://github.com/postmelee/pear/issues/14) |

Documentation, deterministic fixture checks and source inventory improvements can
help without a provisioned runtime or game. Agree scope before implementation;
an Issue on this list is not necessarily unassigned or a beginner task.

## Understand the prerequisites

Existing Wine/FEX reconstruction guides use exact source pins, patches, build
receipts and development-authorized host execution. Some inputs currently depend
on prepared local artifacts. A clean clone does not yet supply a complete,
reproducible player runtime. Follow each guide's declared prerequisites; record
missing inputs as blockers, and do not copy private signing data or authenticated
Steam prefixes into a PR to make it reproducible.

Retain upstream languages and review reuse before writing replacements. Rust
rewrites and performance tuning are not prerequisites for delivering the Preview.
FEX has its own contribution restrictions; follow the
[upstream policy section](../contributing.md#respect-upstream-projects).

## Produce evidence for your claim

A successful native build or fixture is useful evidence for that bounded result.
A Rosetta-free game claim also needs observed process and library architecture
through Steam startup, gameplay, exit and resume; see the
[architecture requirements](../architecture.md#rosetta-independence-evidence).
Preserve failed and unperformed checks. Gameplay, saves, audio and ordinary-user
distribution have separate gates in the [single delivery plan](../delivery-plan.md).

M1 is the technical milestone. The proposed M2 covers ordinary-user delivery;
independent R1 research is not a replacement prerequisite. Report progress against
the actual Issue rather than marking the entire native experience supported.
