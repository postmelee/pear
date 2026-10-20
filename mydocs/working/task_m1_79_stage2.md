# Task #79 Stage 2: adopt master and align guidance

Issue: [#79](https://github.com/postmelee/pear/issues/79)
Implementation plan: [task_m1_79_impl.md](../plans/task_m1_79_impl.md)

## Stage Purpose and Artifacts

Create each public master at its Stage1 integrated commit, switch default access
and prepare the current documentation successors. Task-plan locations apply.
The old remote refs remain until all five documentation PRs merge, avoiding a
temporary broken-link state in Pear's still-published guides.

| Component | Stage2 documentation commit |
|---|---|
| pear-wine | `b4de7ec5f5729d6f47bea7de9cfc091b8e9bc7b5` |
| pear-fex | `18505013d0c45ac344e926709f73964c864916c0` |
| pear-dxmt | `c74c9b811b486e19341805da4e545dc7a20af8b1` |
| pear-runtime | `07ca1793de96fb66665602eedd381844dfc392c1` |

## Body Change Scope / Lossless Preservation

Five existing Pear current guides and eight component guides now describe master
integration/PR targeting. Five historical clickable cutover links are pinned to
the exact Task56 runtime record; their original prose/claims and machine-readable
reference fields are unchanged. Runtime's acquisition command changes only the
fetch ref to master. No other command, existing SHA pin, source, workflow, notice,
lock, recipe or upstream README body changed. Runtime contracts' adjacent stale
collaborator-only access sentence is corrected to the already-public status.
Local task56 checkout names are explicitly distinguished from remote integration.

## Verification Results

- Immediate pre-mutation repository/ref/branch/PR guards matched all four Stage1
  baselines. Each master was created at the identical old tip, then only the
  default_branch setting changed. API readback and git ls-remote --symref confirm
  PUBLIC/master/exact commit; old task56 refs remain intact. No PR needed retargeting.
- Full-tree inventory and inherited YAML trigger audit require no automation-file
  changes. Upstream main filters and all Actions settings are preserved.
- Pear governance PASS: 40 documents, 386 local targets. Fresh document regression
  run PASS: 121 tests, 9.925 seconds, no failures/errors. Git 2.53.0, gh 2.89.0,
  Python 3.13.5 on the existing Mac. These are portable document checks only.
- All five incremental source-notice guards and diff --check pass. No changed source
  requires a notice addition; manual upstream/policy preservation review applies.
- Four component path allowlists contain only the expected three Markdown files
  each. Existing 40-hex pin occurrences are preserved; fenced commands match except
  the explicitly reviewed fetch-ref replacement. Agent full-tree link checks cover
  13 Wine/FEX and 36 runtime/DXMT local targets, all resolved.
- Historical cutover target's 19,460 bytes and SHA256 match the retained canonical
  record. An initially unsupported sparse-checkout add option was corrected in the
  isolated documentation clone before its link repair; no protected checkout changed.

Receipts remain local: master-transition.json, component-doc-checks.json and
component-doc-commits.json; independent final review is a Stage3 gate.
No runtime, native, game, installation or build tests ran. Unchanged historical
runtime evidence is not relabeled as a fresh verification result.

## Artifact Disposition

Only new sparse documentation clones/worktree and text evidence created. Existing
producer roots, local branches, inputs/outputs and #47 are retained. Old remote
refs are pending dependency-complete cleanup; no byte deletion or reclaimed-space
claim. Full private-state rehash is not claimed.

## Residual Risks and Next Stage

Docs are committed locally, not yet integrated. Verify exact PR heads/trees and
available CI before merging. After all five guide successors are published, recheck
live consumers and exact ref values before retiring old remote task56. Unknown
external clones may need to fetch master. Continue within the approved migration.
