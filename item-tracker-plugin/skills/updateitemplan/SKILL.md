---
name: updateitemplan
description: Re-derive TODO-parallel.md (the structural plan — independent streams, worktrees, branches, ordering, integration) from the ITEM STORE (items/*.md), double-checking every item's status field against the real code and git log rather than the marker, and flipping verified-shipped items to status done in their own file. The item-store counterpart of /updateplan. Use when the user says "updateitemplan", "/updateitemplan", or asks to refresh the parallel plan from the items/ store. If the project has a flat hand-edited TODO.md and no items/ store, use /updateplan instead.
tools: Read, Bash, Grep, Glob, Edit, Write, Agent
---

# updateitemplan

Regenerate `TODO-parallel.md` (the **how** — independent streams, worktrees,
branches, ordering, integration mechanism) from the **item store** (`items/*.md`
— the **what**, one file per item, its `status:` field owning open versus done),
**after independently verifying each item's status against the real code and git
history.**

The item-store sibling of `/updateplan`. Two things differ, because the store
unifies open and done into one `status:` field:

- It reads the **item store**, not `TODO.md`. `TODO.md` and `DONE.md` are
  *generated* views — never a source, never hand-edited here.
- "Move a verified-shipped item to DONE" becomes **flip `status: done` and stamp
  `updated:` in that item's own file.** No shuffling sections between files.

## Run from the repo root (the current working directory)

Expects `items/*.md` with `items/scripts/` (`itemlib.py`, `export_todo.py`),
plus a `TODO-parallel.md` structural plan. If there is **no `items/` store**,
this skill doesn't apply — say so and stop, and suggest `/updateplan`. If the
store exists but `TODO-parallel.md` doesn't, ask once whether to create it
rather than assuming.

The point of the skill, and why it isn't a copy-edit: **do not trust the
`status:` field at face value.** Confirm each against the code and git log, flip
the ones that have truly shipped, and surface any drift.

## Step 1 — Read the store and the plan

1. Load every item read-only through itemlib:
   ```bash
   python3 - <<'PY'
   import sys; sys.path.insert(0, "items/scripts"); import itemlib as il
   for f in il.load_items():
       print(f["status"], f.get("priority"), f["section"], "::", f["title"])
   PY
   ```
   Extract, per item: `id`, `title`, `section`, `status`, `priority`, and any
   branch or worktree names its body mentions. The **open** items (status not
   `done`) are what the plan must cover. The **done** items have shipped — don't
   expect their code to be missing, and a stream citing only done items needs no
   fresh work.
2. Read `TODO-parallel.md` in full. Its **authored structure** — the streams
   table, locked decisions, dependency and ordering rules, the integration
   mechanism, open clarifications, the critical path — is NOT derived from the
   store and must be **preserved**, refined only if a decision actually changed.
   Only the progress snapshot is regenerated each run.

## Step 2 — Establish git ground truth

```bash
git -C . log --oneline -40
git -C . branch -a
git -C . status --short
```

Map which stream branches have **merged to the base branch** versus which are
still live or parked. Merge commits are the evidence, as is whatever
commit-subject convention this repo uses to name the branch work came from —
read the real convention out of `git log`, don't assume one. Note the most
recent landings.

Feature branches are often local-only and short-lived, so a branch absent from
`git branch -a` may mean merged-and-deleted, not lost.

## Step 3 — Double-check each status against code and git (the core)

For every item marked `in-progress`, **verify the partial code is real.** For
`backlog`, `needs-spec` and deferred items, confirm no surprise code already
landed them.

The most valuable drift to catch is an **open item that has secretly finished**
— once code and git confirm it, flip `status: done` in its file and list the
flip in the hand-back — or a **`done` item that's actually incomplete**, which
flips back to `in-progress` or `pending-review`. Spot-check the latter only when
a done claim looks suspect.

Fan out **parallel agents** (the Agent tool — `general-purpose` for
doc-versus-code reality checks, `Explore` for breadth) so file dumps stay out of
the main context. Group items by section or area, one agent per cluster. Give
each agent the repo path, the item text plus the exact searches to run, and
"report file references, read-only, do NOT edit." Each agent reports, per item:
shipped, partial, or not started, with evidence.

## Step 4 — Report the ambiguous, flip the certain

- **Certain shipped** — real code and git evidence, not a bare marker → edit the
  item file: set `status: done`, stamp `updated:` today. Preserve everything
  else (priority, created, section, body). Do NOT delete the file.
- **Certain regressed or incomplete-done** → flip `status:` back, usually to
  `in-progress` or `pending-review`, and stamp `updated:`.
- **Genuinely ambiguous** — mixed or partial evidence → do NOT force a flip.
  **Report** it in the hand-back for the user to decide.

## Step 5 — Regenerate TODO-parallel.md

Rewrite only the time-varying **`## Progress as of <date>`** snapshot: which
streams are mergeable or blocked right now, branch and worktree state, and the
next integration step. Keep it **structural** — cite items by title, do NOT
restate per-item statuses, since the store owns those. Leave the authored
sections intact unless a decision actually changed. Take the snapshot date from
`date +%Y-%m-%d`.

## Step 6 — Regenerate exports and hand back

1. `python3 items/scripts/export_todo.py`, so the generated views reflect the
   status flips you just made.
2. **Hand-back**: list every `status:` flip you made — item, old status, new
   status, and the one-line evidence — so the user can reverse any they disagree
   with, plus the ambiguous items you left for them. This list is mandatory.
   It's the guardrail that makes auto-flipping safe.

## When to stop

After the flips, the refreshed `TODO-parallel.md`, and the regenerated exports,
stop. **Do not commit** — the user runs their commit step separately.

## Don't

- Don't trust the `status:` field — verify against code and git; flip only on
  real evidence.
- Don't hand-edit `TODO.md` / `DONE.md` — regenerate them.
- Don't delete an item to mark it done — set `status: done`.
- Don't restate per-item status inside `TODO-parallel.md` — it stays structural.
- Don't run any reverse importer that rebuilds the store FROM `TODO.md`; it
  would clobber the live item edits.
- Don't `git add` or commit, don't fabricate evidence, and force-flip nothing
  that's ambiguous.
