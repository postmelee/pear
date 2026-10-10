---
name: pr-merge-cleanup
description: |
  Apply cleanup after confirming a PR merge.
  Close the GitHub Issue, delete the remote publish/task{N} branch,
  clean up the local local/task{N} branch and separate worktree, and return to master.
  Invoke only after the PR is actually merged.
---

# PR Post-merge Cleanup

## Trigger

- The task requester explicitly says "cleanup after merge" or "clean up the task."
- This SKILL is invoked directly.

## Preconditions

- The target PR is actually merged on GitHub: `gh pr view {number} --json state,mergeCommit`.
- The task requester approved Issue close, or the PR body included `closes #N` and the Issue was automatically closed.

## Procedure

1. Check PR and Issue state.
   ```bash
   gh pr view {number} --json state,mergedAt,mergeCommit,headRefName
   gh issue view {N} --json state
   ```
   - If PR `state != MERGED`, stop immediately and report to the task requester.
2. Close the Issue only if it was not already closed.
   ```bash
   gh issue close {N}
   ```
3. Update `master`.
   ```bash
   git fetch origin --prune
   git checkout master
   git pull --ff-only
   ```
4. Delete the remote publish branch. Skip if the branch was already deleted by PR merge with `--delete-branch`.
   ```bash
   git push origin --delete publish/task{N} 2>&1 || echo "already deleted"
   ```
5. Reconcile the final report's **Retention Handoff** with current consumers using the [artifact retention procedure](../../manual/artifact_retention_guide.md). Inspect ignored/untracked evidence and recovery stores before removing or archiving a separate worktree; an app/Git snapshot alone does not establish their preservation. Verify required material is preserved or retain the worktree with its owner and release condition. Record the actual disposition and deferred cleanup.
   - Run the removal commands only when the dependency and preservation checks permit removal within the authorized scope. Use the host's managed-worktree lifecycle when applicable.
   ```bash
   git worktree remove ../{repo}-task{N}
   git worktree prune
   ```
6. Delete the local work branch only when it is no longer needed.
   ```bash
   git branch -d local/task{N}
   # Forced deletion requires explicit task requester approval: git branch -D local/task{N}
   ```
7. Final daily task board check: confirm the #{N} row in `mydocs/orders/{yyyymmdd}.md` is `Done` with a completion time.
8. Report the cleaned items briefly to the task requester.

## Verification

- `gh pr view {number}` shows `state == MERGED`.
- `git branch -vv | grep local/task{N}` has no output if the branch was deleted.
- `git ls-remote origin publish/task{N}` has empty output.
- `git worktree list` excludes a removed worktree, or the retained worktree has a recorded owner, dependency/recovery reason and release condition.
- `git branch --show-current` is `master`.

## Never Do

- Close an Issue when the PR is not merged.
- Delete another task branch or the main worktree.
- Run `git branch -D` without explicit approval; unmerged commits may be lost.
- Delete another worker's stash.

## Invocation

- Codex: `$pr-merge-cleanup` or the `/skills` menu
- Claude Code: `/pr-merge-cleanup`
