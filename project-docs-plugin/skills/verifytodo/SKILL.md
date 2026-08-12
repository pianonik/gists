---
name: verifytodo
description: Audit TODO.md against the real code and git history rather than trusting its status markers, then move work that has verifiably shipped into DONE.md, bring back any DONE.md claim that turns out to be incomplete, and report anything ambiguous for the user to rule on. Every move is listed at the end so it can be reversed. Use when the user says "verifytodo", "/verifytodo", or asks whether the TODO's statuses are actually true. ONLY for a repo whose tracker is a hand-edited TODO.md: if the repo has an items/ store (items/*.md with items/scripts/itemlib.py), stop and use /verifyitems instead, even when a TODO.md also exists — a stale hand-authored TODO.md often sits alongside a live item store.
tools: Read, Bash, Grep, Glob, Edit, Write, Agent
---

# verifytodo

Go through `TODO.md` and find out which status markers are **lies**.

A hand-edited TODO drifts in both directions. Work finishes and nobody updates
the marker, so the open list is padded with things already done — and the file
slowly turns into a changelog with the real work buried in it. Or something gets
marked done on the strength of a commit that only did half of it, and the
remainder becomes invisible. Both are worse than an empty file, because both are
confidently wrong.

This skill does not trust the markers. It checks each against the code and git
history, moves what it can prove into `DONE.md`, and hands back a list of every
move so you can reverse any you disagree with.

The flat-`TODO.md` sibling of `/verifyitems`.

## Step 0 — check for an item store FIRST (mandatory)

Before reading `TODO.md`, before anything else:

```bash
ls items/scripts/itemlib.py 2>/dev/null; ls items/*.md 2>/dev/null | head -3
```

If either produces output, this project's tracker is the **item store**, not
`TODO.md`. **Stop and tell the user to run `/verifyitems` instead.**

This check is unconditional. A repo can have both: a live `items/` store *and* a
stale hand-authored `TODO.md` still sitting at the root, large and entirely
plausible-looking. **The presence of `TODO.md` proves nothing. The presence of
`items/` is decisive.**

## What this is not

It does not record the current conversation — that's `/updatex`. It does not
produce a broad audit of dead code and doc drift — that's `/planning-review`,
which reports drift but deliberately never writes. This skill is the narrow one
that **corrects the tracker**.

## Run from the repo root

If **`TODO.md` isn't present**, say so and stop. `DONE.md` is optional; if
`TODO.md` exists but `DONE.md` doesn't, ask once whether to create it before
moving anything into it.

## Step 1 — Read the tracker

Read `TODO.md` in full. Extract the section list, each item's title, and its
status marker — **whatever markers this file actually uses.** Derive them; don't
assume a scheme. A file may use checkboxes, emoji, inline `[FIXED]` tags, or
position under a "landed" heading.

Skim `DONE.md`'s headers (`grep -nE '^#+ ' DONE.md`) so you know what has
already shipped. You should not expect that code to be missing.

## Step 2 — Establish git ground truth

```bash
git -C . log --oneline -40
git -C . branch -a
git -C . status --short
```

Note which branches merged and which are still live. Merge commits are the
evidence, as is whatever commit-subject convention the repo uses — read it out
of the log rather than assuming. A branch absent from `git branch -a` may mean
merged-and-deleted, which is normal.

## Step 3 — Check each marker against the code (the core)

- For every partially-done item, **verify the partial code is real.** An item
  can sit half-marked for months because someone wrote a plan and nothing else.
- For not-started and deferred items, confirm no surprise code already landed
  them. This is the most valuable drift to catch: an open item that has secretly
  finished.
- For `DONE.md` entries, spot-check only the ones whose claim looks suspect — a
  finished item whose feature you cannot find, or which the entry says covers
  two platforms when the commit touched one.

Fan out **parallel agents** (the Agent tool — `general-purpose` for
doc-versus-code reality checks, `Explore` for breadth) so file dumps stay out of
the main context. Group items by area, one agent per cluster. Give each the repo
path, the item text plus exact searches, and "report file references, read-only,
do NOT edit." Each reports, per item: shipped, partial, or not started, with
evidence.

Cheap cross-checks to do yourself while they run:

- An item whose branch the log shows as merged: consistent with real work.
- A `DONE.md` entry with no implementing code: drift; bring it back.
- Citations into the source that have drifted off the code.
- "UNCOMMITTED" or "commit this batch" notes while `git status` is clean —
  stale; the work shipped.

## Step 4 — Move the certain, report the ambiguous

- **Verified done** → move its whole section out of `TODO.md` into `DONE.md`,
  keeping its number or heading, and marked done the way the file already marks
  things. Never just flip a marker in place and leave it — a TODO that
  accumulates finished items buries the real work list.
- **Verified incomplete** — a `DONE.md` claim with no implementing code → move
  it back to `TODO.md`.
- **Mis-labeled but still open** → fix the marker in place.
- **Ambiguous** — mixed or partial evidence → **do NOT move it.** Report it and
  let the user decide. For example:

> Judgment calls (reported, not moved):
> - §5.7 marked partially done — the desktop path is present, the mobile path is
>   absent; consistent with it being a release blocker, so leaving it open.
> - §2.4 is in `DONE.md` — but no implementing code found for the second
>   platform; should this come back?

Only real code and git evidence justifies a move. A bare marker does not.

## Step 5 — Hand back

**Mandatory**: list every item you moved, with the file reference or commit that
justified it; any markers you fixed in place; and the ambiguous ones you left.

This list is the guardrail. Moving items on your own judgment is only acceptable
because every move is visible and reversible in one place.

## When to stop

After the moves, stop. **Do not commit** — the user owns that step.

## Don't

- Don't trust a status marker. That's the entire point of the skill.
- Don't move an item on a bare marker alone — code and git, or it doesn't count.
- Don't move anything ambiguous; report it.
- Don't delete entries; move them.
- Don't read all of `DONE.md`'s archive or all of `history.md`; grep for the
  specific item.
- Don't omit the hand-back.
- Don't `git add` or commit.
