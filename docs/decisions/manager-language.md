# Manager implementation language

Decision date: September 28, 2026. Scope: the production runtime manager and launch supervisor planned in [#9](https://github.com/postmelee/pear/issues/9). This is a development choice based on owned native fixtures, not a shipped manager or qualified runtime.

## Decision

Use **Rust for the new manager/supervisor**, with narrow reviewed C interfaces where the operating system requires them. Stage 4 verification passes under the explicit revised functional budget described below. Keep Swift as a viable alternative and evaluate the future Mac UI independently. Retain Wine, FEX and DXMT's upstream implementation languages. This decision imposes no project-wide Rust requirement and does not select a CPU translator or Cranelift backend.

The evidence supporting this choice is the tested implementation's lower build cost and lower recorded command RSS, combined with explicit ownership and a bounded native API surface. Rust also has a lower whole-manager invocation median in this run, but overlapping ranges and the fixed sampling order limit that evidence; it does not establish an intrinsic language-startup advantage. Swift has the smaller executable, no external package dependency and convenient macOS integration. Those are real benefits, but they do not outweigh the current Rust implementation's iteration cost and resource evidence for a separate supervisor in this comparison. Neither language removes the need to implement and verify process ownership correctly.

This selects the implementation direction for #9 within the declared fixture limits. The [clean-output reproduction](../../experiments/manager/results/reproduction.json) passed on the same Mac, including 119 contract tests, 60 experiment tests, two Rust fault tests and all 110 native corpus invocations. Actual runtime integration, independent-host verification and ordinary-user distribution remain gates. No language decision makes the currently blocked source/build candidate ready.

## Evidence and mandatory gates

The [frozen comparison plan](../../experiments/manager/comparison-plan.json) declares the release settings, sampling order, mandatory behavior and qualitative rubric. The [completed comparison](../../experiments/manager/results/comparison.json) records commands, source/binary identities, every sample and package inspection. Both candidates pass all 55 common cases in the standalone pre-check, before and after the completed comparison, and in the separately required final check (110 invocations per run), including input rejection, native execution observations, bounded output, owned cleanup and unrelated sentinel survival. Both retain the deliberately limited four-record fixture contract, not the entire production contract.

Two preliminary attempts failed mandatory observation checks with the original 300 ms negative-case budget. The first stopped before timing; the second retained all 82 samples but failed its final corpus. The [prior-attempt archive](../../experiments/manager/results/prior-comparison-attempts.json) preserves both reports and four unscored targeted diagnostic outcomes. None of their timings is pooled into the selected result, and their passing samples do not override their failed gates.

The [corrective input revision](../../experiments/manager/results/fixture-input-revision.json) records old/new hashes: both deliberate-timeout cases now use the existing ordinary-case 1,500 ms limit, and the intentional delay is 5,000 ms. Required traces, identity disappearance, reaping, sentinel survival, privacy and cleanup checks remain intact. The measured successful-launch workload still uses 1,500 ms; counts, order and rubric remain unchanged. This is a new functional-fixture input revision followed by a complete rebuild and comparison, not a byte-identical repetition of the failed attempts. Startup/deadline sensitivity was observed; the specific underlying OS cause remains unproven.

Independent code review also found a Rust pipe-setup failure path that could enter cleanup with a blocking descriptor. Stage 4 fixes it by evaluating both setup calls and closing both read ends on either failure. Two owned fault tests cover both positions, real pipe-holding descendants, closed descriptors, bounded completion and sentinel survival. The fix and the subsequent full reruns are evidence of a corrected path, not proof that Rust automatically prevents lifecycle bugs.

A later final baseline run still failed Rust `observer_gap` at 1,500 ms: timeout, SIGKILL, no output or child trace, with owned cleanup and the unrelated sentinel check passing. The [failed final corpus](../../experiments/manager/results/final-corpus-before-revision2.json) and its [earlier completed comparison](../../experiments/manager/results/comparison-before-revision2.json) remain separate immutable historical evidence.

The [second input revision](../../experiments/manager/results/fixture-input-revision2.json) separates ordinary functional conformance (5,000 ms within the existing CLI limit) from deliberate-timeout fixtures (1,500 ms) and scored launches (unchanged 1,500 ms). Cleanup remains bounded at two seconds and the outer harness at ten seconds. It archives the earlier completed comparison and failed final corpus byte-for-byte. Passing this revised suite establishes only those declared functional limits; it cannot guarantee startup within 1,500 ms or erase the earlier failure.

The [bounded startup diagnostic](../../experiments/manager/results/startup-diagnostics-before-revision2.json) passed 16 invocations without reproducing that failure. One sampled slow invocation showed pre-main dyld remote-notification work. Apple's published [dyld responder](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/dyld/RemoteNotificationResponder.cpp#L39) and [main-entry path](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/dyld/dyldMain.cpp#L998) explain the corresponding synchronous notification/acknowledgement mechanism. That source revision has not been matched to the installed dyld binary. Sampling can perturb execution; the monitor identity, its contribution to elapsed time and the cause of the earlier timeout remain unproven. No monitor, execution permission or security protection was disabled.

## Measurements

Recorded host: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), AC power. Tool inputs: Xcode 26.6, SDK 26.5, Apple Swift 6.3.3, Rust/Cargo 1.94.1. These are observed experiment inputs, not Pear release requirements.

Values are median (minimum–maximum). Each candidate has three clean-output builds, three native-module comment-edit rebuilds, five retained unscored warmups and 30 recorded manager invocations. All 82 rows of the completed run remain in the result; no unfavorable value is removed.

| Metric | Rust | Swift |
|---|---|---|
| Clean build, 3 samples | 3.670 s (3.060–5.355) | 10.659 s (8.265–12.938) |
| Clean RSS accounting | 170.688 MiB (170.516–170.766) | 333.781 MiB (331.250–345.078) |
| Incremental build, 3 samples | 5.918 s (3.918–6.539) | 7.125 s (6.519–14.824) |
| Incremental RSS accounting | 167.984 MiB (164.453–170.516) | 242.984 MiB (239.297–243.016) |
| Manager invocation, 30 samples | 279.867 ms (207.455–502.431) | 303.175 ms (232.902–657.044) |
| Launch RSS accounting | 2.000 MiB (1.969–2.047) | 6.734 MiB (6.688–6.797) |
| Standalone manager executable | 544,816 bytes | 246,608 bytes |

An invocation covers manager start through validation, child launch and cleanup. The copied native child and filesystem activity are part of that workload. It is not pure language startup, frame time or gameplay latency. The observed launch median difference is 23.308 ms; overlapping ranges, fixed pairing and 1 ms polling prevent a general language-startup ranking.

RSS comes from Darwin `wait4` accounting for the waited command. It is not an independently sampled process-tree peak, and build-driver/compiler attribution is not separated. Clean outputs retain OS, SDK and registry caches. Incremental edits measure a predetermined comment change's invalidation/recompilation cost. Launch pairs always run Rust then Swift rather than being randomized or counterbalanced. Known parallel heavy work was excluded, but general desktop background activity and thermal conditions were not controlled. Detailed low-power-mode settings and numeric thermal limits were unavailable in the recorded snapshots. Timing varies substantially between retained runs, and the final Rust incremental median exceeds its clean-build median. These observations limit interpretation of three-sample build results; no general claim that incremental compilation is faster or that a language is intrinsically faster follows. No power, temperature, game FPS or tail percentile is inferred.

Rust's locked `libc` input is 821,883 compressed bytes and 4,372,804 extracted bytes, with no active transitive crate dependency. It is a build input, not an additional shipped archive. Swift has no external package cache. System libraries, shared C fixtures, SDK and toolchain sizes are separate from the manager executable; full toolchain sizes and a signed app bundle were not measured. The raw result records the corresponding payload categories and exact digest.

## Packaging, native interfaces and maintenance

| Consideration | Evidence and implication |
|---|---|
| Native and package inspection | Both measured managers have only an ARM64 slice, macOS 26.0 deployment metadata and SDK 26.5 metadata. Their linker-generated ad-hoc signatures pass read-only strict verification. Neither has a Developer ID team identity or a qualified distribution bundle. |
| Dynamic dependencies | Rust links system libSystem/libiconv. Swift links system Foundation, Objective-C and Swift libraries; its inspected rpath is `@loader_path`. No third-party dynamic library was found in either inspected manager. The smaller Swift file partly depends on system code; file size alone is not total runtime cost. |
| Build prerequisites | Swift uses the Apple toolchain already needed by Pear's macOS work. Rust adds the recorded compiler/Cargo toolchain and one reviewed `libc` crate under MIT OR Apache-2.0. This contributor/dependency cost is accepted for the manager, not dismissed as zero. |
| Ownership and supervision | Rust's standard ownership types support explicit resource lifetimes, but group signaling, unreaped-leader identity, descriptor modes and cleanup deadlines remain manual obligations. Swift's classes/defer and `posix_spawn` also support the required design. Both passed the final common corpus; neither design is automatically correct. |
| C ABI | Both use CommonCrypto/libproc and the same narrow process-identity bridge. Rust has explicit unsafe/extern boundaries and reviewed `pre_exec` calls. Swift's current manual `@_silgen_name` declarations need header-checked imports or an equivalent tested ABI boundary for production. Rust's manual declarations also need ABI tests. |
| Parsing and diagnostics | Both currently maintain strict custom JSON parsing and a fixed fixture subset. Production evolution needs shared adversarial parity tests, bounded typed errors and useful local diagnostics without emitting secrets. Existing generic errors are insufficient for the final user experience. |
| Contribution model | Preserve the common language-neutral contracts, reproduction commands and process protocol. Language familiarity is a contributor consideration, not an assumed preference of all users. Future UI work need not use Rust. |

Read-only signature verification is not Developer ID signing, provisioning, notarization, an app-bundle test or minimum-OS/independent-Mac qualification. The inspection found no candidate-specific distribution blocker, but it did not establish a release path for either candidate.

## Production handoff

[#9](https://github.com/postmelee/pear/issues/9) owns spawning, reaping, termination and mutable state. It must implement the full required [runtime contracts](../runtime-contracts.md), independent trust policy, immutable runtime activation, compatibility-scoped prefixes, safe cache/save boundaries and recoverable version changes. It must close the pathname-execution race through actual immutable ownership and at-use validation, cover cancellation and manager crashes, and establish ownership of real detached helpers without signaling unrelated processes. Rust `unsafe`/FFI and any fork/pre-exec behavior need documented threading, lifetime, error and unwinding contracts. Add cold-start/deadline tests across relevant supported environments; the corrected fixture budget is not an ordinary-user reliability guarantee.

[#10](https://github.com/postmelee/pear/issues/10) owns observations rather than child management. Replace fixture flags with a causal observer-ready acknowledgement for the exact launch request, monotonic producer sequence evidence, process-creation identities and required process/module coverage. Record late attachment, missing helpers, dropped events and inaccessible modules as gaps. A native launcher or ARM64 file cannot prove every required host process avoided Rosetta. The observer must not reap, terminate or mutate the supervisor's children or prefixes. If the selected observation API requires synchronous acknowledgements, keep that path bounded, move expensive analysis off the acknowledgement path, and measure observer-induced startup/runtime effects without silently dropping required coverage.

Full contract execution, Steam sign-in/install, Wine/FEX/DXMT integration, real game behavior, signed distribution and clean external-Mac verification remain unimplemented or unqualified by these experiments. No prototype is copied into a production `manager/` directory by this decision.

## Alternative and reconsideration

Swift remains the alternative if measured production integration, maintainers' capacity, a simpler tested native-API boundary or release packaging evidence outweigh the present supervisor benefits. Revisit the choice if representative long-running supervision, cancellation, real helper coverage or distribution tests reveal a Rust-specific cost; if the selected toolchain/dependency burden becomes unjustified; or if the final reproduction cannot uphold the functional evidence. Reconsideration needs comparable behavior and a reviewed task, not an automatic rewrite based on a microbenchmark.


## Clean-output reproduction scope

The [Stage 5 report](../../mydocs/working/task_m1_3_stage5.md) records a fresh virtual environment from five reviewed, hash-verified cached wheels, new locked/offline native builds and semantic agreement with the final Stage 4 corpus. Installed toolchains, SDK, verified Cargo sources and machine caches were reused; no dependency download was requested. The 82 timing rows were retained and checked, not repeated or pooled with this functional run.

Both rebuilt manager hashes differ from the Stage 4 measured payloads. Rust remains 544,816 bytes; Swift is 246,416 bytes versus 246,608 in the measured build. Relocated inputs/build outputs, compiler metadata, linker UUIDs and ad-hoc signatures can affect bytes, but the contribution of each was not measured. This establishes matching declared behavior on these exact recorded payloads, not a byte-reproducible toolchain or signature claim. The earlier startup failure, normal distribution and production-ownership gaps remain open.
