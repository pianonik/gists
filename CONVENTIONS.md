# Conventions these skills assume

The skills in this marketplace were written around a particular way of working.
They will function without you adopting all of it, but a few of these are
load-bearing, and the skills say so where it matters. This file is the single
place they point at rather than each restating it.

## Fail loud, never degrade

If a skill cannot work out something it needs — the base branch, the build
command, where the tracker lives — it stops and says what is missing. It does
not guess a plausible default and carry on.

The same applies to code these skills write or review: prefer a crash to a
silent fallback, because a fallback hides a logic error that then ships. Where a
skill reviews code, "a fallback was added without being asked for" is a finding.

Asking the user is not a fallback. Several skills ask one question and then
offer to record the answer in the repo so they never have to ask again.

## The user owns the commit

No skill in this marketplace commits on your behalf except the ones whose entire
job is committing (`/commit`), and the batch runners, which commit only on
throwaway local branches. Everything else edits files and stops. This is
deliberate: a review or a doc update that quietly commits is a review you cannot
inspect before it lands.

## history.md is newest-first

Where a project keeps a `history.md`, new entries go at the **top**, under a
`## YYYY-MM-DD` heading. `/updatex` and `/updateitems` both depend on this, and
the trimmer that keeps the file from growing without bound splits on exactly
that heading shape.

Trimming moves old entries into `history-archive.md`. It never deletes them.

## Worktree branches are local and disposable

`/mkwt`, `/wtmerge`, `/fwtmerge`, `/sequencework` and `/projectreview` all share
one convention:

- A worktree lives at `<main repo root>/.claude/worktrees/<name>`, **inside** the
  main checkout, never as a sibling directory beside it.
- Its branch is `worktree-<name>`.
- **That branch is never pushed.** Only the base branch is. The feature branch is
  a throwaway label; the durable, backed-up copy of the work is the base branch
  after a merge.
- `.claude/worktrees/` goes in `.git/info/exclude`, which is per-clone and not
  versioned, so the skills check for it every time rather than assuming.

If you push worktree branches, `/wtmerge` and `/fwtmerge` will still work, but
you will accumulate remote branches they never clean up.

## Worktrees do not isolate code outside the repo

A worktree is a second checkout of *this* repo. A sibling checkout, a linked
package, or a shared library directory that lives outside it is shared by every
worktree at once. Two jobs editing that shared code will corrupt each other no
matter how the worktrees are arranged. `/sequencework` and `/projectreview` both
enforce a limit of one job per batch touching anything outside the repo.

## Testing goes through the project's own automation

The `iterate` skills refuse to drive an application with AppleScript, `osascript`
or desktop UI-scripting, and refuse to take screenshots with `screencapture`.
Both are unreliable and both require a human sitting there. If a project cannot
be driven by a script, that is worth fixing before iterating on it.

## No caching, no premature optimization

Caching is a last resort taken when a measurement demands it, not a default. In
review skills, "caching added with no demonstrated performance need" is a
finding, as is per-frame allocation on a hot path — the two are not
contradictory, they are the same rule applied at the two ends of the scale.

## No backward-compatibility shims before a first release

Pre-release, when something changes, change every call site. A compatibility
shim written before anyone depends on the old behaviour is dead weight that
outlives the reason for it.

## Dates come from the machine

Any skill stamping a date runs `date +%Y-%m-%d` first. Sessions cross midnight
and conversation context gets compacted; a date remembered from earlier in a
conversation is not trustworthy.
