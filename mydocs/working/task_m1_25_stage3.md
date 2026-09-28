# Task #25 - Stage 3 Report

GitHub Issue: [#25](https://github.com/postmelee/pear/issues/25)
Implementation plan: [task_m1_25_impl.md](../plans/task_m1_25_impl.md)
Stage: 3 - Templates and mechanical verification
Date: September 28, 2026
Work branch: `codex/task25`

## Stage Purpose

Complete the approved task templates, bounded offline governance checker and documentation CI. The maintainer explicitly approved the Stage 2 report and Stage 3 start in this thread. Final-report preparation and publication retain their separate approval gates.

Context used: the [approved task plan](../plans/task_m1_25.md), implementation plan, [Stage 2 report](task_m1_25_stage2.md), root/tests/docs rules, contributor guidance and existing template/skill manuals. Existing Python diagnostics and `unittest` CLI fixtures provided language and test conventions; no governance checker already existed. Python standard-library parsing is appropriate for the approved bounded Markdown subset without adding a parser dependency. This does not select a runtime-manager language. Apple technical expertise is not applicable to this documentation-checking stage; its previously reviewed inventory is validated as data, without GPU work.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/check_governance.py` | 302 lines; offline document paths, discovery/routing and pinned-source inventory checker; optional `--root` and script-relative default |
| `tests/docs/test_check_governance.py` | 468 lines; 35 public-CLI tests with isolated synthetic repositories and success/rejection subcases |
| `.github/workflows/documentation.yml` | 28 lines; PR-to-master and manual checks on hosted Ubuntu/Python with verified immutable action pins |
| `.github/ISSUE_TEMPLATE/task.yml` | Extend existing scope, verification and reference prompts; preserve nine field IDs |
| `.github/pull_request_template.md` | Link requirement/reuse/guidance decisions and documentation impact; clarify actual verification context and limitations |
| `mydocs/_templates/task_plan.md` | Add relevant rules, reuse and pinned expertise prompts; retain approved document-location judgment and Pear's docs root |
| `mydocs/_templates/task_impl_plan.md` | Define planned inputs, tools/settings/evidence and explicit stage approval dependency |
| `mydocs/_templates/stage_report.md` | Add actual context, approved/actual locations, evidence scope and unavailable/unperformed results |
| `docs/contributing.md` | Document offline commands, coverage and manual-review limits |
| Task/implementation plans and `mydocs/orders/20260928.md` | Record Stage 2 approval and Stage 3 completion; #25 remains In progress pending final reporting/publication |
| `mydocs/working/task_m1_25_stage3.md` | This report |

## Body Change Scope / Lossless Preservation

All artifact locations match the approved task/implementation plans. Five existing templates received narrow additions inside existing sections; their Markdown headings and nine Issue field IDs were preserved. They allow reasoned `Not applicable`, separate planned verification from performed results and reuse existing evidence/location sections. Related registration/start/stage/final skills and indexes were reviewed; no further manual or skill edit was needed.

The checker scans root README/agent entrypoints, required scoped rules, Markdown below `docs/` and the Pear router. Contained document-directory symlinks are traversed; escaping paths and directory cycles fail with diagnostics. Historical `mydocs/` artifacts/templates and unrelated root `analysis/` and `research/` are excluded from input scanning. Linked local destinations can still be checked for existence without scanning their bodies. Expected public-guide/metadata routing relationships are checked independently of the wording of their labels.

P01-P16/E01-E05 remain exactly the same 21 dependency rows as the planning base. Framework attribution, `.hyper-waterfall/version.json`, historical #22 records and both mode-120000 discovery symlinks are unchanged. This stage changes no host/runtime code, schema, manager language, security configuration or other worktree. No empty runtime/profile/manager directory or `.porting` state was created. The checker uses the reviewed Apple metadata from Stage 2; it neither replaces that source review nor changes the pin.

## Verification Results

Execution context: local Python `3.14.4`, Ruby `2.6.10` with Psych `3.1.0`, and installed actionlint `1.7.12`. Tests use temporary redistributable text/JSON fixtures and invoke the actual checker CLI from unrelated working directories. No network, credentials, game files or GPU tools are needed by the checker/tests. These are documentation and synthetic-fixture results, not host/game or performance qualification.

### Planned commands and results

Ran the following Stage 3 implementation-plan block verbatim under `bash -e`:

```sh
python3 tools/check_governance.py
python3 -m unittest discover -s tests/docs -p 'test_*.py' -v
ruby --disable-gems -rpsych - <<'RUBY'
issue = Psych.safe_load(File.read('.github/ISSUE_TEMPLATE/task.yml'))
abort 'Issue body missing' unless issue.is_a?(Hash) && issue['body'].is_a?(Array)
ids = issue['body'].map { |field| field['id'] }.compact
abort 'Duplicate Issue field IDs' unless ids.uniq == ids
workflow = Psych.safe_load(File.read('.github/workflows/documentation.yml'))
abort 'Workflow jobs missing' unless workflow.is_a?(Hash) && workflow['jobs'].is_a?(Hash)
puts 'PASS: Issue and workflow YAML parsed; body IDs unique; jobs present'
RUBY
git diff --check
git diff --stat a75237a
```

| Check | Actual result and scope |
|---|---|
| Repository checker | PASS: `18 documents, 101 local targets; skill routing and source inventory consistent (offline)` |
| Fixture suite | All 35 tests passed in 7.627 seconds; no skips |
| Ruby/Psych YAML checks | PASS: Issue/workflow parsed, Issue IDs unique, workflow jobs present |
| Whitespace | `git diff --check` passed |
| Integrated diff review | Reviewed tracked diff from `a75237a` plus the new checker, tests and workflow; only approved stage/task paths changed |
| Additional workflow validation | `actionlint .github/workflows/documentation.yml` exited 0 |
| Preservation checks | PASS: 21 P/E rows, framework notice/version, discovery links and absence of future implementation/porting directories |

The complete planned-command output is retained locally at `/private/tmp/pear-task25-stage3/verification.log`. These source identities bind the final checker, tests and workflow to that run:

| Input | SHA-256 |
|---|---|
| `tools/check_governance.py` | `8b6111b15a7690d24e53f0cbdf7e839f698192c280fce8c5af323162cacf3758` |
| `tests/docs/test_check_governance.py` | `68819407288a73e8e0b44ab9f44d29d697a630a68beb6d713c0d9f3085ab5f19` |
| `.github/workflows/documentation.yml` | `80a54e4da03d64ae6f4823223dd84e86adeeaa956ed0095eba78106fbdfa6c4d` |

### Rejection coverage and resolved findings

Tests cover missing required files; broken inline/image/reference-definition targets; plain/angle destinations and optional titles; source-relative and URL-escaped paths; query/fragment path handling; external/code/comment exclusions; directory targets; wrong/missing/escaping discovery links; router links that name or reach the wrong resource; malformed inventory types/JSON; moving/short/nonhex revisions; mismatched repository/plugin/skill/reference/tool identities, URLs and requirements; and default-root/CLI exit behavior. The revision test also deliberately accepts a consistent but unverified full SHA, demonstrating that the checker validates structure rather than remote existence.

Independent review found and resolved three concrete gaps before completion:

- A same-line triple/quad-backtick code span could be mistaken for a fence and hide a following real link. Fence recognition now rejects backticks in the info string; regression cases require the real missing link to fail.
- Recursive globbing skipped symlinked document directories. Explicit contained traversal now inspects internal aliases, rejects external aliases and reports ancestor cycles; fixtures prove both traversal and rejection.
- Windows drive-absolute destinations could be mistaken for an external URL scheme. They are rejected before scheme exclusion, with plain and angle-form cases.

Initial suite failures also exposed two test assumptions, not production requirements: invalid `--root` uses argparse exit 2, and uppercase full hexadecimal revisions are valid when their pinned URLs agree. Expectations were corrected and the consistent-uppercase positive case added. The final suite and independent reproductions passed; no actionable review finding remains.

### CI configuration and source verification

The workflow runs the two approved commands on every PR targeting `master` and manual dispatch. It uses `ubuntu-24.04`, Python `3.12`, a five-minute job timeout, `contents: read`, and disabled checkout credential persistence. There is no path filter, secret dependency, `pull_request_target`, GPU or runtime job.

Official release/tag metadata and the pinned README/action manifests were checked on September 28, 2026:

| Action | Reviewed release and immutable revision | Primary source |
|---|---|---|
| `actions/checkout` | `v7.0.1`, `3d3c42e5aac5ba805825da76410c181273ba90b1` | [Release](https://github.com/actions/checkout/releases/tag/v7.0.1), [action.yml](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/action.yml), [README](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/README.md) |
| `actions/setup-python` | `v7.0.0`, `5fda3b95a4ea91299a34e894583c3862153e4b97` | [Release](https://github.com/actions/setup-python/releases/tag/v7.0.0), [action.yml](https://github.com/actions/setup-python/blob/5fda3b95a4ea91299a34e894583c3862153e4b97/action.yml), [README](https://github.com/actions/setup-python/blob/5fda3b95a4ea91299a34e894583c3862153e4b97/README.md) |

Both actions declare Node 24 and document runner `2.327.1` or later. The [official Ubuntu image inventory](https://github.com/actions/runner-images/blob/7ef9dd0112f1827264dbca2dff8b13eb9f1a5534/images/ubuntu/Ubuntu2404-Readme.md), image `20260920.314.1`, lists Python `3.12.14` in the tool cache. Detailed local source-verification metadata is retained at `/private/tmp/pear-task25-stage3/action-source-verification.json`. This establishes the selected source/prerequisite review, not a successful remote run.

### Verification limitations

- GitHub CI and its Python 3.12 environment have not run; local `python3.12` is unavailable. The actual completed tests used Python 3.14.4. Record remote results only after approved PR publication.
- The checker supports a bounded Markdown subset. It does not resolve reference uses, validate heading fragments, parse raw HTML links or cover nested/escaped Markdown edge cases. New Stage 3 prose adds no link fragments; unsupported forms and future anchors require manual review.
- Inventory checks establish shape and internal provenance consistency, not remote source availability, factual correctness or installed-tool availability.
- No host regression, signing, runtime/game, Steam, GPU or performance execution was needed or performed for these changes. Existing qualification boundaries remain in force.

## Residual Risks

- The first actual GitHub run can expose hosted-environment or repository-setting issues that local YAML/actionlint checks cannot establish.
- The bounded parser requires manual review for unsupported Markdown constructs; successful automation must not be described as full document correctness or agent comprehension.
- #1/#3 and remote master may advance before publication. Recheck live state and preserve concurrent changes when preparing the final report/PR.

## Impact on Next Stage

All three implementation stages now have artifacts, local verification and reports. After approval of this report, prepare the final acceptance mapping, recheck integration state, complete the final report and daily board under the existing workflow. Final-report approval precedes publication of an open PR to `master`; CI results, merge and cleanup remain subsequent work. No Issue closure or task completion is inferred from this stage alone.

## Approval Request

Review the Stage 3 artifacts and verification results, then approve proceeding to final-report preparation. PR publication requires the subsequent final-report approval; this report does not authorize publication or merge by itself.
