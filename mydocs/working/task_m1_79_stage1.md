# Task #79 Stage 1: integration branch dependencies

Issue: [#79](https://github.com/postmelee/pear/issues/79)
Implementation plan: [task_m1_79_impl.md](../plans/task_m1_79_impl.md)

## Stage Purpose

Freeze the source-preserving branch migration boundary. Context and documentation
locations follow the task plan; explicit migration authorization includes references
and old-remote cleanup, with existing runtime/debug state excluded.

## Artifacts

Fresh remote/whole-tree inventories, protected-root snapshot and exact target table:

| Repository | Current integrated commit / initial master target |
|---|---|
| pear-wine | `25d8970fb4db0fe4650cd7a2f5495680e60201a6` |
| pear-fex | `2f0f6a0b65f2fa42355cccad2bcd75576051c7e1` |
| pear-dxmt | `8ad610a936f2bff2fa38fc70f5ac92d93adcedaa` |
| pear-runtime | `9fb0a6c69e04651fe292f83014ad38a550959ff7` |

## Body Change Scope / Lossless Preservation

The exact existing historical cutover content is available at runtime
`9be1545f5a0845d3b14d4b845bf6bd413a224df3`: 19,460 bytes, SHA256
`4c07cd037cb71df1d487e50b6423c8acc3d04a7d534e99c21eb5a8544671542b`.
Five historical clickable links (Pear research plus four component Stage6
reports) will point there; recorded source/ref fields and claims stay unchanged.
Runtime's current acquisition command must fetch master instead of the retired
ref; all exact SHA pins and other commands remain. These observed locations and
the one command-argument exception are reconciled into the implementation plan.

## Verification Results

Fresh authenticated GitHub reads confirm all four PUBLIC, task56 defaults at the
listed tips, no master/tags/open component PRs/rulesets/effective branch rules,
environments or Pages. Protection GET404 is recorded as not configured/unavailable,
not a secret-policy clearance. Each also has the merged task77 publication branch.
83 Issue/PR bodies across five repositories have no live old-branch URL; seven
textual historical/plan mentions remain. No open PR needs retargeting.

Actions are enabled but the registered workflow/run lists are empty. Full-tree
inspection finds nine inherited FEX workflows and one DXMT workflow. Their
push/PR filters use upstream main; DXMT also has an independent v* tag trigger.
None is tied to task56/master. Keep these unchanged: rewriting main would activate
unrelated upstream build matrices. Local scheduled automation files have no
literal task56/component match. External clones/automation are not exhaustively
enumerable and are not claimed cleared.

Whole-tree Git searches classify live guidance URLs, one acquisition command,
dated evidence fields and retained local branch names. No executable source or
runtime lock depends on the old remote name. Checked-out local task56 branches
are retained. The independent remote audit SHA256 is
`f7c86d03a7f6807bde4513440c419d3489f0ff116ff916e94fbfc746a04bf567`.
`git diff --check` and incremental source notice check pass; no source changed.
No previous runtime test is reused as new branch-migration evidence.

## Artifact Disposition

29 existing/newly created Pear/component roots had HEAD/branch/status/local-ref
metadata captured before editing. The new Task79 worktree is the only permitted
working branch change; existing roots, local debug branches and ignored artifacts
are retained. New component checkouts are isolated sparse shared clones; no build
or runtime copies. Raw inventories stay local. No storage reclaimed or private
payload rehash claimed.

## Residual Risks and Next Stage

Immediate SHA/default guards are still required before each mutation. Current
docs must be integrated before old remote deletion. Unknown third-party clones
may need to fetch master manually. Source/build/tool pins remain authoritative.
Proceed within the requester's approved migration scope; Stage1 does not itself
change any remote branch or authorize runtime work.
