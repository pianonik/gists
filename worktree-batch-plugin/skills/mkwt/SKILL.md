---
name: mkwt
description: Create a transient feature worktree at <repo-root>/.claude/worktrees/<name> with a new local branch worktree-<name> off the repo's base branch, then cd the session into it. Use when the user says "mkwt", "/mkwt <name>", or asks to create a worktree.
tools: Bash, Read
---

# mkwt

Create a transient feature worktree for the current repo, in the one sanctioned
location, and land the session inside it.

**The location rule:** worktrees live at `<repo-root>/.claude/worktrees/<name>` —
**inside** the main checkout, **never** as a sibling directory beside it. A
sibling directory escapes the repo's own ignore rules and gets picked up by
tooling that scans the parent directory. After creating it, **always `cd` into
the new worktree** so subsequent work happens there. Building or editing in the
main checkout while believing you are in the worktree is the classic way to lose
an afternoon.

The new branch is `worktree-<name>` — `/mkwt drag` gives branch `worktree-drag`
at `.claude/worktrees/drag`. Branches are transient and **local-only**: never
pushed. Work returns to the base branch via `/wtmerge` or `/fwtmerge`.

## Arguments

`/mkwt <name>` — `<name>` is required. If missing, ask for it; don't invent one.
An optional second argument is the base ref, which otherwise defaults to the
repo's own base branch as resolved in step 1.

## Procedure

Run with Bash. Stop and report at the first failure — never force.

### 1. Resolve the main repo root and the base branch

This works even when run from inside another worktree: the first entry of
`git worktree list` is always the main worktree.

```bash
MAIN_WT=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}')
[ -n "$MAIN_WT" ] || { echo "not in a git repo"; exit 1; }

# base branch -- detected, never assumed
BASE=$(git -C "$MAIN_WT" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -n "$BASE" ] || { git -C "$MAIN_WT" show-ref -q --verify refs/heads/master && BASE=master || BASE=main; }
git -C "$MAIN_WT" rev-parse -q --verify "$BASE" >/dev/null || { echo "base ref '$BASE' does not exist"; exit 1; }

NAME=<name>
WT_DIR="$MAIN_WT/.claude/worktrees/$NAME"
BRANCH="worktree-$NAME"
echo "main=$MAIN_WT  dir=$WT_DIR  branch=$BRANCH  base=$BASE"
```

Abort if `$WT_DIR` already exists, or if
`git show-ref --verify -q "refs/heads/$BRANCH"` says the branch already exists.
Don't reuse either — ask the user for a different name.

### 2. Ensure `.claude/worktrees/` is ignored in THIS clone

`.git/info/exclude` is per-clone and not versioned, so check every time:

```bash
git -C "$MAIN_WT" check-ignore -q .claude/worktrees/probe \
  || echo '**/.claude/worktrees/' >> "$(git -C "$MAIN_WT" rev-parse --git-common-dir)/info/exclude"
```

### 3. Create the worktree and branch

```bash
mkdir -p "$MAIN_WT/.claude/worktrees"
git -C "$MAIN_WT" worktree add -b "$BRANCH" "$WT_DIR" "$BASE"
```

### 4. Verify LFS content smudged — LFS repos only

Skip this entirely if `git lfs ls-files` is empty or `git lfs` isn't installed.

```bash
git -C "$WT_DIR" lfs ls-files | awk '$2=="-"' | head
```

Rows whose second column is `-` are un-smudged pointers: the file on disk is a
short text stub, not the real content, and a build would link the stub. Fix
with:

```bash
mkdir -p "$MAIN_WT/.git/lfs/tmp"
TMPDIR="$MAIN_WT/.git/lfs/tmp" git -C "$WT_DIR" lfs pull
```

`TMPDIR` must be on the **same filesystem as the repo**. git-lfs downloads into
the temp directory and then renames the file into place, and a rename across
filesystems fails with a "cross-device link" error. This bites whenever the
repo lives on a different volume from the system temp directory.

### 5. cd into it — mandatory, not optional

```bash
cd "$WT_DIR" && pwd && git branch --show-current
```

The Bash tool's working directory persists across calls, so this leaves the
whole session operating inside the new worktree.

### 6. Report

State the worktree path, branch name, the base ref and SHA it was cut from, LFS
status, and that the session's working directory is now the worktree. Add one
line: the branch is local-only and merges back via `/wtmerge` or `/fwtmerge`.

## Don't

- Don't create the worktree beside the repo instead of inside it.
- Don't push the new branch — ever.
- Don't reuse an existing directory or branch name — abort and ask.
- Don't skip the final `cd`.
