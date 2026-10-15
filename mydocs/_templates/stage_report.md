# Stage Report Template

This central template is for `mydocs/working/task_{milestone}_{issue}_stage{stage}.md`. A stage report records one Stage's implementation, verification, residual risk, and impact on the next stage, then requests approval to continue.

GitHub Issue: [#{issue}](https://github.com/postmelee/pear/issues/{issue})
Implementation plan: [`task_{milestone}_{issue}_impl.md`](../plans/task_{milestone}_{issue}_impl.md)
Stage: {stage}

## Stage Purpose

{Explain what this Stage was meant to resolve and where it fits in the implementation plan.}

Context used: {applicable specifications/scoped rules, approved reuse decision and selected skill/guide revision/version actually read; link unchanged plan context or give reasoned Not applicable.}

## Artifacts

| File | Change Summary |
|---|---|
| `{path}` | {change summary} |

## Body Change Scope / Lossless Preservation

{Describe documentation impact, approved versus actual locations, source preservation and rewrite scope; explain API/behavior preservation for code changes. Use Not applicable with a reason where appropriate.}

## Verification Results

Execution context: {actual tool/platform versions and availability, relevant settings, input/test identity and whether this was source review, a fixture, host or game execution. Separate diagnostics from performance runs.}

Evidence reuse: {identify prior input/revision-bound evidence and its unchanged claim scope, or `None`; list changes that invalidated prior evidence and the checks actually repeated. Reused results are not newly executed checks and do not replace approved required checks.}

Command run:

```bash
{verification command}
```

Result:

- {Actual outcome and key output summary, sanitized evidence link and coverage boundary}
- {Unavailable, skipped or unperformed checks and reasons; these are not passing results}

## Artifact Disposition

Reconcile the plan's lifecycle record using the [artifact retention procedure](../manual/artifact_retention_guide.md). Record actual retained, disposable, archived, unavailable or released material; distinguish planned cleanup from completed cleanup. A small task may summarize Git-backed text outputs and give reasoned `Not applicable` for material storage.

| Artifact/root | Actual state and outcome | Remaining owner/consumer | Identity/recovery reference | Retain reason / release condition |
|---|---|---|---|---|
| `{root or manifest reference}` | {state; operation performed or deferred} | {owner and consumers} | {bindings; restore-required/unavailable status and procedure} | {reason, release event, unresolved dependency} |

Storage observations: {if measured, separate logical/allocated/archive sizes and filesystem free-space change, with method/time and concurrent-work limits; otherwise state unperformed or Not applicable with reason}.

## Residual Risks

- {remaining risk. Write `None` if there are none.}

## Impact on Next Stage

- {context the next Stage must inherit. Write `None` if there is none.}

## Approval Request

- If you approve the Stage {stage} artifacts and verification results, proceed to the next stage.
