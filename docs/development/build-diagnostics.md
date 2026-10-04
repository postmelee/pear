# Build diagnostics

Use existing timing records to locate slow build iterations before changing a
recipe or repeating a full build. Pear already uses Ninja through CMake/Meson
where selected by the component. Keep those generators and the component's pinned
tools; Wine and Python validation need their own diagnostics.

This guide is based on source inspection of **Ninja 1.13.1**, commit
`79feac0f3e3bc9da9effc586cd5fea41e7550051`, reviewed October 4, 2026. The examples
were not executed as part of this documentation work. Tool behavior is separate
from measured performance or qualified runtime support.

## Locate the time first

Compare a whole-invocation timer with the existing command `elapsed_ms` records.
Identify whether the outer timer includes lock waiting, preparation, input checks,
configuration, build commands, installation and final verification. A timer's name
alone does not establish its boundary.

For serial, non-overlapping top-level spans within the same invocation:

```text
unattributed time = whole invocation time - sum(recorded command spans)
```

Do not sum nested or parallel spans as elapsed wall time. Supervised command times
can include output scans, process startup, polling and cleanup. A negative
remainder suggests mismatched boundaries or overlap; investigate it rather than
clamping it to zero. Preserve missing measurements as unknown.

The [October 4 timing analysis](../../mydocs/tech/20261004_build_timing_analysis.md)
contains one two-build example and a sanitized projection. Its large remainder
is not a measurement of hashing cost or a prediction of removable delay. It does
not establish typical build speed. When such a remainder dominates, measure its
individual regions in separately approved instrumentation work before optimizing
Ninja or changing verification.

| Observation | Useful next inspection | What it can establish |
|---|---|---|
| Long wait before any build command | Outer wrapper and lock/preparation/input-check boundaries | Whether the delay is outside the compiler invocation; individual costs still need timing |
| Unchanged source appears to rebuild | Dry-run explanation for the selected target | Recorded reasons such as missing/stale outputs or changed commands |
| A dependency or target relationship is unclear | Query the target's inputs/outputs and inspect its generated command chain | The loaded graph and command definitions, not successful execution |
| Compilation or linking dominates | Saved Ninja log plus manifest/target mapping and outer timing | Candidate expensive edges; not CPU time or an automatic critical-path result |
| Commands finish but the wrapper remains busy | Artifact/inventory and post-build verification boundaries | Work that Ninja timing does not cover |

## Select the diagnostic workspace and tool

Use the owning task's approved **inactive, mutable diagnostic build tree** and
its already pinned Ninja executable. Check the recorded executable identity;
`--version` alone does not establish the source/tool provenance. Preserve the
selected compiler, SDK, configuration, target and existing resource/job limits.
Capture each diagnostic's arguments, exit status and output in a distinct,
traceable task location such as `.build/taskN/diagnostics/run-id/`.

An inactive qualification/evidence directory may still be immutable. Do not run
these diagnostics on it or on another worker's active tree. Use an already
approved diagnostic setup whose generated paths and aliases refer to its own
intended inputs. Copying a directory does not automatically relocate CMake/Meson
state or absolute paths. If no suitable setup exists, inspect saved records first
and arrange a setup through the owning task's normal workflow.

Keep raw command output local where it contains private paths or settings; share
only the relevant redacted facts. These examples do not install tools, change job
counts, clear caches or authorize a compiler run.

## Inspect the selected target

Replace the three placeholders with the tool, build directory and target from
the selected component's records. Quote them as shown; paths may contain spaces.
The build directory must already contain its applicable `build.ninja`.

```sh
pear_ninja='/absolute/path/to/pinned/ninja'
pear_build_dir='/absolute/path/to/owned/inactive-diagnostic-build'
pear_target='recorded-target-name'

# Print the target's generated command chain; do not execute the printed text.
"$pear_ninja" -C "$pear_build_dir" -t commands "$pear_target"

# Inspect input/output relationships, suppressing ordinary log write-open setup.
"$pear_ninja" -C "$pear_build_dir" -n -t query "$pear_target"

# Explain the proposed rebuild without running compiler/linker commands.
"$pear_ninja" -C "$pear_build_dir" -n -d explain "$pear_target"
```

`-t commands` prints definitions for the requested target and its input chain,
including commands whose outputs may already be current. It is not a list of
commands actually executed or necessarily scheduled next. In this version it
runs after manifest loading, before log opening or manifest regeneration.
`query` describes inputs/outputs and may load existing dynamic-dependency data;
it is not an independent completeness check for every runtime dependency.
[Command and tool dispatch source][dispatch]

Place global options, including `-n`, before `-t`; later arguments belong to the
selected tool. The `query` example uses `-n` to avoid ordinary log write-open and
compaction paths. **Dry-run does not guarantee an untouched filesystem.** Log
loading can remove an unsupported log or truncate a damaged dependency log even
in dry-run; dry-run build-edge handling can also create directories and write or
remove response files. Use the diagnostic workspace described above.
[Log handling][build-log], [dependency-log recovery][deps-log], [edge handling][build]

If `-n -d explain` schedules regeneration of `build.ninja`, this version can stop
after simulating that regeneration instead of reaching the requested target.
That output is not proof of a no-change target build. Resolve the generator state
through the owning task's approved workflow. Keep build-definition fixes in the
CMake/Meson source/configuration rather than editing generated `build.ninja`.
[Dry-run manifest handling][dispatch]

## Interpret a saved Ninja log

Inspect a preserved log from a known completed invocation. Ninja normally stores
`.ninja_log` in the build root; the manifest's `builddir` can select another
location. Preserve its identity and invocation boundary before further diagnostics
or rebuilds change it. [Pinned manual][manual]

In this version, each data row records start/end milliseconds, output modification
time, output path and command hash. The start/end times use the invocation's time
origin; the modification-time column is not a command duration. `end - start` is
an edge's elapsed span, including some setup, not CPU time. Failed/interrupted
commands need their separate process logs and outcomes; the build log is not a
complete failure history. [Log writer][build-log], [execution timing][build]

Account for these limits before ranking slow edges:

- One edge can have multiple outputs and therefore multiple log rows. Use the
  manifest's edge/output mapping; do not count each output as a separate compile
  or merge unrelated edges just because their timestamps match.
- Concurrent edges overlap. Their duration sum is not wall time. A critical path
  requires the dependency graph and scheduling context, not just sorting times.
- A file can contain entries from several invocations. Compaction can retain only
  newer entries for outputs. Do not treat it as a complete, single-run trace or
  infer trustworthy run boundaries from a timestamp reset alone.
- Configuration, external input checks, locking and final verification may be
  outside Ninja entirely. Keep the outer measurement alongside the edge data.

## Preserve the final verification requirement

Distinguish a fresh output directory, a clean reconstruction, warm caches, an
unchanged incremental check and a targeted relink. They answer different questions.
A fast no-change check does not prove a reproducible full build; a fresh directory
does not prove cold host caches or a clean machine.

Use the smallest approved target or relink to investigate a concrete cause, with
input identity and failed attempts retained. Then perform the required fresh
reconstruction and candidate verification through the component's existing
procedure. Changing a link option or input does not let an earlier successful
candidate qualify the new one. Ninja does not replace source hashes, provenance,
signing, native fixtures or game qualification. See the
[architecture's reproducibility requirements](../architecture.md#reproducibility).

## Sources and scope

The sources below are pinned to the reviewed Ninja commit. Their license and
upstream implementation remain unchanged; this guide links and explains them
without introducing a replacement build system or copying an implementation.
The version string is confirmed in [version.cc][version]. Changes in a future
pin require rechecking behavior. No speed improvement is claimed by this guide.

[dispatch]: https://github.com/ninja-build/ninja/blob/79feac0f3e3bc9da9effc586cd5fea41e7550051/src/ninja.cc
[build]: https://github.com/ninja-build/ninja/blob/79feac0f3e3bc9da9effc586cd5fea41e7550051/src/build.cc
[build-log]: https://github.com/ninja-build/ninja/blob/79feac0f3e3bc9da9effc586cd5fea41e7550051/src/build_log.cc
[deps-log]: https://github.com/ninja-build/ninja/blob/79feac0f3e3bc9da9effc586cd5fea41e7550051/src/deps_log.cc
[manual]: https://github.com/ninja-build/ninja/blob/79feac0f3e3bc9da9effc586cd5fea41e7550051/doc/manual.asciidoc
[version]: https://github.com/ninja-build/ninja/blob/79feac0f3e3bc9da9effc586cd5fea41e7550051/src/version.cc
