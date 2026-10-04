# Task #14 Stage 4 — Isolated DXMT Temporary-Root Portability

GitHub Issue: [#14](https://github.com/postmelee/pear/issues/14)
Implementation plan: [task_m1_14_impl.md](../plans/task_m1_14_impl.md)
Stage: 4 — isolated patch verification completed October 5, 2026; integration pending.

## Stage Purpose

Remove OS-specific scratch-root selection from two existing DXMT test helpers while preserving #7's completed, intentionally uncommitted source and evidence. The requester authorized the concrete snapshot, patch, local-test and handoff sequence in this thread. #7's owner was notified before work; its worktree was not modified.

Context: root/tests rules, README, documentation index, architecture and delivery plan; #14 Issue, plans and preceding reports; #7's final Stage 5 and delivery reports; task/Git/document/conflict procedures and task-start, todo and task-stage-report skills. Reuse the existing Python unittest suites and tempfile API. This is test scratch handling, not Metal implementation or diagnostics; Apple tooling guidance is not applicable.

## Artifacts

| File | Change Summary |
|---|---|
| [task_m1_14_stage4.patch](task_m1_14_stage4.patch) | Four changed helper lines across the two latest #7 test files; integration delta rather than an import of uncommitted #7 work |
| Existing #14 task and implementation plans | Approved snapshot/test boundaries; original maintenance/promotion proposal retained as Stage 5 |
| [October 5 board](../orders/20261005.md) | Local patch milestone recorded; #14 remains In progress |
| This report | Exact source identities, observed failure/correction, execution and integration limits |

## Body Change Scope / Lossless Preservation

Continue on codex/task14 fast-forwarded to master `abaabc2`. Target tests are not yet on master. The patch is therefore tracked as internal task evidence for later integration; neither #7's working tests nor master tests were changed. No public CI configuration, source verifier, runtime, signing policy or upstream patch changed.

The baseline snapshot contains 503 unique paths: tracked working files plus the named public completion files, 8,751,032 regular-file bytes. It preserves #7's actual working source, not merely HEAD `d3772898b2bdafa72f5962312cd125658601e6c9`. Five explicitly selected untracked completion files are the final and Stage 5 reports, loader reservation patch, loader test and loader tool. The snapshot excludes .git, ignored build payloads, private diagnostic captures and signing data. Files were copied independently (no hard links), hashed and reread for consistency. Symlink targets were recorded without following them. A final reread found no changes in any of the 503 owner paths.

Local evidence root in the main workspace: `.build/task14/runs/20261005-dxmt-temp-portability/`. It contains baseline/, candidate/, baseline-manifest.json, original/corrected patch, test inventory, run-suite.py, results.json, verification.json and separate initial/corrected logs. It is ignored, local-only and retained through successor integration and review. Preserve needed evidence before cleanup; a recorded path does not promise indefinite availability.

Baseline manifest SHA-256: `ac4cfe009387929f397459acde9c081ba1acadc8cb51a743ab8ff70d538b9768`.
Patch SHA-256: `7087e30de2b0e7819d7d1004576df6ffa7b7738171e06ea212848d14c8228a5a`.

| Target file | Before SHA-256 | After SHA-256 |
|---|---|---|
| `tests/dxmt/test_deterministic_native.py` | `e5348cf936e83e4c323a33268ebad24aaf2dc2b66fd1c3e070d73491853ed18a` | `a8b3bf4177ca7c02e6231abf9f88c6ed5637a054d31afb42283889df713e3aa5` |
| `tests/dxmt/test_deterministic_pair.py` | `0295b42cdcf767f533147e980c75d1c661d6a16a2577ed76aed171536e0b3aaf` | `97a8f3d418670a2aa2a1a2a21488deaa9b647e23a3931b4a3d886b9c82f3bdc5` |

## Verification Results

Execution context: Python 3.14.4, macOS 26.5.2, arm64. This is synthetic unittest execution, with no compiler, GPU, signed runtime or game execution. Existing #7 final native/reconstruction evidence was preserved and referenced as prior evidence only; it was not rerun or transferred to a different native candidate.

First attempt: removing only `dir='/private/tmp'` exposed the platform default `/tmp` alias. The pair file recorded 2 assertion failures and 34 errors; native recorded 1 error. Existing strict validators rejected aliased roots (`unsafe_root`, `shader_directory_alias`, and O_NOFOLLOW rejection). Both files passed under the physical custom root. All initial logs and the failed patch remain retained.

Correction: after normal tempfile allocation, resolve only `self.root=Path(self.temporary.name).resolve(strict=True)`. TemporaryDirectory still owns and cleans the original allocation. Synthetic aliases created by refusal tests remain aliases; no refusal predicate/assertion or test selection was weakened. This makes the patch four changed lines rather than the initially proposed two.

Command shape from the independent candidate root:

```sh
python3 -B <run-root>/run-suite.py test_deterministic_pair.py
python3 -B <run-root>/run-suite.py test_deterministic_native.py
```

The retained runner uses unittest discovery for the named file, compares actual IDs with its static inventory, records all outcomes and exact skipped IDs, and observes `tempfile.mkdtemp` audit events without changing allocation arguments or cleanup. Each invocation is a fresh process. All PEAR_TEST_* overrides and PYTHONPATH are cleared; default mode clears TMPDIR/TMP/TEMP, while custom mode sets TMPDIR to the physical run-owned `scratch with spaces` directory. The corrected logs are in logs/corrected-default/ and logs/corrected-custom/; process exit codes are retained separately. This local runner intentionally accounts for the eight known optional-input skips; it is not the no-skip CI gate.

| Mode | Suite | Discovered/run | Passed | Skipped | Failures/errors | Created / retained temp directories | Exit |
|---|---|---:|---:|---:|---|---|---:|
| Platform default | pair | 96 | 88 | 8 | 0 / 0 | 79 / 0 | 0 |
| Platform default | native | 37 | 37 | 0 | 0 / 0 | 33 / 0 | 0 |
| Physical TMPDIR with spaces | pair | 96 | 88 | 8 | 0 / 0 | 79 / 0 | 0 |
| Physical TMPDIR with spaces | native | 37 | 37 | 0 | 0 / 0 | 33 / 0 | 0 |

No expected failures or unexpected successes occurred. Every observed temp directory was under the selected physical root and was removed at completion. The custom scratch directory was empty afterward. Per mode, 125 passed and 8 were explicitly unperformed; repeated modes do not increase unique coverage.

Skipped IDs are six MetalControlEnvironment methods, FixedDirectoryActual.test_actual_source_dependency_configuration_and_post_observation_closure, and Reuse.test_reviewed_fex_package_import_is_captured_without_global_package_alias. The retained inventory/results contain every full ID. These require optional actual Metal/FEX inputs and were intentionally absent. Do not treat them as qualified or silently filter them out of a future CI run.

The final snapshot diff is exactly the two intended test files/four lines. `git apply --check` against the preserved baseline and Python AST parsing passed. The owner's 503-path manifest was rechecked unchanged. Offline governance and local document links, new task-artifact links and `git diff --check` passed on the #14 worktree.

## Residual Risks

- The patch is applied and tested in the isolated candidate only. Integration into #7 or a successor checkout remains pending its source handoff; compare target file hashes before applying. Do not overwrite the owner's final reports or tests.
- Hosted Linux execution and CI selection are unperformed. The native suite has no conditional test methods; the pair suite mixes public and private-input methods and needs an explicit later selection/split without weakening no-skip CI policy.
- The snapshot does not preserve private native build payloads; #7 retains ownership of those original records and artifacts.
- Existing approved #7 native evidence remains scoped to its original candidate. A later source or toolchain change may require affected revalidation.

## Impact on Next Stage

Hand the patch and exact target hashes to the #7 owner. Once its completion source is published or an integration checkpoint is agreed, apply the patch to the corresponding tracked files and rerun affected checks if any inputs changed. Keep source verification and historical evidence unchanged. Full #14 maintenance/promotion remains the separate Stage 5 proposal; no Issue closure, PR publication or remote CI was performed here.

## Approval Request

The approved isolated patch/test delivery is complete. Review this artifact before a subsequent integration/hosted-CI stage; the current authorization does not expand to that stage.


## October 5 integration follow-up

The #7 owner integrated the exact verified after-bytes in ea6c018565217b852b8e116d692773214cec1c20 (PR #33). Both target SHA-256 values matched this report on merged master 7ba7aa9. PRs #33/#34 are merged and #7 is CLOSED; its retained worktree/evidence remains owned by #5/#7. The pending-integration statements above describe this report's original checkpoint; source integration is now complete. Stage 5 handles separate Linux/CI qualification.
