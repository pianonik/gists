# worktree-batch

Git worktrees used as disposable workspaces, and batches of unattended Claude
sessions that pile their work onto a single branch.

Everything here is repo-neutral: the base branch, the commit-subject convention,
the build command and the tracker are all worked out from the repo at run time,
never assumed. Where something can't be worked out, the skill stops and says
what's missing.

## The shared convention

All five skills agree on this, and it's worth understanding before using any of
them:

- A worktree lives at **`<main repo root>/.claude/worktrees/<name>`** — inside
  the main checkout, never as a sibling directory beside it.
- Its branch is **`worktree-<name>`**.
- **The branch is never pushed.** Only the base branch is. The feature branch is
  a throwaway label; the durable copy of the work is the base branch after a
  merge. This avoids remote-branch bookkeeping entirely for work that lives a
  day or two.
- `.claude/worktrees/` goes into `.git/info/exclude`, which is per-clone and not
  versioned — so every skill checks for it rather than assuming.

If you'd rather push feature branches, these still work; you'll just accumulate
remote branches they don't clean up.

## The skills

**`/mkwt <name>`** — creates the worktree and branch off the base branch, checks
that Git LFS content actually smudged if the repo uses LFS, and then **moves the
session into it**, so subsequent work happens in the worktree you just made
rather than in the main checkout.

**`/wtmerge [message]`** — the two-way sync. Commits the worktree's branch
locally, merges it into the base branch **in the base branch's own worktree**
(you can't check out a branch that's already checked out elsewhere), pushes the
base branch, then merges the base branch back down into the feature branch.
Stops at the first conflict rather than resolving anything.

**`/fwtmerge [message]`** — the same, forward only. No merge back down, so the
feature branch may end up behind. Use it for a final landing before deleting the
worktree.

**`/projectreview [repo…]`** — reviews recent commits in one or more repos
against the tracker and flags partially-completed, broken, and inefficient work.
It then **writes, but does not run**, a script that creates one worktree per
follow-up job, each carrying a prompt written to stand alone in a fresh
unattended session. You run the jobs whenever you like, or never. Can wait a set
period before reviewing, so it picks up work that lands in the meantime.

**`/sequencework [focus]`** — the batch runner. Asks how many jobs and what to
pick them for, reviews the project, carves the findings into that many jobs,
gets each **approved one at a time** with a suggested model, then runs them in
sequence. Each job is cut from a `pending` branch, run headless, fast-forward
merged back into `pending`, and its worktree deleted. One build at the end with
every merge in it.

`pending` is the point: at the end there's exactly one branch holding
everything, in a worktree, waiting for you to look at it before it lands. The
skill never touches the base branch and never pushes. It records progress in a
state file and is resumable with `--resume` after a kill or a reboot, including
part-way through a job.

## Which of the two batch skills

`/projectreview` sets work up and stops. `/sequencework` sets work up, gets it
approved, and runs it.

Use `/projectreview` when you want to look at the jobs first, run them at your
own pace, or run several at once in separate terminals. Use `/sequencework` when
you want a bounded amount of work to happen unattended and arrive as one branch.
