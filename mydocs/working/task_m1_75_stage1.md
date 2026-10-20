# Task #75 Stage 1 — Current baseline and document reconciliation

GitHub Issue: [#75](https://github.com/postmelee/pear/issues/75)
Implementation plan: [task_m1_75_impl.md](../plans/task_m1_75_impl.md)
Stage: 1

## Stage Purpose

Correct current documentation after the merged split-runtime handoff without
changing the selected runtime or attributing old builds to newer source tips.
Context used: root/docs rules, existing README/documentation index, architecture,
delivery plan, runtime contracts and development guide; Task #56 final report and
source-cutover record; approved Task #75 plan, workflow/retention procedures and
`task-stage-report` skill. The user approved continuous progression through all
three stages with verification, reports and commits on 2026-10-20.

## Artifacts

| File/repository | Change summary |
|---|---|
| `README.md` | Final-report link now resolves to the corrected merged report |
| `docs/development/rosetta-free.md` | Exact final-source versus compiled/tool roles; Task75 tracking and private status |
| Task75 plans and daily board | Recorded continuous approval and bounded WGI scope/capacity |
| Wine/DXMT component guidance | Corrected current public-ancestry prose; historical pins retained |
| Runtime README/NOTICE/development guide | Accepted ownership and publicly reachable corrected Pear handoff |

Component documentation commits and their bundled Stage1 reports: Wine `6684cba19474dabbf6bdb5de4019427e0c958938`,
DXMT `28fe386342ae849e746564eae3ca94e9612bd912`,
runtime `17516d7`.
These are local review branches, not new remote/default-branch or runtime pins.
FEX's final README already states the accepted boundary and needs no prose edit.
The index, architecture and runtime contracts already describe the right owners;
no change was needed there.

## Body Change Scope / Lossless Preservation

Pear base `2c151f1d074fab5a55bc2d77e25b5fb81aedc257`; component bases are the
four exact final Task56 refs listed in the updated guide. Edits are confined to
approved existing document locations and task records. Source, locks, imported
notices, generated headers, frozen source-cutover records and old reports are
unchanged. Runtime tool `6f0202b` and FEX tool `9c9b602` retain their separate
clean source roots. Historical dirty runtime and locked Pear roots are preserved.

## Verification Results

Execution context: macOS, Git and Python 3.14.4; portable documentation checks,
no build/runtime/guest/game execution. Evidence reuse: original Task56 controls
are cited only as historical evidence for their exact inputs, not fresh checks.

```sh
git diff --check
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base 2c151f1d074fab5a55bc2d77e25b5fb81aedc257
```

- Governance: 40 documents / 385 local targets passed.
- Documentation tests: 121 passed in 11.534 seconds.
- Incremental source notice check: no touched source files, no errors.
- Runtime Markdown targets: all 45 local paths exist. Relevant Pear historical,
  corrected and merge commits are ancestors of the observed public master.
- Component reports record narrow path/link checks and `git diff --check`.
- Protected source HEAD/status snapshot retained privately; selected roots match
  expected identities. Full installed/game/private-state hashing was not performed;
  no operation targets those roots. This is not whole-filesystem attestation.

## Artifact Disposition

| Artifact/root | Actual state/outcome | Owner/consumer | Identity/recovery | Retain/release condition |
|---|---|---|---|---|
| New Task75 source worktrees | Isolated source output; Wine sparse | Task75 review | Git stage commits | Retain for review and later dependency check |
| Private Task75 audit records | New read-only inspection evidence | Publication/WGI stages | Hashed evidence retained privately | Retain through successor handoff |
| Selected candidate/tool/input roots | Preserved; no mutation | Task56, #12/#13, next WGI work | Existing locks/producer records | No release authorized in #75 |
| Installed app/game/saves/private state | No operation performed | User/#47 | Existing owner | No release authorized |

Measured new task trees and audit files totaled 128,679,604 logical bytes and
134,332,416 stat-allocated bytes at the Stage1 snapshot, below the 512 MiB initial
ceiling. This excludes shared existing Git storage. Filesystem free space was
20,088,377,344 bytes at a separate snapshot; concurrent work prevents attributing
its change to this task. No storage was reclaimed, and no old artifact was deleted.

## Residual Risks

Private source availability is not public-clone runtime reproducibility. Existing
retained lower layers and private developer inputs remain required. The old
494-byte frame request is already restore-required as recorded by the handoff;
its exact recovery copy remains retained, and no game-run restoration is attempted.

## Impact on Next Stage

Audit the exact original remote heads plus these documentation successors.
WGI producer records are now located; independent reproduction belongs to Stage3.

## Approval Record

The requester approved all three stages continuously. Stage2 proceeds after this
verified bundled commit. Visibility conversion, game execution and old-artifact
deletion remain excluded.
