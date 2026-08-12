---
name: updateplan
description: Re-derive TODO-parallel.md from TODO.md, double-checking every status claim against the actual code and git log rather than trusting the markers. Keeps the plan structural — independent streams, branches, ordering, integration mechanism, and a thin "mergeable or blocked right now" snapshot — and lets TODO.md own per-item status. Use when the user says "updateplan", "/updateplan", or asks to refresh or regenerate the parallel plan from the TODO. ONLY for a repo whose tracker is a hand-edited TODO.md: if the repo has an items/ store (items/*.md with items/scripts/itemlib.py), stop and use /updateitemplan instead, even when a TODO.md also exists — a stale hand-authored TODO.md often sits alongside a live item store.
tools: Read, Bash, Grep, Glob, Edit, Write, Agent
---

# updateplan

Regenerate `TODO-parallel.md` (the **how** — independent streams of work,
branches, ordering, integration mechanism) from `TODO.md` (the **what** — the
open items and their status markers), **after independently verifying that
status against the real code and git history.**

## Step 0 — check for an item store FIRST (mandatory)

Before reading `TODO.md`, before anything else:

```bash
ls items/scripts/itemlib.py 2>/dev/null; ls items/*.md 2>/dev/null | head -3
```

If either produces output, this project's tracker is the **item store**, not
`TODO.md`. **Stop and tell the user to run `/updateitemplan` instead.** Do not
edit `TODO.md` or `DONE.md`.

This check is unconditional and comes first. It is NOT conditional on `TODO.md`
being missing — a repo can have both: a live `items/` store *and* a stale
hand-authored `TODO.md` and `DONE.md` still sitting at the repo root from before
the store existed, large and entirely plausible-looking. Moving sections between
those two files rearranges a document nobody reads while the real statuses go
untouched. **The presence of `TODO.md` proves nothing. The presence of `items/`
is decisive.**

## The division of labor

- **`TODO.md` owns the status of open work.** It is the single source of truth
  for each open item and its marker. The user hand-edits it. This skill *drains*
  an item out of it into `DONE.md` once step 3 verifies the work actually
  shipped.
- **`DONE.md` is the completed archive.** An item reaches it when it is verified
  done — either this skill's check confirms it shipped, or the user marked it
  done. Move the whole section across, keeping whatever numbering the file uses.
- **`TODO-parallel.md` stays structural.** It must NOT restate per-item status —
  it cites sections by name or number and describes streams, which files each
  one owns, dependency and ordering rules, and the integration mechanism. Its
  one time-varying section is a **thin snapshot** of what is mergeable or
  blocked right now, plus branch state.

The whole point of the skill — the reason it isn't a copy-edit — is: **do not
trust the markers at face value.** Confirm each against the code and git log,
and surface the drift.

## Standing rule on moving items

When *this skill's own verification* (step 3) confirms an open item has actually
shipped in the code and git, **move it to `DONE.md` on your own judgment**: mark
it done and move its whole section out of `TODO.md`, keeping its number. Never
just flip a marker in place. Then refresh `TODO-parallel.md`.

Two guardrails make that safe, and both are mandatory:

1. Move ONLY on **real code and git evidence**, never on a bare marker.
2. **List every move in the step 7 hand-back** so the user can reverse any they
   disagree with.

Genuinely *ambiguous* cases — mixed or partial evidence, or a `DONE.md` claim
that looks incomplete — are **reported, not moved**.

## Run from the repo root (the current working directory)

All paths below are relative to the current working directory. If **`TODO.md` or
`TODO-parallel.md` isn't present**, this skill doesn't apply here: say so
clearly and stop. Don't fabricate a plan, and don't create either file from
scratch unless the user asks.

`DONE.md` is optional. If `TODO.md` exists but `DONE.md` doesn't, ask once
whether to create it before moving anything into it.

## Step 1 — Read the docs

1. Read `TODO.md` in full. Extract the section list, each item's title, its
   status marker — **whatever markers this file actually uses**; derive them,
   don't assume a scheme — and any branch names it mentions. These are the open
   items the plan must cover.
2. Skim `DONE.md`'s headers (`grep -nE '^#+ ' DONE.md`) so you know what has
   already shipped. You should *not* expect that code to be missing, and a
   stream citing only finished items needs no fresh work.
3. Read `TODO-parallel.md` in full. Its **authored structure** — the streams
   table, locked decisions, dependency and ordering rules, the integration
   mechanism, open clarifications, the critical path — is NOT derived from
   `TODO.md` and must be **preserved**, refined only if a decision actually
   changed. Only the progress snapshot is regenerated each run.

## Step 2 — Establish git ground truth

```bash
git -C . log --oneline -40
git -C . branch -a
git -C . status --short
```

Build a map of which branches have **merged to the base branch** versus which
are still live or parked. Merge commits are the evidence, as is any
commit-subject convention this repo uses to name the branch work landed from —
read the real convention out of `git log`, don't assume one.

Note that a branch absent from `git branch -a` may simply have been merged and
deleted, which is normal, not lost work. Local-only feature branches are common;
see the marketplace's `CONVENTIONS.md`.

## Step 3 — Double-check status against code and git (the core)

For every item marked as partially done, **verify the partial code is actually
real.** For not-started and deferred items, confirm no surprise code already
landed them. The most valuable drift to catch is an **open item that has
secretly finished** — once code and git confirm it, move it to `DONE.md` and
list the move in the hand-back — or a **`DONE.md` claim that's actually
incomplete**, which should come back to `TODO.md`. Spot-check the latter only
when a done claim looks suspect.

Fan out **parallel agents** (the Agent tool — `general-purpose` for
doc-versus-code reality checks, `Explore` for breadth) so file dumps stay out of
the main context. Group items by area, one agent per cluster. Give each agent
the repo path, the item text to check, the exact searches to run, and "report
file references, read-only, do NOT edit." Each agent answers, per item:

- Does the implementation actually exist in the source, and how much of it?
- Does the code match what `TODO.md` claims?
- Is there a merged branch or commit backing it?

Cheap cross-checks to do yourself while the agents run:

- A partially-done item whose branch the log shows as merged: consistent.
- An open item whose feature clearly **fully landed**: it's done — move it.
- A `DONE.md` entry with **no implementing code**: drift; bring it back.
- Citations into the source that have drifted off the code.
- Branch names in either doc that no longer exist — remembering that merged and
  deleted is normal.

## Step 4 — Resolve each verified item

Be explicit about every change you make:

- **Verified done** → move it to `DONE.md`, keeping its section number, and
  prune any queue line elsewhere that referenced it.
- **Marker tweak** (still open, just mislabeled) → edit it in place in
  `TODO.md`.
- **Ambiguous or mixed evidence** → do NOT move it. Report it and let the user
  decide, and reflect reality in the progress snapshot meanwhile. Present these
  as a short list, for example:

> Judgment calls (reported, not moved):
> - §5.7 marked partially done — the desktop path is present, the mobile path
>   is absent (no references anywhere in the source); consistent with it being
>   a release blocker, so leaving it open.
> - §2.4 is in `DONE.md` — but no implementing code found for the second
>   platform; should this come back?

Only real code and git evidence justifies a move. A bare marker does not.

## Step 5 — Rewrite the plan

Edit `TODO-parallel.md`:

1. **Preserve** the streams table, decisions, dependency and ordering rules,
   integration mechanism, open clarifications, and critical path. Update them
   only if a decision actually changed — a stream's owned files shifted, a
   decision was locked or reversed. Keep the stream-to-section cross-references
   accurate, remembering that a cited section now lives in `DONE.md` if it
   shipped.
2. **Regenerate the progress snapshot** as `## Progress as of <YYYY-MM-DD>`:
   - Get the date from `date +%Y-%m-%d`. Never a date from earlier in the
     conversation or copied from the old doc.
   - Content is what's **mergeable or blocked right now**, plus per-stream
     branch state (landed, underway, parked), grounded in the git ground truth
     from step 2 and the verification from step 3.
   - **Do NOT restate per-item markers** — those live in `TODO.md` and
     `DONE.md`. Reference sections instead. The snapshot describes integration
     reality, not an item checklist.

## Step 6 — Trim history.md (housekeeping)

Keep `history.md` bounded to a rolling recent window so it doesn't grow without
limit. Older entries are MOVED, never deleted, into `history-archive.md`:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/updatex/trim_history.py"      # 7-day default
```

If `$CLAUDE_PLUGIN_ROOT` isn't set, the trimmer is at
`~/.claude/skills/updatex/trim_history.py`. Run it from the repo root. `/updatex`
runs the same trimmer every time it writes history, so this is usually a no-op —
a cheap backstop. If it reports `history-archive.md` is NEW and untracked, run
`git add history-archive.md` so the next commit includes it. Do **not** commit.

Skip this step entirely if the project has no `history.md`.

## Step 7 — Hand back

Summarize: **every item you moved to `DONE.md`**, with the file reference or
commit that justified each; any markers you fixed in place; any ambiguous items
you reported for the user to rule on; what changed in the plan's structure, if
anything; the new snapshot date; and whether `history.md` was trimmed.

Since moves are on your judgment, this list is the user's chance to reverse one.

Do **not** commit. The user owns that step.

## Don't

- Don't trust a status marker at face value — confirm against code and git every
  run.
- Don't duplicate per-item status into the plan — that reintroduces the drift
  this workflow exists to prevent.
- Don't move an item to `DONE.md` on a bare marker alone, and always list the
  move in the hand-back. Move nothing that's ambiguous.
- Don't read all of `DONE.md`'s archive section or all of `history.md`; sample
  the head or grep for the specific item.
- Don't commit.
