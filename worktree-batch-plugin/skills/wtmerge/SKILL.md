---
name: wtmerge
description: Two-way sync between the current git worktree's local-only feature branch and the repo's base branch — commit the feature branch locally, merge it into the base branch and push the BASE branch (the only pushed ref), then merge the base branch back into the feature branch locally. Use when the user says "wtmerge", "/wtmerge", or asks to sync the current worktree with the base branch both ways.
tools: Bash, Read
---

# wtmerge

Two-way sync between the **current feature worktree** and the repo's **base
branch**:

1. Commit the current worktree's branch **locally** (no push).
2. Merge the current branch **into the base branch**, and **push the base
   branch**.
3. Merge the base branch **back into** the current branch **locally** (no push).

**Feature branches stay local-only by design.** Worktrees here are transient —
spun up for a day or two, merged occasionally, then deleted. To avoid
remote-branch bookkeeping, **only the base branch is ever pushed.** All the
durable, backed-up work lives there; the feature branch is a throwaway label.

This is why step 1 uses a plain `git commit` rather than any commit wrapper the
repo may have. A wrapper that pushes would create exactly the upstream feature
branch this workflow avoids. If the repo's wrapper also shapes the commit
subject a particular way, **replicate the subject format by hand** rather than
calling the wrapper.

The repo is checked out as **multiple worktrees of one repo** — the main
checkout on the base branch, plus a transient one per feature. You **cannot**
`git checkout <base>` in the feature worktree, because the base branch is
already checked out in another worktree. So "merge into base" must run *inside
the base worktree*, while "merge base back" runs here.

**Precondition:** the base worktree has no uncommitted changes. Step 2 verifies
this and aborts if it's dirty.

## Commit message

If the user passed text after `/wtmerge`, use it verbatim. Otherwise write a
concise message summarizing the worktree's uncommitted changes. If there is
nothing uncommitted, skip the commit entirely — there is nothing to push, since
the branch is local-only.

**Match the repo's own commit-subject convention.** Read it out of the log
before writing anything:

```bash
git --no-pager log --oneline -10
```

If the subjects carry a consistent prefix or shape — a branch tag, a
`type(scope):` conventional-commit prefix, a ticket id — reproduce it. If the
repo's wrapper script normally adds that prefix, add it yourself here, since
you're not calling the wrapper. If subjects are plain, keep yours plain.

## Procedure

Run these steps in order with Bash. **Stop and report at the first failure or
merge conflict — never force, never auto-resolve.**

### 0. Gather context

```bash
BRANCH=$(git branch --show-current)
CUR_WT=$(git rev-parse --show-toplevel)
MAIN_WT=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}')

BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -n "$BASE" ] || { git show-ref -q --verify refs/heads/master && BASE=master || BASE=main; }

BASE_WT=$(git worktree list --porcelain \
  | awk -v b="refs/heads/$BASE" '/^worktree /{p=substr($0,10)} $0=="branch "b{print p; exit}')
echo "branch=$BRANCH  cur_wt=$CUR_WT  base=$BASE  base_wt=$BASE_WT"
```

Abort if `BRANCH` is empty or equals `$BASE` — run this from a *feature*
worktree. Abort if `BASE_WT` is empty: no worktree currently has the base branch
checked out, so there is nowhere to merge into. Say that plainly; the fix is for
the user to check the base branch out in the main worktree.

### 1. Commit the current branch LOCALLY (no push)

```bash
cd "$CUR_WT"
if [ -n "$(git status --porcelain)" ]; then
  git commit -a -m "<subject matching the repo's convention>"
else
  echo "nothing to commit (local-only branch — nothing to push)"
fi
```

`git commit -a` stages tracked modifications and deletions only. If there are
**untracked** files that belong in the commit, `git add` them first. Do not
push the feature branch, and do not use a commit wrapper that would.

### 2. Merge the current branch INTO the base branch, and push it

This is the **only** push in the whole skill.

```bash
cd "$BASE_WT"
[ -z "$(git status --porcelain)" ] || { echo "base worktree DIRTY — aborting"; exit 1; }
git fetch origin
git merge --ff-only "origin/$BASE" 2>/dev/null || true   # advance base if it is behind
git merge --no-edit "$BRANCH"
git push
```

If the merge reports conflicts: **stop**. Report the conflicted files
(`git diff --name-only --diff-filter=U`). Do not push. Leave the merge in
progress so the user can resolve it with your help; `git merge --abort` in the
base worktree cleanly backs out if they prefer.

If `git push` is rejected because someone else pushed first, integrate and
retry: `git pull --rebase origin "$BASE"`, resolve any conflict, then push
again. Never force-push.

### 3. Merge the base branch BACK INTO the current branch (local, no push)

```bash
cd "$CUR_WT"
git merge --no-edit "$BASE"
```

Merging the base *ref* into the current branch is allowed even though the base
branch is checked out elsewhere — you aren't checking it out. **Do not push**
the feature branch. Same conflict rule: on conflict, stop and report;
`git merge --abort` backs out.

### 4. Report

State plainly:

- the local commit that was made, or "nothing to commit" — and note it was
  **not** pushed;
- the base merge result, the new base SHA, and that **the base branch was
  pushed**;
- the base-into-branch merge result and the new branch SHA (local).

Show `git --no-pager log --oneline -3` for both worktrees so the user can see
both ends are in sync.

## Teardown (separate from this skill)

When the user is done with a transient worktree they delete it themselves. This
skill does NOT. The clean teardown, once the work is on the base branch:

```bash
git -C "$BASE_WT" worktree remove "$CUR_WT"
git -C "$BASE_WT" branch -d "$BRANCH"     # -d is safe: it refuses if unmerged
```

Lowercase `-d` only deletes a branch fully merged into the current one, which is
the safety net. There is no remote branch to delete, since it was never pushed.

## Don't

- Don't `git checkout` the base branch in the feature worktree — it will fail.
- Don't push the feature branch in step 1 or 3 — only the base branch is pushed.
- Don't use a commit wrapper that pushes; replicate its subject format instead.
- Don't force-push, skip hooks, or auto-resolve conflicts.
- Don't touch shared code that lives outside this repo — out of scope here.
- Don't proceed past a dirty base worktree or an unresolved conflict.
