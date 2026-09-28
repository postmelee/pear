# Host capability diagnostics

The host tools collect native macOS observations and execute isolated baseline, process/memory/JIT and ABI/thread trials for [Issue #2](https://github.com/postmelee/pear/issues/2). They are development tools; runtime and game qualification remain unassessed.

`pear-host-probe` only observes its own process. `pear-baseline-probe` supervises four disposable `pear-probe-child` processes, including a fixed ARM64 JIT leaf. Neither tool enters the foreign x18 ABI, changes process page geometry, enables a thread memory-order policy, or launches Steam. Finding an API symbol does not establish permission to call it or prove its behavior.

The separate `pear-process-probe` and `pear-process-probe-layout` executables can self-spawn native trial children with an authorized 4 KiB page mode. Run their restricted tests through `provisioned_probe.py`, which validates the actual local profile, signs fresh copies and checks effective claims before launch. The optional `--suite abi` adds isolated x18 and thread-policy trials. Both suites use fixed native test code and do not execute game code.

## Build and run

From the repository root on an Apple Silicon Mac with Apple clang, the macOS SDK, Make and Python 3 available:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
lipo -archs .build/host-probe/pear-host-probe
.build/host-probe/pear-host-probe > .build/host-probe/local-observations.json
python3 -m json.tool .build/host-probe/local-observations.json
lipo -archs .build/host-probe/pear-baseline-probe
lipo -archs .build/host-probe/pear-probe-child
.build/host-probe/pear-baseline-probe > .build/host-probe/local-baseline.json
python3 -m json.tool .build/host-probe/local-baseline.json
```

Builds and unreviewed local observations stay under ignored `.build/`. These baseline builds use system libraries and require no configured developer signing identity. Their ad-hoc execution does not establish permission for restricted ABI operations or runtime distribution. Keep the baseline supervisor and its companion child in the same directory. The baseline run intentionally causes one protected-write fault; the child suppresses core dumps, but macOS may still record crash diagnostics.

The initial development environment is Apple clang 21 with macOS SDK 26.5 on M4 Pro/macOS 26.5.2. The diagnostic's build target is not a declaration of Pear's eventual minimum supported macOS or chip.

## Interpret the observation report

The versioned JSON report is scoped to the current diagnostic process. Observations identify a value or explain why it could not be obtained. Error domain and numeric code are preserved when an operating-system request fails.

| Observation | Meaning | Limit |
|---|---|---|
| Executable architecture | The running diagnostic's Mach-O architecture | Does not describe Wine, Steam or a future child process |
| Process translation query | The diagnostic's own `sysctl.proc_translated` result | A denied or missing query remains unavailable; it is not converted to `false` |
| OS/build and page size | Values visible to this process | Sandbox restrictions and a different process configuration may change observations |
| Runtime symbol presence | Whether selected host APIs can be resolved dynamically | Does not call them, validate permission, or verify semantics |
| Signature category | A coarse category derived from the current executable | Does not validate a distribution identity, provisioning profile, entitlement authorization or notarization |
| Capability execution and qualification | Explicitly not run or not assessed | No whole-runtime or Megabonk support claim is made |

`observed` means that an observation succeeded. `unavailable` means that the requested information could not be obtained in this context. `failed` identifies an invalid or failed observation operation. These observation statuses are distinct from the baseline execution statuses below. An ordinary diagnostic exit does not mean that every observation is available.

The report deliberately omits identity names, account information, hostnames, usernames, private signing material and absolute private paths. Review result files before sharing them; other tools run alongside the probe may have different output policies.

## Test boundary

The tests combine a real native run with a separately built fixture that injects observation results into the production collection and JSON-writing code. The shipped diagnostic has no fixture mode. Synthetic success cannot qualify the host.

Tests cover denied translation queries, absent symbols, unavailable signature information, unexpected architecture input, JSON escaping, and invalid CLI arguments. A denied query must remain unavailable instead of becoming a negative translation result. Missing APIs must remain observations rather than positive execution results.

The baseline tests use actual disposable children to exercise deadlines, nonzero exits, signals, invalid packets, output limits, inherited descriptors and descendant-held pipes. They check direct-child reaping, descriptor counts and survival of an unrelated sentinel process. Separate fixtures verify that a wrong JIT return value, incomplete pre-fault evidence or cleanup failure cannot become a passing result. Fixture success is distinct from the native baseline run.

## Initial observations

The September 27, 2026 run on the development Mac produced the following observations. The [saved evidence](../mydocs/working/task_m1_2_stage1_observations.json) binds the reports to source/test hashes, the local binary hash and build metadata.

| Item | Tool sandbox | Ordinary host execution |
|---|---|---|
| Diagnostic architecture | ARM64 | ARM64 |
| Own translation query | Unavailable, `EPERM` | Observed `false` |
| macOS/build | 26.5.2 / 25F84 | 26.5.2 / 25F84 |
| Process page size | 16,384 bytes | 16,384 bytes |
| Four selected runtime symbols | Resolved | Resolved |
| Signature category | Ad hoc | Ad hoc |

The 14 diagnostic tests passed. These results establish that this observation tool runs natively and handles unavailable information correctly. The 16 KiB result describes its ordinary process geometry; it does not test Windows 4 KiB behavior. Ad-hoc signing does not establish authorization for restricted capabilities.

## Interpret the baseline report

The separate JSON record uses `record_kind: baseline_execution`. `parent_observations` retains the observation-only contract and describes the supervisor. `probes` records the four owned children, their actual termination, bounded output counts and individual operations. A `passed` probe means only that this particular baseline behavior was observed. `unavailable` retains the platform error for an operation that the current process configuration could not perform. `failed` covers malformed evidence, unexpected termination, runner errors and incorrect behavior. `not_run` marks steps that were not reached.

The CLI returns zero when every probe is passed or unavailable, one when any probe fails, and two for invalid arguments. Therefore a zero exit alone cannot qualify a runtime. Inspect each status and its error. Step values are operation-specific: bytes for allocation/code publication, the observed integer for readback/execution, and zero for a completed void operation or a failed request without another value. Only `not_run` uses a null value. Numeric error domains distinguish errno, Mach and internal semantic checks.

| Probe | Positive evidence | Boundary |
|---|---|---|
| Memory | Allocate, write/read 42, switch to read-only and read again, restore write access, write/read 84, release | Ordinary process pages only |
| Protection | Valid pre-fault packet after allocation/readback/read-only protection, then SIGBUS or SIGSEGV | An unrelated signal or a fault before the packet fails |
| Low address | Non-overwriting allocation at `0x20000000`, readback and release | Normal linker layout retained; failure here does not prove every low address or layout unavailable |
| JIT | MAP_JIT allocation, fixed eight-byte ARM64 code write, write-protection publication, instruction-cache synchronization, return value 42, release | No x86 translation, guest code, restricted ABI authorization or distribution test |

The runner creates an owned process group, uses a three-second monotonic execution deadline, caps stdout at one 160-byte packet and stderr at 1,024 bytes, then gives cleanup a separate bounded window of up to one second. Byte counters saturate at the limit plus one to detect overflow; any stderr prevents a valid success packet. The caller must not concurrently reap the owned leader; auto-reaping SIGCHLD dispositions are rejected before launch. The leader remains unreaped until group cleanup, which prevents its PID from being reused during signaling. Cleanup errors remain failures. This is lifecycle control for cooperative test programs, not a security sandbox: descendants that deliberately escape the process group are outside its containment guarantee. A platform refusal to terminate or reap is reported explicitly, not hidden by an indefinite wait or a success result.

The production supervisor accepts no fixture or alternate-child argument. The binary packet is a private same-build protocol, not hostile-code attestation; the JSON report is the shareable evidence. Raw child stderr and private paths are not included.

## Stage 2 observations

The September 28, 2026 ordinary-host run on the same M4 Pro/macOS 26.5.2 produced these results. The [Stage 2 evidence](../mydocs/working/task_m1_2_stage2_observations.json) binds the result to source/test hashes, binary hashes, build inputs and verification. All three executables contained only ARM64 code and had linker-generated ad-hoc signatures. The supervisor's own translation query was observed false. All four direct children were reaped.

| Trial | Result | Recorded evidence |
|---|---|---|
| Memory | Passed | 16,384-byte allocation; readback 42; read-only transition/readback; restored write/readback 84; release |
| Protection | Passed | Valid pre-fault packet, then SIGBUS (10); supervisor continued |
| Low address | Unavailable | Fixed `0x20000000` allocation rejected with Mach code 1, `KERN_INVALID_ADDRESS` |
| JIT | Passed | Eight fixed instruction bytes published and synchronized; returned 42; released |

The inspected child retained a zero-permission `__PAGEZERO` segment covering 0–4 GiB. The low-address result describes the attempted address in this executable's configuration; it is not evidence that a different authorized layout cannot work. The protection child intentionally terminates at the fault, so its later release step stays `not_run`; process teardown, rather than a fabricated successful release, ends that trial. JIT success here does not establish hardened-runtime or restricted-capability authorization.

## Set up signed capability trials

Stage 3 was approved after the Stage 2 report. An ordinary-host signing preflight found one valid Apple Development identity and one valid Developer ID Application identity, with SIP and Gatekeeper enabled. The initially installed macOS profile did not grant either cross-architecture entitlement. The maintainer then supplied a matching development profile that grants `com.apple.developer.cross-architecture-support`. The signed trials below passed with that profile. The earlier sandbox zero-identity result remains an observation of that restricted context.

The restricted development route requires a real profile from the intended Apple developer team:

1. In [Identifiers](https://developer.apple.com/account/resources/identifiers/list), create an explicit App ID for the probe. The initial maintainer identifier is `io.github.postmelee.pear.host-probe`; contributors should use an identifier owned by their own team and pass it with `--bundle-id` to the local signing tool.
2. Inspect **Capabilities** and **Capability Requests** for **Cross-architecture Compatibility Framework**. This name comes from the [Wine maintainer's September follow-up](https://list.winehq.org/hyperkitty/list/wine-devel@list.winehq.org/message/EYMEAE4QQE2CR4OBITUENL3LB67ECDLU/). If access must be requested, follow the [Apple capability request procedure](https://developer.apple.com/help/account/capabilities/capability-requests/). If the capability is absent, its availability to that team remains unresolved; ask Apple Developer Support rather than inventing a grant.
3. Register the Mac using its **Provisioning UDID** from System Information, rather than assuming the Hardware UUID is interchangeable.
4. Generate a **Mac App Development** profile for the explicit App ID, the matching development certificate and the registered Mac. The downloaded profile's actual entitlements determine which capability may be claimed. The named entitlement alternatives are not a reason to add both speculatively.
5. Keep the profile, identity information and device identifiers outside Git. Embed the verified profile in the test app at `Contents/embedded.provisionprofile`; sign with the matching certificate and only the granted restricted entitlement. No restricted test runs until that authorization is verified.

Apple's [provisioning profile explanation](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles) distinguishes entitlement claims in a signature from the profile's authorization. A successful `codesign --verify --strict` does not by itself demonstrate that a restricted capability is authorized. Each required executable needs an appropriate authorization path; a helper does not automatically inherit its parent's grant. The restricted probe uses a single provisioned executable with parent and self-spawned child modes.

The child tests distinguish user page size from kernel page size and verify independent 4 KiB protection plus reserved decommit/recommit behavior. Page alignment, a successful spawn-attribute call, or memory advice alone is insufficient. A distinct layout artifact independently tests low-address behavior.

An independent ordinary Hardened Runtime control can use the existing Developer ID certificate with the public `com.apple.security.cs.allow-jit` exception. The corresponding negative control omits the exception. These local, non-distributed bundles do not claim a cross-architecture entitlement or validate a provisioning route. The existing JIT code uses `pthread_jit_write_protect_np`; it must not also claim `com.apple.security.cs.jit-write-allowlist`, which changes that API contract. See [Apple's JIT guidance](https://developer.apple.com/documentation/apple-silicon/porting-just-in-time-compilers-to-apple-silicon).

After setting `PEAR_PROVISIONING_PROFILE` to a local profile path, run:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
python3 host/probe/hardened_baseline.py > .build/host-probe/local-hardened.json
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" > .build/host-probe/local-provisioned.json
```

The independent control selects a unique valid Developer ID Application identity; `PEAR_SIGNING_IDENTITY` can select an existing local identity explicitly. The provisioned tool requires one matching valid Apple Development identity, an unexpired macOS profile, its actual explicit App ID/cross-architecture grant and this Mac's Provisioning UDID. It signs both layout variants with Hardened Runtime and public allow-jit, embeds the validated profile, verifies signatures and effective claims, then runs default and 4 KiB modes. Missing or ambiguous authorization stops the tool; no fallback invents a grant. Generated copies stay under ignored `.build/` and use local signatures without a timestamp. They are not release artifacts.

The process runner retains the baseline ownership, timeout, packet and cleanup checks. Every 4 KiB child records the spawn-attribute call and its result. A missing setter or nonzero error is a failed launch, with no silent default-mode retry. Unit tests inject setter outcomes into test-only objects; they do not exercise the restricted API. The signed trials provide the actual platform evidence.

## Stage 3 observations

The September 28, 2026 run on M4 Pro/macOS 26.5.2 (25F84), using Apple clang 21 and SDK 26.5, passed the [Stage 3 verification](../mydocs/working/task_m1_2_stage3.md). The [sanitized evidence](../mydocs/working/task_m1_2_stage3_observations.json) binds source, tests, inputs and signed binaries to the results. All five built tools contain only ARM64 slices; signed supervisors observed their own translation status as false. SIP and Gatekeeper remained enabled. All 94 regression tests passed.

| Signed configuration | User / Mach user pages | Kernel pages | Low mapping at `0x20000000` | JIT |
|---|---|---|---|---|
| Standard layout, default mode | 16 KiB / 16 KiB | 16 KiB | Unavailable | Returned 42 |
| Standard layout, 4 KiB mode | 4 KiB / 4 KiB | 16 KiB | Unavailable | Returned 42 |
| Emulation layout, default mode | 16 KiB / 16 KiB | 16 KiB | Passed | Returned 42 |
| Emulation layout, 4 KiB mode | 4 KiB / 4 KiB | 16 KiB | Passed | Returned 42 |

The layout variant uses `-Wl,-x86_64_layout_emulation,-pagezero_size,0x10000`. Inspection confirms a protected 64 KiB `__PAGEZERO` instead of the standard 4 GiB segment. The emulation flag alone did not shrink that segment. This is a probe configuration and a single tested low address, not the final Wine address-space reservation policy.

In each 4 KiB mode, a 12 KiB owned allocation supported changing only its middle 4 KiB page to read-only while retaining and updating both neighbors. Write restoration and readback passed. Replacing only the owned middle page with anonymous `PROT_NONE` memory preserved the neighbors; restoring RW produced 4,096 zero bytes, then returned the written value 42. Separate armed trials observed actual protection/access faults (SIGBUS 10). These tests establish those finite memory semantics, not the complete Windows virtual-memory contract or a physical-memory reclamation guarantee. All 28 direct children across the four runs were reaped.

The ordinary Hardened Runtime positive control returned 42. Its negative counterpart, built from identical pre-signing inputs without allow-jit, failed MAP_JIT allocation with `EINVAL` (22), and its baseline CLI exited one. The control assessment accepts this specific paired rejection; the original `failed` allocation and errno remain in the evidence. EINVAL is not globally reclassified as a permission error. Unpaired EINVAL, failures at later steps and unrelated faults still fail validation. The eight ordinary control children were reaped.

## Run the ABI and thread suite

Stage 4 adds an explicit suite to the same provisioned executable. The default invocation continues to run the Stage 3 process/memory tests. After the normal build and local profile setup:

```sh
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" --suite abi > .build/host-probe/local-abi.json
```

The tool signs fresh copies and checks the same actual profile, device, certificate and effective claims. Each default/4 KiB run contains a geometry trial plus five isolated ABI/thread trials. ABI children have a ten-second execution deadline, followed by the runner's bounded cleanup. A native ABI record uses `record_kind: abi_capabilities`; the signed tool's enclosing record uses `provisioned_abi_control`. A zero exit alone is insufficient: every required trial must pass independently.

| Probe | Behavior under test |
|---|---|
| `x18-roundtrip` | 64 explicit host/foreign/host transitions; preserve a known guest x18 value across the permitted getter; return to host mode |
| `x18-callbacks` | 32 host callbacks, each with a nested guest transition; restore distinct inner/outer guest values; propagate 16 injected error returns correctly |
| `x18-signals` | Deliver SIGUSR1 in host mode and asynchronously during a foreign spin window; verify entry mode, guest signal context, safe host handler calls and guest resumption |
| `thread-policy` | Two workers individually initialize, enable and restore the x86 compatibility policy; retain raw Mach errors and verify joins |
| `thread-litmus` | Two workers run 10,000 baseline and 10,000 enabled-policy message-passing trials; record both outcomes and verify restoration/cleanup |

Apple's SDK `os/arch/arm64.h` requires strict mode toggling: a redundant setter call aborts, and disabling custom mode destroys the guest x18 value. The audited assembly saves guest state before a host callback and restores it only after re-entering foreign mode. Foreign windows call only the two allowed, pre-resolved x18 APIs. Normal C/POSIX work happens in verified host mode. The asynchronous signal gateway follows the same rule and preserves the interrupted context.

The ordering test uses plain assembly stores `data=1; flag=1` and loads `flag; data`. Observing flag=1 with data=0 is forbidden under x86-TSO; a nonzero enabled-policy count fails. Baseline ARM reordering is recorded when observed but is not required for success. Synchronization belongs outside the measured pair. The SDK exposes a setter without a corresponding getter, so successful calls are recorded as requests accepted, not independently observed policy state or inheritance. A finite zero count does not prove universal ordering or replace translator-level tests.

Ordinary tests simulate packets and policy return codes and inspect assembled instructions. They never execute x18-writing code with a fake mode setter, which would still leave macOS's reserved x18 register in force. Only the provisioned native runs establish actual platform behavior.

## Stage 4 observations

The September 28, 2026 [Stage 4 run](../mydocs/working/task_m1_2_stage4.md) on the same M4 Pro/macOS 26.5.2 passed in standard/emulation layouts and default/4 KiB page modes. [Sanitized evidence](../mydocs/working/task_m1_2_stage4_observations.json) records the actual signed runs, input bindings and 126 passing tests. The 24 ABI-suite children were reaped. The rebuilt executable also passed the Stage 3 process suite, retaining the standard-layout low-mapping limitation and reaping its 28 children. SIP and Gatekeeper remained enabled.

Every configuration completed 64 round trips, 32 nested callbacks and 16 injected error returns with the expected guest values and host-mode restoration. Signal handlers observed mode 0 during the host control and mode 1 when interrupting the foreign spin window. The gateway entered host mode for the handler body, checked the interrupted x18 context, returned to foreign mode and resumed with the guest value intact. Both markers from actual handler writes were received. These are finite SIGUSR1 and explicit error-return cases, not a complete exception/unwind implementation.

Two policy workers per configuration each successfully requested disable, enable and disable, then joined. The message-passing trial used two further explicitly initialized workers:

| Configuration | Baseline trials / forbidden observations | Enabled trials / forbidden observations |
|---|---|---|
| Standard / default pages | 10,000 / 3 | 10,000 / 0 |
| Standard / 4 KiB pages | 10,000 / 2 | 10,000 / 0 |
| Emulation / default pages | 10,000 / 0 | 10,000 / 0 |
| Emulation / 4 KiB pages | 10,000 / 0 | 10,000 / 0 |

The five baseline observations show that this test can expose the ordering difference on this machine. No forbidden outcome occurred across 40,000 enabled-policy trials. This supports the tested behavior without proving universal ordering, independently reading a hardware mode bit, or qualifying a translator's entire memory model. Baseline zero counts in two configurations are not treated as failures or as proof that ARM ordering is always sufficient.

## Reproduced host capability decision

On September 28, 2026, [Stage 5](../mydocs/working/task_m1_2_stage5.md) reproduced the complete host suite from a fresh output directory on the same Mac. All 38 source/test file hashes matched Stage 4, and all five rebuilt ARM64 binaries matched their earlier SHA-256 hashes before identity signing. The 126 tests passed. Fresh signed controls and process/ABI trials retained their expected outcomes, and all 64 dedicated trial children were reaped. [Sanitized evidence](../mydocs/working/task_m1_2_stage5_observations.json) includes the inputs, signatures, commands and full result records.

The selected passing host configuration is M4 Pro/macOS 26.5.2 (25F84), SDK 26.5, the emulation layout with a protected 64 KiB PAGEZERO, requested 4 KiB user pages, and the validated Apple Development profile granting cross-architecture support. Kernel pages remain 16 KiB. SIP and Gatekeeper stayed enabled. The standard layout's low-address allocation remains unavailable and is retained as a comparison, not counted as a passing prerequisite.

The new ABI run again completed all roundtrip, callback, controlled signal and explicit error-return cases. Message passing produced baseline forbidden counts of 3, 6, 0 and 0 for standard/default, standard/4 KiB, emulation/default and emulation/4 KiB respectively. Enabled-policy counts were zero in all four configurations: 0 out of 40,000 trials. Baseline counts may vary; the interpretation remains finite behavioral evidence with no independent policy getter. The paired negative JIT control retained its failed MAP_JIT allocation, errno 22 and baseline CLI exit 1; only its assessment against the matched successful positive control passed.

This passes Issue #2's bounded native host gate on the declared configuration. The [final report](../mydocs/report/task_m1_2_report.md) maps all three acceptance criteria. It completes the host-probe contribution to G0; source qualification and the integrated M1 runtime still need their own evidence.

### Repeat from fresh build outputs

After all previous probe runs finish, preserve their ignored output directory and rerun the documented commands. The signing prerequisites in this guide still apply; set `PEAR_PROVISIONING_PROFILE` locally to your actual authorized profile. Do not commit the profile or generated bundles.

```sh
if [ -d .build/host-probe ]; then
    mv .build/host-probe ".build/host-probe-preserved-$(date -u +%Y%m%dT%H%M%SZ)-$$"
fi
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
.build/host-probe/pear-host-probe > .build/host-probe/local-observations.json
.build/host-probe/pear-baseline-probe > .build/host-probe/local-baseline.json
python3 host/probe/hardened_baseline.py > .build/host-probe/local-hardened.json
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" > .build/host-probe/local-process.json
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE" --suite abi > .build/host-probe/local-abi.json
```

Inspect per-probe statuses, exact signing checks and input bindings rather than relying on CLI exit zero. Compare behavior separately from timings, baseline reordering counts and signed artifact hashes. The recorded reproduction used the same host, source checkout and installed toolchain; it is not a clean-machine or independent-tester result. The matched pre-signing binary hashes are a result for these inputs, not a universal deterministic-build guarantee.

## Remaining qualification

Later Wine/FEX integration needs its own ABI, exception, executable-memory and memory-model coverage. Controlled SIGUSR1 and explicit error returns do not establish Windows SEH, arbitrary framework callbacks or general unwinding. A fixed native JIT leaf does not execute an x86 game or validate the translator's code generation. These probe observations cover their own processes and artifacts; the full required game process/module tree remains unassessed.

Development-profile execution and ordinary-user distribution require separate evidence. The eventual downloadable app must work for its supported users without their installing developer tools or obtaining their own development profiles. The current registered-Mac trials do not establish that distribution path, notarization, other hardware/OS support or Rosetta-free Megabonk execution.

See the [host audit](research/macos-runtime-audit.md), [runtime architecture](architecture.md), and [approved task plan](../mydocs/plans/task_m1_2.md) for the requirements and execution boundaries.
