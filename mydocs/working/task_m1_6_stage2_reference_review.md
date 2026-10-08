# Task #6 Stage 2 — Native Reference Publication Review

Date: October 8, 2026. Stage 2 is in progress, not complete.

## Decision requested

Approve an early push of the reviewed CPU harness and
[reference workflow](../../.github/workflows/cpu-native-reference.yml) to
`codex/publish-task6`, execution of the native Windows reference, and retrieval of
its exact PE/result artifacts. Necessary corrections confined to this same
reference harness may update that task branch. This does not merge into `master`,
close #6, or approve a later stage.

The [approved implementation plan](../plans/task_m1_6_impl.md) requires review of
the concrete workflow before this publication exception. Native execution is
needed to establish independent results before comparing the same PEs on Pear.

## Concrete execution

| Step | Scope |
|---|---|
| Trigger | Push to `codex/publish-task6`, limited to the named workflow and CPU fixture/tool paths |
| Linux build | Ordinary `ubuntu-24.04` runner, 15-minute job limit; FEX revision `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`; NASM 3.02 and LLVM-MinGW 20260908 archives checked against recorded SHA-256 |
| Windows execution | Ordinary `windows-2022` runner, 15-minute job limit; actual process/native machine checked with `IsWow64Process2`; 30-second limit per fixture |
| Permissions | `contents: read`; checkout credentials are not persisted; no secrets, provisioning profiles, game files, Steam state or local private diagnostics |
| Artifacts | 19 redistributable PEs, corresponding source/notices, exact build inputs and native observations; 14-day Actions retention; failed observations retained |
| Qualification | Record unavailable features and failing cases; no Rosetta reference, no unsupported-to-pass conversion and no game qualification |

Actions are pinned to immutable commits. Only ordinary hosted jobs are selected;
private-repository execution uses the account's normal Actions allowance. No new
paid service or larger runner is requested. `master` and existing workflows are
unchanged. Preserve selected records locally before Actions retention expires.

## Local preflight completed

- Official NASM 3.02 source archive SHA-256:
  `87336eba53b4acfe917424ab5d500d2b0054d9f5148d35c2273ccf2cfb712f0d`.
  Native ARM64 build succeeded in a task-owned 35 MiB tree; no system installation.
- Existing ARM64-selected LLVM-MinGW cross compiler builds all **19 AMD64 PE32+**
  fixtures: 12 selected FEX instruction cases, five unchanged Pear boundaries,
  new register/stack callback checks, and table-based SEH/unwind checks.
- All 19 PEs have no writable/executable section. The SEH image contains its
  exception/unwind table. These are static/build observations, not execution.
- **12 harness refusal tests** and **14 corpus checks** passed; governance and
  whitespace checks passed. Negative cases include false success, truncated
  build/results, mixed binary inputs, corrupted upper AVX lanes, altered ABI
  state, undefined flag masks, feature absence and a non-native reference host.
- The first ABI build failed because a stack diagnostic buffer required a CRT
  stack helper. Moving that buffer to static storage removed the unnecessary
  dependency. The original failure log is retained privately.

## Remaining Stage 2 work

Run this native reference, retrieve its exact PEs, and admit the unchanged #5
runtime through its recorded source/build/signing checks. Complete the #6 adapter
for Pear's existing process supervisor, then compare actual defined results with
native Windows. Pear admission is deliberately unavailable in the new result
parser until that adapter exists; a caller-supplied success flag cannot qualify
it. Fix and reduce any required mismatch before reporting Stage 2 complete.

No native reference, new Pear guest execution, GitHub push or workflow run has
occurred at this review checkpoint.

## Requester approval

The requester explicitly approved publication, confined corrections and execution
on October 8, 2026. No additional permission is needed for routine reference
harness fixes within this reviewed scope. Stage 2 completion and later stages
retain their existing evidence and transition requirements.
