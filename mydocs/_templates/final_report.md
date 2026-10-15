# Final Report Template

This central template is for `mydocs/report/task_{milestone}_{issue}_report.md`. The final report closes the full plan-implementation-verification cycle, records acceptance criteria and residual risk for long-term retention, and requests approval before PR publication.

GitHub Issue: [#{issue}](https://github.com/postmelee/pear/issues/{issue})
Milestone: M{milestone}

## Work Summary

- Target Issue: #{issue}
- Milestone: M{milestone}
- Stage count: {N}
- Work purpose: {one-line summary}

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `{path}` | {change summary} | {impact area} |

## Document Location Verification

If this task created, moved, or edited product, user, contributor, external integration, API, architecture, or roadmap documentation, verify that the actual artifact location matches the "Document Location Judgment" in the task plan. If no such document changed, write `Not applicable` and explain why.

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| `{path or not applicable}` | `{path}` | `{path}` | OK/MISS | {evidence from task plan and diff} |

## Quantitative Before/After Comparison

| Metric | Before | After |
|---|---|---|
| {metric} | {value} | {value} |

If no quantitative metric applies, write "Not applicable" and explain why.

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| {criterion} | OK/MISS - {evidence} |

### Stage Verification Results

- Stage 1: {report link or verification summary}
- Stage 2: {report link or verification summary}
- Stage 3: {report link or verification summary}

## Retention Handoff

Reconcile remaining artifacts with current consumers under the [artifact retention procedure](../manual/artifact_retention_guide.md). Include ignored worktree evidence and recovery dependencies before any later worktree removal. Small text-only tasks may use a concise Git-backed handoff with reasoned `Not applicable` for material storage.

| Remaining artifact/root | State and owner/consumer | Identity/recovery reference | Retain reason / release condition |
|---|---|---|---|
| `{root or manifest reference}` | {retained, disposable, archived or unavailable; responsible tasks} | {required bindings, recovery store and restore procedure} | {needed claim/use, release event and checks} |

Cleanup outcome and limits: {completed versus deferred operations, unavailable material, unresolved consumers, worktree preservation decision and any separately measured storage results; no inferred deletion permission from task completion}.

## Residual Risks and Follow-up Work

### Residual Risks

- {remaining risk. Write `None` if there are none.}

### Follow-up Candidates

- {follow-up Issue candidate. Write `None` if there are none.}

## Approval Request to Task Requester

- If you approve the final report and acceptance criteria verification, proceed to PR publication.
