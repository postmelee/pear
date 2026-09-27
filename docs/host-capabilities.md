# Host capability diagnostics

The host tools collect native macOS observations and execute isolated baseline memory/JIT trials for [Issue #2](https://github.com/postmelee/pear/issues/2). They are development tools; runtime and game qualification remain unassessed.

`pear-host-probe` only observes its own process. `pear-baseline-probe` supervises four disposable `pear-probe-child` processes, including a fixed ARM64 JIT leaf. Neither tool enters the foreign x18 ABI, changes process page geometry, enables a thread memory-order policy, or launches Steam. Finding an API symbol does not establish permission to call it or prove its behavior.

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

## Remaining qualification

The complete host gate still requires an authorized signing/provisioning path, actual 4 KiB mapping/protection/decommit behavior, a suitable low-address layout, x18 transition correctness, callback/signal handling and per-thread memory-order policy. Required failures or unavailable prerequisites keep Issue #2 open. A fixed native JIT leaf does not execute an x86 game or validate the translator's code generation.

Development-profile execution and ordinary-user distribution require separate evidence. The eventual downloadable app must work for its supported users without their installing developer tools or obtaining their own development profiles. Neither outcome follows from these baseline builds.

See the [host audit](research/macos-runtime-audit.md), [runtime architecture](architecture.md), and [approved task plan](../mydocs/plans/task_m1_2.md) for the requirements and execution boundaries.
