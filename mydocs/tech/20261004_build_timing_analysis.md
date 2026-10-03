# Existing build timing analysis — October 4, 2026

## Research Background

[Task #31](https://github.com/postmelee/pear/issues/31) examines retained #5/#7
records to choose useful build diagnostics. Pear already uses pinned Ninja and
records command durations. This is dated evidence, not a benchmark or support
claim. No build, Ninja diagnostic or qualification replay was run for this note.

## Research Questions

- How much of two construction invocations falls inside recorded command spans?
- Which timer boundaries and unmeasured regions limit attribution?
- What existing practices can be reused before adding instrumentation?

## Research Targets

| Target | Purpose | Evidence |
|---|---|---|
| Two original #7 build records | Command values and producer identity | Local originals; digests and selected fields in projection |
| Two operator receipts and wrapper source | Whole-invocation timer boundary | Local originals; digests in projection |
| Pinned observation file | Cross-check command rows independently of the changing working copy | Exact Git commit in references |
| Captured constructor and monitor sources | Understand timer placement | Four producer digests matched to pinned Git objects |
| #5 Stage 1 and #7 Stage 2 reports | Existing Ninja preparation and reuse | Pinned reports in references |

The [timing projection](20261004_build_timing_analysis.json) retains run labels,
selected outcomes/durations, source/receipt digests and derived totals. Raw paths,
arguments, environments, inventories and private diagnostics remain excluded.
The projection is an analysis artifact, not a build or qualification receipt.

## Findings

### Source identity and fixed sample

Both original build records and both operator receipts match the planning hashes.
Each original ten-command projection equals its pinned observation-file rows.
Four captured producer files from each build match their receipt digests and the
pinned Git objects. These are selected byte/field checks, not full source/tool
verification replay. The original command outcomes are all exit_code 0 with no
stop_reason; this historical result does not qualify runtime behavior.

The pinned #7 commit is e41b7bd7daaab707c3609693ff11e14af6f2d085. Its observation
file has SHA-256 4c7bac2dbb731ddeaf40db01308d0a2a168c19d77b3c8e404342cb6ac26dece1.
The plan separately recorded a working-copy digest of
8a3d8fda4cb037e95f2425ff086d3f295134d08a8cd14f942e47de19964756a1 alongside that
checkout HEAD. A working-copy digest is not a Git-blob digest. The exact old
working-copy snapshot is not retained here, and the live file has since changed.
Use the pinned command rows and original receipts, not new observations. All
selected durations still reproduce the plan without replacing the two-run sample.

### Time distribution

Integer milliseconds are authoritative; percentages round to two decimals.
The dxmt.compile column is already included in the command sum.

| Invocation | Wrapper (ms) | Ten-command sum (ms) | dxmt.compile (ms) | Unattributed remainder (ms) | Remainder (%) |
|---|---:|---:|---:|---:|---:|
| build7 / small_stub_reference | 902376 | 132326 | 82978 | 770050 | 85.34 |
| build8 / small_stub_candidate | 893511 | 119568 | 70049 | 773943 | 86.62 |

For each run: remainder = wrapper elapsed_ms - sum(command elapsed_ms).
The ten top-level spans are serial and already include child work. Do not add
nested compiler/Ninja durations again. Summed parallel edge durations would not
be elapsed wall time either.

The remainder is about 12 minutes 50 seconds / 12 minutes 54 seconds. It is
**unattributed wall time**, not measured hashing time, CPU utilization, redundant
work or an estimate of removable delay. Two uncontrolled sequential observations
do not establish a speed comparison or typical Pear build duration. Fresh output
directories do not establish cold host caches or a clean machine.

### Timer boundaries

The wrapper acquires the shared compilation lock before calling its run function.
That function starts a monotonic timer before opening output logs, synchronously
invokes the constructor, and samples elapsed time after the child returns.
Initial lock waiting, preceding regression checks, subsequent artifact comparison,
and later independent comparison/native qualification are outside these spans.
Logging setup and constructor startup are inside. The wrapper receipt write is
after its elapsed-time sample.

The captured monitored_command starts timing after making the log directory. Its
timer includes initial/final output-size scans, child startup/execution, periodic
storage/log checks, polling sleeps and cleanup. It samples elapsed_ms before
hashing stdout/stderr and appending the command record. Adapter setup also occurs
before entering this timer. Command durations are supervised wall-time spans, not
compiler-only CPU time. Some supervisor/log bookkeeping falls into the remainder.
Command milliseconds are truncated; wrapper milliseconds are rounded. That small
granularity does not explain the roughly 770-second remainder.

Constructor inspection identifies these candidate regions outside command spans:

| Candidate region | Inspected source operations | Individually measured? |
|---|---|---|
| Input/provenance replay | verify_build, prepared_values, qualification_values before commands | No |
| Source preparation and tool checks | source.project, verify_wine_tools | No |
| Layout and generated inputs | copy_layout, generated_inputs between groups | No |
| Artifact and final verification | artifact_rows, final_epochs, qualification_values, source_projection | No |
| Monitor/log bookkeeping | Adapter setup, directory creation and log hashes outside elapsed_ms | No |

These names identify where future timers might help, not their costs or redundant
work. Inventory scans also occur inside command spans; do not assign all inventory
work to the remainder. Source inspection cannot determine which region dominates.

### Existing practices to retain

#5 records ARM64 Ninja 1.13.1 built at commit
79feac0f3e3bc9da9effc586cd5fea41e7550051. #7 reuses that verified source-built tool.
Its Stage 2 report records two-job native builds; this is an operational bound,
not a measured optimum. The #7 implementation plan records 31 link-only trials
before fresh reconstruction. That diagnostic separation avoids repeating full
builds for every link experiment while retaining final evidence. Those trials
are historical #7 work; no speedup was measured by this note.

## Decisions

- Retain existing Ninja/CMake/Meson and Python elapsed_ms records.
- First separate command spans from other construction work; the latter dominates
  these two recorded invocations without identifying its individual causes.
- Use Ninja detail when rebuild decisions or command execution are implicated.
- Preserve source identities and required fresh reconstruction/qualification.
  Cost alone does not authorize weakening checks.

## Non-decisions / Deferred Items

- Individual phase costs, critical path, resource peaks, cache effects, optimal
  job count and achievable improvement remain unknown.
- New timers, verification caching, tuning and validator changes need their own
  approved implementation scope.
- The projection and hashes do not make private originals publicly replayable.
- No native/game performance, Rosetta-free execution or distribution qualification
  follows. Other-task communication and integration remain deferred by the user.

## Implementation Impact

Stage 2 should explain attribution before listing Ninja options, preserve these
timer caveats and separate incremental/relink diagnosis from final fresh-build
requirements. Link this dated analysis rather than treat its timings as a permanent
product statement. Other tasks need not change their current inputs or processes.

## References

- [Approved plan](../plans/task_m1_31.md) and [implementation plan](../plans/task_m1_31_impl.md).
- [Timing projection](20261004_build_timing_analysis.json).
- [Pinned observations](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/mydocs/working/task_m1_7_stage5_reconstruction_observations.json).
- [Constructor](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/tools/dxmt/deterministic_pair.py).
- [Command supervisor](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/tools/dxmt/build_native.py).
- [Pairing adapter](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/tools/dxmt/pairing_monitor.py).
- [Deterministic adapter](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/tools/dxmt/deterministic_monitor.py).
- [#5 tool report](https://github.com/postmelee/pear/blob/275681a07353ccfe5676ed2518530795c4994938/mydocs/working/task_m1_5_stage1.md).
- [#7 native build report](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/mydocs/working/task_m1_7_stage2.md).
- [#7 link trial record](https://github.com/postmelee/pear/blob/e41b7bd7daaab707c3609693ff11e14af6f2d085/mydocs/plans/task_m1_7_impl.md).

Sources were inspected as local immutable Git objects on October 4, 2026.
Stage 3 subsequently fetched all eight linked Pear files at those exact commits
and matched their remote Git blob IDs to the inspected local objects. This
confirms source-link availability, not private-receipt or runtime qualification.
