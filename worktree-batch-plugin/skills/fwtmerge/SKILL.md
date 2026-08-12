---
name: fwtmerge
description: One-way FORWARD merge from the current git worktree's local-only feature branch INTO the repo's base branch — commit the feature branch locally, merge it into the base branch and push the BASE branch (the only pushed ref). Unlike wtmerge, it does NOT merge the base branch back into the feature branch. Use when the user says "fwtmerge", "/fwtmerge", or asks to forward the current worktree's changes into the base branch one way only.
tools: Bash, Read
---

# fwtmerge

One-way **forward** merge from the **current feature worktree** into the repo's
**base branch**:

1. Commit the current worktree's branch **locally** (no push).
2. Merge the current branch **into the base branch**, and **push the base
   branch**.

That's it. **Unlike `/wtmerge`, there is no step merging the base branch back
into the feature branch.** This skill only flows work upward. Afterwards the
feature branch may be behind the base branch — that's expected. If you also want
the back-merge so the feature branch stays in sync, use `/wtmerge`.

The natural use is a final landing before deleting the worktree, and the end of
a `/sequencework` batch, where the accumulated `pending` branch goes home.

**Feature branches stay local-only by design.** Only the base branch is ever
pushed; the feature branch is a throwaway label. This is why step 1 uses a plain
`git commit` rather than any commit wrapper the repo may have — a wrapper that
pushes would create exactly the upstream feature branch this workflow avoids. If
the repo's wrapper shapes the commit subject a particular way, replicate that
format by hand rather than calling the wrapper.

The repo is checked out as **multiple worktrees of one repo**. You **cannot**
`git checkout <base>` in the feature worktree, because the base branch is
already checked out in another worktree — so the merge must run *inside the base
worktree*.

**Precondition:** the base worktree has no uncommitted changes. Step 2 verifies
this and aborts if it's dirty.

## Commit message

If the user passed text after `/fwtmerge`, use it verbatim. Otherwise write a
concise message summarizing the worktree's uncommitted changes. If nothing is
uncommitted, skip the commit entirely.

**Match the repo's own commit-subject convention** — read it out of
`git --no-pager log --oneline -10` and reproduce whatever consistent prefix or
shape you find, or keep it plain if the subjects are plain.

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
worktree. Abort if `BASE_WT` is empty: no worktree has the base branch checked
out, so there is nowhere to merge into.

### 1. Commit the current branch LOCALLY (no push)

```bash
cd "$CUR_WT"
if [ -n "$(git status --porcelain)" ]; then
  git commit -a -m "<subject matching the repo's convention>"
else
  echo "nothing to commit (local-only branch — nothing to push)"
fi
```

`git commit -a` stages tracked modifications and deletions only. `git add` any
untracked files that belong in the commit first. Do not push the feature branch.

### 2. Merge into the base branch, and push it

This is the **only** push in the whole skill.

```bash
cd "$BASE_WT"
[ -z "$(git status --porcelain)" ] || { echo "base worktree DIRTY — aborting"; exit 1; }
git fetch origin
git merge --ff-only "origin/$BASE" 2>/dev/null || true   # advance base if it is behind
git merge --no-edit "$BRANCH"
git push
```

On conflict: **stop**. Report the conflicted files
(`git diff --name-only --diff-filter=U`). Do not push. Leave the merge in
progress; `git merge --abort` in the base worktree backs out cleanly.

If the push is rejected because someone else pushed first,
`git pull --rebase origin "$BASE"`, resolve, and push again. Never force-push.

### 3. Report

State plainly:

- the local commit that was made, or "nothing to commit" — not pushed;
- the base merge result, the new base SHA, and that **the base branch was
  pushed**;
- that this was a **forward-only** merge, so the feature branch may now be
  behind the base branch — use `/wtmerge` to re-sync it.

Show `git --no-pager log --oneline -3` for both worktrees so the user can see
where each end stands.

## Teardown (separate from this skill)

The user deletes the worktree themselves when they're done. Once the work is on
the base branch:

```bash
git -C "$BASE_WT" worktree remove "$CUR_WT"
git -C "$BASE_WT" branch -d "$BRANCH"     # -d is safe: it refuses if unmerged
```

There is no remote branch to delete, since it was never pushed.

## Don't

- Don't merge the base branch back into the feature branch — that's what makes
  this the forward-only variant. Use `/wtmerge` if you want it.
- Don't `git checkout` the base branch in the feature worktree — it will fail.
- Don't push the feature branch — only the base branch is pushed.
- Don't use a commit wrapper that pushes; replicate its subject format instead.
- Don't force-push, skip hooks, or auto-resolve conflicts.
- Don't proceed past a dirty base worktree or an unresolved conflict.
