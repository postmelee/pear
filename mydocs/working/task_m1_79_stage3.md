# Task #79 Stage 3: reviewed integration and retirement gates

Issue: [#79](https://github.com/postmelee/pear/issues/79)
Implementation plan: [task_m1_79_impl.md](../plans/task_m1_79_impl.md)

## Stage Purpose and Artifacts

Verify and integrate the four component guide successors, and prepare the
coordinating Pear documentation PR. Old-ref retirement is a post-merge operation:
keep the aliases until Pear's published links also use master. The Issue will
carry the actual Pear merge/CI and guarded cleanup readback.

| Component PR #3 | Integrated master |
|---|---|
| [pear-wine](https://github.com/postmelee/pear-wine/pull/3) | `258a5711b307b5ca62e793b6bf00a1c65feb7b6e` |
| [pear-fex](https://github.com/postmelee/pear-fex/pull/3) | `15915d4f1e9c6525786230c361816fe1e829731c` |
| [pear-dxmt](https://github.com/postmelee/pear-dxmt/pull/3) | `b4c34b8a544cfdb244ea42949e5880860b442794` |
| [pear-runtime](https://github.com/postmelee/pear-runtime/pull/3) | `0e79b1f1f436112241ec0ff38ac38dc2025c2fef` |

## Body Change Scope / Lossless Preservation

The independent review accepted 18 existing Markdown files: 13 current guides and
five historical URL-only repairs. Existing SHA occurrences, upstream README text,
source/configuration/workflows/locks/notices remain unchanged. 45 command blocks
match except the one approved fetch-ref substitution. Historical report prose
matches its fixed Task77 baseline with exactly one URL replacement per file.
No format/schema/source/API behavior changed. All locations match the plan.

## Verification Results

- Independent exact-diff review: no blocking findings; 178 relative links resolve
  through complete Git trees. The review initially compared historical links to an
  already-updated HEAD; the collector was corrected to fixed pre-migration bases
  and rerun. The failed collector draft remains local; it was not accepted evidence.
- Four component PRs target master, preserve reviewed heads and three-file
  Markdown allowlists, and merge as two-parent commits with exactly the reviewed
  trees. No component checks/statuses ran; this is not a CI pass. No new review
  request or comment blocked integration. Source equality supports reuse of the
  exact local document checks, not any new runtime execution claim.
- Nine retrievable relevant historical comments/review messages and 83 Issue/PR
  bodies contain no direct old component branch URLs. Textual history stays intact.
- Pear's fresh Stage2 run passed 121 document tests. The test/checker/fixture inputs
  and current guides are unchanged since that run; reuse it for report-only edits.
  Governance, incremental notices and diff --check pass again before this commit.
- 29 existing roots pass HEAD/branch/status/existing-local-ref comparison before
  publication. The separate historical runtime documentation checkout was also
  enumerated. New task checkouts alone have updated remote HEAD caches.

Git 2.53.0, gh 2.89.0, Python 3.13.5. Independent review SHA256:
`243b87a81acdbfa82822ae5fb412ccc597abded89a67445e90cf7957bbeb7295`.
The original source/build/tool pins and retained input/output bytes were not edited.
No new build, native/game, signing, installation or full private-state rehash.

## Artifact Disposition

Original debug worktrees/local task56 branches, producer roots, inputs, outputs and
#47 remain protected. New task scratch plus Pear checkout measured 108,343,350
logical bytes / 113,168,384 stat-allocated bytes; filesystem available was
16,134,385,664 bytes. Shared Git overhead and concurrent changes are not attributed.
No artifact deletion or reclaimed-space claim. Raw inventories remain private.

## Post-merge Retirement and Recovery

After Pear's reviewed PR merges, freshly verify all four master tips contain their
Stage1 tips, no old-branch PR/rule/automation consumer remains, current links work,
and each old remote ref still equals its recorded tip. Delete only those four refs
with an exact-old-value Git lease; verify all other remote refs unchanged. Keep
local task56 branches/upstream settings for frozen consumers; never pull/reset them
to follow master. New work uses a fresh checkout. Issue #79 records the actual
outcome; deletion is not yet performed at this report's prepublication checkpoint.

If restoration is separately required, recreate the named remote ref at its Stage1
commit using GitHub's create-ref API or an exact Git push to an absent ref. Do not
rewind master or move any local producer root. These old commits remain master
ancestors. Unknown external clones/bookmarks and links embedded in older immutable
document versions may still use the retired name; consult current guides and the
recorded commit path. History is not rewritten to alter old documentation blobs.

## Handoff

The requested migration is ready for coordinating Pear publication and guarded
post-merge retirement. Existing Megabonk/WGI work and qualification limits are
unchanged; no runtime candidate or execution authorization is renewed.
