# Milestones and implementation plan

Planning baseline: September 27, 2026. All implementation and research issues below are planned work; none establishes a working Rosetta-free runtime.

## Milestones

- **M1 — Megabonk on Apple Silicon without Rosetta:** the first product milestone. Its 16 issues cover a source-buildable runtime, substantial host ports where needed, correctness tests, Steam/game integration, and reproducible qualification.
- **R1 — Evaluate an independent Pear CPU translator:** five conditional research issues. This track does not block M1. A well-supported decision to retain FEX can complete the research without delivering a new translator.

See the repository's [GitHub milestones](https://github.com/postmelee/pear/milestones) and the [architecture](architecture.md). No delivery dates or staffing estimates are asserted before source and host-capability gates are resolved.

## First-milestone completion

M1 requires all of the following on an explicitly named Mac/macOS/game/runtime configuration:

1. A reproducible build/setup from identifiable source, documented patches, and a complete runtime lock.
2. Normal macOS protections and a documented authorized signing/provisioning path. Development-profile execution can qualify this technical milestone; unrestricted end-user distribution is a separate release claim.
3. No Rosetta execution in any required host process or native dependency, including Steam helpers; guest x64 code must use the selected CPU translator.
4. Passing required CPU/API/graphics fixtures, normal Steam launch, input/audio, local saving, clean exit, and reload.
5. At least 20 minutes of active gameplay and a report of frame-time behavior, failures, tested features, and known limitations.
6. Independent or second-clean-environment reproduction. One configuration does not imply all-Mac support.

A source or entitlement gap can require a substantial port or an architecture change. Record that decision explicitly; do not bypass the requirement with undocumented binary dependencies. Failed capability gates remain failed even if other preparatory tasks are completed.

Final evidence must refer to one matching runtime artifact and configuration. If packaging, signing, components, the profile, game, or Steam changes in a way relevant to execution, requalify the affected tests before closing M1.

## Dependency order

Source qualification and host probes start first. Contracts and language evaluation can run in parallel. Wine host bring-up precedes FEX integration; CPU and graphics tests precede Steam/game qualification. The supervisor and evidence collector can be developed against redistributable fixtures in parallel. Final qualification combines all required results.

Dependencies below are acceptance dependencies: preparatory source reading and fixture development can start earlier, but downstream issues cannot be marked complete without their required evidence. The code and source manifest remain the authoritative version record; changing a web page or label does not change support status.

## Core implementation backlog

| ID | Issue | Acceptance dependencies |
|---|---|---|
| P01 | [#1 Qualify source availability and pin the runtime toolchain](https://github.com/postmelee/pear/issues/1) | None |
| P02 | [#2 Probe macOS ABI, memory, JIT and signing capabilities](https://github.com/postmelee/pear/issues/2) | None |
| P03 | [#3 Define runtime contracts and choose the manager language](https://github.com/postmelee/pear/issues/3) | None |
| P04 | [#4 Bring up the ARM64 Wine host and macOS ABI boundary](https://github.com/postmelee/pear/issues/4) | P01, P02 |
| P05 | [#5 Port FEX Wine host services to Darwin and integrate its CPU modules](https://github.com/postmelee/pear/issues/5) | P01, P02, P04 |
| P06 | [#6 Qualify CPU semantics and the Wine translation boundary](https://github.com/postmelee/pear/issues/6) | P05 |
| P07 | [#7 Reproduce the ARM64EC DXMT and ARM64 Metal bridge build](https://github.com/postmelee/pear/issues/7) | P01, P04 |
| P08 | [#8 Qualify Direct3D 11 through the native Metal path](https://github.com/postmelee/pear/issues/8) | P06, P07 |
| P09 | [#9 Implement the native runtime supervisor and Megabonk profile](https://github.com/postmelee/pear/issues/9) | P03 |
| P10 | [#10 Collect complete process and module evidence of Rosetta independence](https://github.com/postmelee/pear/issues/10) | P02, P03 |
| P11 | [#11 Validate Windows Steam and its helper architecture requirements](https://github.com/postmelee/pear/issues/11) | P06, P08, P09, P10 |
| P12 | [#12 Qualify Megabonk gameplay, input, audio and save/relaunch behavior](https://github.com/postmelee/pear/issues/12) | P11 |
| P13 | [#13 Assemble and reproduce the signed Pear runtime candidate](https://github.com/postmelee/pear/issues/13) | P01, P02, P03, P06, P08, P09 |
| P14 | [#14 Add regression CI and a maintained upstream patch workflow](https://github.com/postmelee/pear/issues/14) | P03, P06, P08, P09, P10, P13 |
| P15 | [#15 Characterize frame times, stability and power under controlled conditions](https://github.com/postmelee/pear/issues/15) | P12, P13 |
| P16 | [#16 Publish the first Rosetta-free Megabonk qualification record](https://github.com/postmelee/pear/issues/16) | P10, P12, P13, P14, P15 |

## Independent CPU-engine research

| ID | Issue | Acceptance dependencies |
|---|---|---|
| E01 | [#17 Define the CPU-engine hypothesis and differential semantics corpus](https://github.com/postmelee/pear/issues/17) | None |
| E02 | [#18 Compare Cranelift with a reference CPU-code backend](https://github.com/postmelee/pear/issues/18) | E01 |
| E03 | [#19 Test the experimental CPU runtime on signed macOS](https://github.com/postmelee/pear/issues/19) | E02 |
| E04 | [#20 Integrate the experimental CPU module with Wine](https://github.com/postmelee/pear/issues/20) | E03, P06 |
| E05 | [#21 Decide whether to adopt a Pear CPU translator](https://github.com/postmelee/pear/issues/21) | E04, P16 |

E01 and E02 must record an explicit continuation decision. If the hypothesis or backend comparison does not justify more work, close later conditional experiments as **not planned**, state the evidence, and retain FEX. Those closures are not successful implementation results. Adopting a replacement requires the shared Wine/game qualification, including the P16 reference baseline.

## Issue and evidence conventions

- Each issue has a problem statement, bounded scope, acceptance checklist, dependency links, and supporting technical documents.
- Qualify an exact component set; do not close an issue based on an unpinned upstream demo.
- Record unsupported and unobserved cases explicitly. Correctness failures on the required path block qualification.
- Keep test fixtures redistributable. Game files, authenticated Steam prefixes, and private save data stay outside Git.
- Attribute reused code and preserve license and upstream contribution-policy boundaries.
- Code patches stay reviewable and rebased. Build success, runtime success, game qualification, and general distribution are distinct outcomes.

Detailed issue content is stored in [backlog.json](planning/backlog.json). Stable P/E identifiers preserve the plan's meaning independently of GitHub issue numbering. Published issue and milestone identifiers are recorded in [github-map.json](planning/github-map.json).
