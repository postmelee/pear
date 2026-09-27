# Host capability diagnostics

The first host probe collects observations from its own native macOS process. It is a development tool for [Issue #2](https://github.com/postmelee/pear/issues/2), not the Pear launcher or a Rosetta-free game runtime.

The probe does not enter the foreign x18 ABI, execute generated code, change page geometry, enable a thread policy, or launch Steam. Those operations belong to later isolated and signed tests. Finding an API symbol does not establish permission to call it or prove its behavior.

## Build and run

From the repository root on an Apple Silicon Mac with Apple clang, the macOS SDK, Make and Python 3 available:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
lipo -archs .build/host-probe/pear-host-probe
.build/host-probe/pear-host-probe > .build/host-probe/local-observations.json
python3 -m json.tool .build/host-probe/local-observations.json
```

Builds and unreviewed local observations stay under ignored `.build/`. The diagnostic uses system libraries and does not require an Apple developer identity. That statement applies only to collecting these observations, not to restricted ABI execution or runtime distribution.

The initial development environment is Apple clang 21 with macOS SDK 26.5 on M4 Pro/macOS 26.5.2. The diagnostic's build target is not a declaration of Pear's eventual minimum supported macOS or chip.

## Interpret the report

The versioned JSON report is scoped to the current diagnostic process. Observations identify a value or explain why it could not be obtained. Error domain and numeric code are preserved when an operating-system request fails.

| Observation | Meaning | Limit |
|---|---|---|
| Executable architecture | The running diagnostic's Mach-O architecture | Does not describe Wine, Steam or a future child process |
| Process translation query | The diagnostic's own `sysctl.proc_translated` result | A denied or missing query remains unavailable; it is not converted to `false` |
| OS/build and page size | Values visible to this process | Sandbox restrictions and a different process configuration may change observations |
| Runtime symbol presence | Whether selected host APIs can be resolved dynamically | Does not call them, validate permission, or verify semantics |
| Signature category | A coarse category derived from the current executable | Does not validate a distribution identity, provisioning profile, entitlement authorization or notarization |
| Capability execution and qualification | Explicitly not run or not assessed | No whole-runtime or Megabonk support claim is made |

`observed` means that an observation succeeded. `unavailable` means that the requested information could not be obtained in this context. `failed` identifies an invalid or failed observation operation. These statuses are distinct from a future capability test passing or failing. An ordinary diagnostic exit does not mean that every observation is available.

The report deliberately omits identity names, account information, hostnames, usernames, private signing material and absolute private paths. Review result files before sharing them; other tools run alongside the probe may have different output policies.

## Test boundary

The tests combine a real native run with a separately built fixture that injects observation results into the production collection and JSON-writing code. The shipped diagnostic has no fixture mode. Synthetic success cannot qualify the host.

Tests cover denied translation queries, absent symbols, unavailable signature information, unexpected architecture input, JSON escaping, and invalid CLI arguments. A denied query must remain unavailable instead of becoming a negative translation result. Missing APIs must remain observations rather than positive execution results.

Disposable child execution, timeout/signal containment, memory/JIT behavior and signed ABI tests are later stages. Their absence is a limit of this initial diagnostic, not an implicit passing result.

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

## Remaining qualification

The complete host gate still requires isolated memory/JIT tests, an authorized signing/provisioning path, actual 4 KiB behavior, x18 transition correctness, callback/signal handling and per-thread memory-order policy. Required failures or unavailable prerequisites keep Issue #2 open.

Development-profile execution and ordinary-user distribution require separate evidence. The eventual downloadable app must work for its supported users without their installing developer tools or obtaining their own development profiles. Neither outcome follows from a native diagnostic build.

See the [host audit](research/macos-runtime-audit.md), [runtime architecture](architecture.md), and [approved task plan](../mydocs/plans/task_m1_2.md) for the requirements and execution boundaries.
