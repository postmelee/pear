# Pear roadmap and delivery plan

Planning baseline: September 28, 2026. This is Pear's canonical roadmap and defines intended outcomes and completion criteria. It does not certify a Rosetta-free runtime or an available end-user release.

The [official documentation index](README.md) identifies the source for each kind of information. Current task state belongs in [GitHub Issues](https://github.com/postmelee/pear/issues); actual execution claims require matching qualification records. Dated [local experiments](research/local-evidence.md) and [host capability evidence](host-capabilities.md) retain their recorded limits. Issue-specific plans, approvals and reports belong in [mydocs](../mydocs/manual/document_structure_guide.md), rather than serving as a second roadmap. See the [contributor guide](contributing.md) for participation and review.

## Product phases

The first user goal is to download Pear on a supported Apple Silicon Mac, sign into official Steam, install an owned Windows copy of Megabonk, and play, save, quit and resume without Rosetta. Every required host process and native library must meet that requirement; a native launcher alone cannot qualify the experience.

| Phase | Intended user capability | Completion focus |
|---|---|---|
| 1 - Megabonk for ordinary users | Download and install Pear, complete official Steam sign-in and owned-game installation, then play, save and resume with understandable recovery. | Qualified runtime plus ordinary-user execution, application, installation, packaging and recovery evidence on a declared supported configuration. M1 and proposed M2 describe the technical and user-delivery parts. |
| 2 - Versioned game profiles | Extend the verified approach to additional games through a versioned Game Profile Spec. | Reusable declarative profiles with explicit runtime compatibility, bounded operations, validation, evidence and known limitations. |
| 3 - Steam library and Install/Play | Find owned games and see whether the user's environment matches a verified configuration before choosing Install or Play. | Steam library integration and automatic comparison of host, game, runtime and profile identities with verification records; unknown and unsupported combinations remain explicit. |
| 4 - Community-maintained compatibility | Contribute profiles and reproducible results, discover reviewed support, and submit requests, votes and reports. | GitHub PR review, automated schema and redistributable fixture checks, real-game testing by game owners, a reviewed profile registry and a community compatibility database. Votes express demand; matching evidence establishes support. |
| 5 - Sustainable platform | Use a maintained experience approaching Proton for macOS as compatibility grows. | Reproducible runtime releases, upstream maintenance, reviewed profiles, regression evidence, updates and recovery that remain manageable across supported games and Mac configurations. |

Phases describe expanding user capabilities, not a requirement to postpone useful groundwork. Profile design and validation can begin in Phase 1. [#3](https://github.com/postmelee/pear/issues/3) owns actual runtime/profile contracts and the manager-language decision; this roadmap does not settle either. Later phases require their own bounded tasks and acceptance criteria before implementation. No delivery dates, all-game support or performance advantage are implied.

## Milestones

- **M1 — Megabonk on Apple Silicon without Rosetta:** the existing technical runtime milestone. Its 16 implementation issues cover a source-buildable runtime, necessary host ports, correctness tests, Steam/game integration and reproducible qualification. Authorized development-profile execution may qualify this technical scope; an ordinary-user application requires additional evidence.
- **M2 — Install Pear and play Megabonk without Rosetta (proposed):** the ordinary-user portion of Phase 1, including the application, runtime installation, official Steam flow, recovery and distribution. M2 and U01-U07 below are unregistered planning candidates as of this baseline, with no assigned GitHub identities.
- **R1 — Evaluate an independent Pear CPU translator:** the existing five conditional research issues. R1 does not block M1 or proposed M2. A supported decision to retain FEX can complete the research without delivering a new translator.

Existing M1/R1 names and Issue identities remain unchanged. See the [registered GitHub milestones](https://github.com/postmelee/pear/milestones) and [runtime architecture](architecture.md). M1 completion contributes to Phase 1; it does not complete the ordinary-user outcome by itself.

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

Source qualification and host probes come first. Contracts and language evaluation can run in parallel. Wine host bring-up precedes FEX integration; CPU and graphics tests precede Steam/game qualification. The supervisor, evidence collector and application can be developed against redistributable fixtures in parallel. Final qualification combines all required results.

Dependencies below are acceptance dependencies: preparatory source reading and fixture development can start earlier, but downstream issues cannot be marked complete without their required evidence. The code and source manifest remain the authoritative version record; changing a web page or label does not change support status. [#1](https://github.com/postmelee/pear/issues/1) owns source qualification and runtime component pins.

Source completeness and ordinary-user execution permissions are early Phase 1 blockers. UI fixtures cannot satisfy them. The Wine/FEX/DXMT direction remains the primary candidate; a new CPU translator or GPTK adoption is not a Phase 1 prerequisite. Standalone Metal Shader Converter or D3DMetal experiments remain deferred unless a concrete graphics blocker or separately approved native-shader implementation calls for them.

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

## Proposed M2 - Ordinary-user Megabonk experience

M2 and U01-U07 require separate milestone/Issue registration through the [task registration procedure](../mydocs/skills/task-register/SKILL.md). Registration is follow-up work, excluded from the roadmap task [#25](https://github.com/postmelee/pear/issues/25). The U identifiers are planning references only; they have no Issue numbers or completion status. When registered, record their actual identities and links without changing the existing P/E mappings.

### First-user flow

1. Download the signed Pear release candidate for the declared supported Mac/macOS configuration, install it and open it through normal macOS launch behavior.
2. Check host compatibility and available space, explain the runtime download, and install one verified runtime artifact. Explain unsupported configurations without presenting them as compatible.
3. Prepare an isolated environment and open the official Steam client. The user signs in directly with Steam, including Steam Guard or QR when offered. Pear does not collect the Steam password or replace Steam authentication.
4. Install the user's owned Windows Megabonk through Steam, identified by App ID `3405340`, and use the qualified normal Steam launch path.
5. Choose Play, apply the verified profile and supervise Pear's own runtime processes. Present actionable failures and optional redacted diagnostics without requiring routine users to understand backend details.
6. Play, save, exit and resume. Preserve current data before restore or migration, provide local backups and compatible runtime recovery, and identify any unverified Steam Cloud behavior.
7. Reuse the verified installation on later launches and recover from interrupted setup, download/update failures or expired Steam sessions. Requalify affected evidence when an update changes the execution path.

The initial integration uses official Windows Steam in the candidate ARM64 Wine/FEX runtime. A native macOS Steam bridge requires a separate reviewed architecture decision and equivalent qualification.

### Proposed work and acceptance dependencies

| ID | Proposed work | Acceptance dependencies |
|---|---|---|
| U01 | Qualify runtime execution for ordinary end users | P02 (#2), P13 (#13) |
| U02 | Build the native Pear application and setup flow | P03 (#3), P09 (#9) |
| U03 | Install and manage verified runtime versions | P03 (#3), P13 (#13), U01 |
| U04 | Integrate Steam setup, sign-in, game installation and launch | P11 (#11), U02, U03 |
| U05 | Preserve saves and provide recovery | P09 (#9), P12 (#12), U03 |
| U06 | Package the installable Pear release candidate | U01-U05, P14 (#14) |
| U07 | Qualify the complete first-user Megabonk experience | P16 (#16), U06 |

### U01 - Ordinary-user execution

Demonstrate the actual signed runtime on a clean supported Mac whose user needs no Xcode, developer account, supplied development profile or disabled security protection. Record the authorization/signing route and its limits. Permission investigation may proceed early; final qualification depends on the P13 artifact. The development-provisioned [host results](host-capabilities.md) do not establish this distribution outcome.

### U02 - Application and setup states

Build a native application using the shared manager contract, with states for unsupported host, missing runtime, installation, Steam sign-in required, game missing, ready, running and recoverable failure. Verify keyboard and VoiceOver operation, localization-ready strings and redacted diagnostic export. Fixture processes can validate behavior before the runtime is ready; fixture success must not appear as game support.

### U03 - Runtime installation and versions

Verify artifact identity, stage installation and activate it atomically. Test interrupted downloads, cancellation, insufficient storage, corrupt artifacts, concurrent launch/update and recovery. Keep runtime payloads immutable and preserve a compatible known-working prefix/runtime combination. Profiles select approved declarative operations rather than downloaded shell scripts. Follow the contracts defined through P03 instead of introducing another profile format.

### U04 - Official Steam and owned-game flow

Exercise official Steam installation, updates, sign-in, owned-game download and normal launch. Handle absent ownership, expired sessions, client updates and launch failure. Preserve Steam ownership and API behavior: no authentication stubs, client bypass or shipped `steam_appid.txt` shortcut. Include every required Steam helper in the process/module architecture evidence.

### U05 - Save preservation and recovery

Implement versioned local save/settings backups, verified restoration and compatible runtime rollback. Restore only after relevant processes stop, preserving current data before replacement. Verify Steam Cloud behavior before claiming it and disclose untested conflict cases. Uninstallation preserves saves unless the user deliberately removes them.

### U06 - Installable release candidate

Package the signed/notarized application and compatible runtime delivery with component identities, source references, notices, and tested installation, update, removal and diagnostic instructions. The supported user flow needs no Terminal commands. Resolve Pear's own license and component distribution obligations before public release. Packaging alone does not qualify support or authorize a repository visibility change.

### U07 - End-to-end qualification

On a second clean supported setup, complete the exact download-to-resume flow, at least 20 minutes of active gameplay, save/quit/reload and recovery exercises. Verify no required host process or native module uses Rosetta during Steam startup, game startup, play, shutdown or relaunch. Record app, runtime artifact/lock, profile, Steam, game, hardware, OS, settings, date and known limitations. Requalify affected tests if the released artifact differs from the earlier M1 configuration.

### Phase 1 release gates

Phase 1 requires a source-reproducible runtime, authorized ordinary-user execution under normal macOS protections, the complete official Steam and owned-game flow, and tested recovery that preserves user data. M1 CPU/API/graphics/game requirements must pass on the final application/runtime configuration, with no unexplained required process/module observation gaps. Qualification names the tested configurations and limitations; broader support and comparative performance or power claims require their own evidence.

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
- Automated schema and fixture checks establish only their tested properties. Game owners must supply real execution evidence before a reviewed profile can claim game support.

The original P/E issue definitions are retained in [backlog.json](planning/backlog.json); [GitHub Issues](https://github.com/postmelee/pear/issues) hold live task status. Stable P/E identifiers preserve the plan's meaning independently of GitHub issue numbering. Registered issue and milestone identifiers are recorded in [github-map.json](planning/github-map.json); proposed M2/U work is documented above pending registration.

Discussions, if enabled, are for requests, votes, questions and proposals; adopted decisions must be reflected in the official documents and linked Issues. The Wiki, if used initially, should guide readers to those sources rather than maintain separate rules. Neither surface changes qualification status or substitutes for reviewed evidence.
