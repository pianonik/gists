---
name: commit
description: Commit the current session's work with a detailed message written from the conversation rather than from diff archaeology, matching whatever commit-subject convention the repo's own git log shows and using the repo's own commit wrapper script if it has one. Handles nested independent repos and a rejected push. Use when the user says "commit", "/commit", or asks to commit the session's changes.
tools: Bash
---

# commit

Commit what the current session changed. This is the "just commit it" path: a
detailed message written from what happened in the conversation, with all
modified files swept in unless the user asks for a subset.

**Source of truth for the message is THIS conversation, not the diff.** The
conversation knows why a change was made; the diff only knows what changed.
Don't go spelunking through `git diff` to reconstruct a narrative you already
have. Sweeping in an unrelated in-progress file is acceptable — describe *your*
work; you needn't enumerate every swept file.

## Step 1 — Work out this repo's conventions

Never assume. Two things to settle, both cheap:

```bash
git rev-parse --show-toplevel
git --no-pager log --oneline -20
ls -1 scripts/ tools/ bin/ 2>/dev/null | grep -iE '^(commit|cmt|ci)' || true
```

**The subject convention.** Read the last twenty subjects. If they consistently
carry a prefix or shape — a branch tag, a `type(scope):` conventional-commit
prefix, a ticket id, an area name — reproduce it exactly. If they're plain
sentences, keep yours plain. A repo whose log is uniform and whose newest commit
breaks the pattern looks like a mistake, because usually it is one.

**A commit wrapper.** Many projects have a script that wraps `git commit` to
stamp the subject, sign, push, or run a formatter afterwards. If the repo has
one — check `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md` and the scripts
directory — **use it rather than calling `git commit` directly**, and read it
first, because two things about it change what you do:

- **Does it add the subject prefix itself?** If so, do NOT prepend the prefix
  yourself; you'd get it twice.
- **Does it push?** If so, say so to the user *before* running it. A wrapper that
  pushes on a branch that shouldn't be pushed — a local-only worktree branch, for
  instance — is the wrong tool; use a plain `git commit` replicating its subject
  format instead.

Also check how the wrapper takes its message. Some read the message from
standard input when standard input is not a terminal, which is always the case
under an agent's shell — meaning a message passed as an argument is silently
ignored and an empty message gets committed. If in doubt, pipe the message in:

```bash
printf '%s\n' "$MSG" | scripts/<wrapper>
```

## Step 2 — Write the message

- **Subject**: one imperative line, carrying whatever prefix the convention
  requires.
- **Body**: bullets covering the logical changes — features, fixes, doc updates.
  Name key files where it helps a future reader.
- Be honest but don't over-scope. If the sweep pulls in unrelated in-progress
  files, that's fine; describe your work.

Avoid backticks and `$` in the message text if you're piping it through a shell,
unless you're confident about the quoting. Command substitution inside an
unquoted heredoc will eat them.

## Step 3 — Commit

With a wrapper, use it. Without one:

```bash
git commit -a -m "<subject>" -m "<body>"
```

`git commit -a` stages modifications and deletions to **tracked** files. It
does not pick up **untracked** files — a newly created file is silently left
out. If the session created new files that belong in the commit, `git add` them
first. This is the single most common way a "successful" commit turns out to be
missing half the work.

## Step 4 — Nested independent repos

Some trees contain independent git repos that the outer repo ignores — a vendored
library, a subproject with its own history, a sibling checkout. **`git commit`
in the outer repo will not touch them**, and the work in them is silently left
uncommitted.

If this session edited files in more than one repo, run the commit once per
repo, each with its own message. Find them by checking the paths you actually
edited:

```bash
git -C <path> rev-parse --show-toplevel
```

Report each commit separately.

## Step 5 — If the push is rejected

A wrapper that pushes, or your own push afterwards, can be rejected because
someone else pushed first. Integrate and retry rather than forcing:

```bash
git pull --rebase origin <branch>
# resolve any conflict; running-log files like history.md or a TODO often collide
# because several sessions prepend entries — keep BOTH sides, newest first
git add <resolved files> && git rebase --continue
git push origin <branch>
```

Never force-push to recover from this.

## Step 6 — Report

Report the resulting commit hash for each repo — `git -C <repo> log -1 --oneline`
— so the user can see exactly what landed, and say whether it was pushed.

If the wrapper printed errors *after* committing and pushing — a missing
formatter, a hook that isn't on your PATH — say what it was and that the commit
itself succeeded, rather than reporting a failure.

## Don't

- Don't reconstruct the message from `git diff` archaeology.
- Don't prepend a subject prefix by hand when the wrapper already adds it.
- Don't run a wrapper that pushes without telling the user first, and never on a
  branch that is meant to stay local.
- Don't force-push, and don't skip hooks.
- Don't assume `git commit -a` caught new files.
