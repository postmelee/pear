# Implementation Plan Template

This central template is for `mydocs/plans/task_{milestone}_{issue}_impl.md`. The implementation plan turns an approved task plan into concrete Stage artifacts, verification commands, and commit messages.

Task plan: [`task_{milestone}_{issue}.md`](task_{milestone}_{issue}.md)
GitHub Issue: [#{issue}](https://github.com/postmelee/pear/issues/{issue})
Milestone: M{milestone}

Reference the task plan's applicable specifications/scoped rules, reuse rationale and selected technical guidance. In each Stage's Changes section, identify any approved changes to that context, including exact skill/guide source revisions and versions. Use `Not applicable` with a reason for irrelevant items.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | {title} | `{path}` | `{verification summary}` |
| 2 | {title} | `{path}` | `{verification summary}` |
| 3 | {title} | `{path}` | `{verification summary}` |

Each Stage's Verification section must define inputs, required tools/platform versions, settings, expected outcomes and evidence to retain. Record availability checked during planning or `Not checked`, plus planned checks that may remain unavailable. Commands below are planned work; performed results belong in stage reports.

For each reused result, name its input/revision identity and supported claim, the existing check and relevant false-success case, and the changes requiring revalidation. Distinguish reused evidence from checks to execute in this Stage; do not waive approved required checks.

## Document Location Check

Confirm that the actual Stage artifact locations match the "Document Location Judgment" in the task plan. If no document is created, moved, or edited, write `Not applicable` and explain why.

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| `{path or not applicable}` | `{path}` | `{path}` | OK/MISS | {if mismatch, approval is required before changing the plan} |

## Stage 1 - {Title}

### Artifacts

New:

- `{path}`

Modified:

- `{path}`

### Changes

- {Specifically describe what will be created or changed.}

### Verification

```bash
{verification command}
git diff --check
```

### Commit

```text
Task #{issue} Stage 1: {summary}
```

## Stage 2 - {Title}

### Artifacts

- `{path}`

### Changes

- {Specifically describe what will be created or changed.}

### Verification

```bash
{verification command}
git diff --check
```

### Commit

```text
Task #{issue} Stage 2: {summary}
```

## Stage 3 - {Title}

### Artifacts

- `{path}`

### Changes

- {Specifically describe what will be created or changed.}

### Verification

```bash
{verification command}
git diff --check
```

### Commit

```text
Task #{issue} Stage 3: {summary}
```

## Verification

- Run each Stage verification command before writing the stage report.
- Do not treat a Stage as complete when verification fails.
- If the plan must change, update the implementation plan first and get task requester approval.
- If a document location differs from the task plan judgment, update the task plan or implementation plan and get approval before implementing.

## Commits

- Each Stage commit bundles the Stage artifacts with `mydocs/working/task_{milestone}_{issue}_stage{N}.md`.
- Commit messages follow `Task #{issue} Stage {N}: {summary}`.

## Stage Dependencies

- Stage 2 starts after Stage 1 verification, report and task requester approval.
- Stage 3 starts after Stage 2 verification and report approval.

## Risks and Responses

- **{risk name}**: {response}

## Approval Request

- {Ask for approval of Stage split, artifacts, verification commands, and commit messages.}
