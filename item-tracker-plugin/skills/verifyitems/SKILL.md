---
name: verifyitems
description: Audit every item in the items/ store against the real code and git history rather than trusting its status field, then flip the ones that have verifiably shipped to done, flip back any done item that turns out to be incomplete, and report anything ambiguous for the user to rule on. Every flip is listed at the end so it can be reversed. Use when the user says "verifyitems", "/verifyitems", or asks to check whether the tracker's statuses are actually true. Requires an items/ store (items/*.md with items/scripts/itemlib.py); if the project has a flat hand-edited TODO.md instead, use /verifytodo.
tools: Read, Bash, Grep, Glob, Edit, Write, Agent
---

# verifyitems

Go through the item store and find out which statuses are **lies**.

A tracker drifts in both directions. Work finishes and nobody flips the item, so
the open list is padded with things already done. Or an item is marked done on
the strength of a commit that only did half of it, and the remainder is now
invisible. Both are worse than an empty tracker, because both are confidently
wrong.

This skill does not trust the `status:` field. It checks each one against the
code and the git history, flips the ones it can prove, and hands back a list of
every flip so you can reverse any you disagree with.

The item-store sibling of `/verifytodo`.

## What this is not

It does not record the current conversation — that's `/updateitems`. It does not
produce a broad audit of dead code and doc drift — that's
`/planning-items-review`, which reports drift but deliberately never writes.
This skill is the narrow one that **corrects the store**.

## Run from the repo root (the current working directory)

Expects `items/*.md` with `items/scripts/` (`itemlib.py`, `export_todo.py`). If
there is **no `items/` store**, say so and stop; suggest `/verifytodo` for a
flat `TODO.md` project. Do not invent a store.

## Step 1 — Load the store

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "items/scripts"); import itemlib as il
for f in il.load_items():
    print(f["status"], f.get("priority"), f["section"], "::", f["id"], "::", f["title"])
PY
```

Extract per item: `id`, `title`, `section`, `status`, `priority`, and any branch
names or file references its body mentions. Those references are what the
verification will chase.

If the user named a section or an area, scope the run to it and say so. A full
store of several hundred items is a large sweep; scoping is normal.

## Step 2 — Establish git ground truth

```bash
git -C . log --oneline -40
git -C . branch -a
git -C . status --short
```

Note which branches have merged and which are still live. Merge commits are the
evidence, as is whatever commit-subject convention this repo uses to name the
branch work came from — read the real convention out of `git log`, don't assume
one. A branch absent from `git branch -a` may mean merged-and-deleted, which is
normal, not lost work.

## Step 3 — Check each status against the code (the core)

- For every `in-progress` item, **verify the partial code is real.** An item can
  sit at `in-progress` for months because someone wrote a plan and nothing else.
- For `backlog` and `needs-spec` items, confirm no surprise code already landed
  them. This is the most valuable drift to catch: an open item that has secretly
  finished.
- For `pending-review` items, confirm the work is actually complete, since the
  user is being asked to sign off on it.
- For `done` items, spot-check only the ones whose claim looks suspect — a done
  item whose feature you cannot find at all, or which the item body says covers
  two platforms when the commit touched one.

Fan out **parallel agents** (the Agent tool — `general-purpose` for
doc-versus-code reality checks, `Explore` for breadth) so file dumps stay out of
the main context. Group items by section, one agent per cluster. Give each agent
the repo path, the item text plus the exact searches to run, and "report file
references, read-only, do NOT edit." Each agent reports, per item: shipped,
partial, or not started, with the evidence.

## Step 4 — Flip the certain, report the ambiguous

- **Certain shipped** — real code and git evidence, not a bare marker → set
  `status: done`, stamp `updated:` to today (`date +%Y-%m-%d`). Preserve
  everything else: priority, created, section, body. Never delete the file.
- **Certain incomplete** — a `done` item with no implementing code, or with an
  obvious half missing → flip back to `in-progress` or `pending-review` and
  stamp `updated:`.
- **Finished but unsigned-off** — if the work is complete and the user has not
  confirmed it, `pending-review` is the honest status, not `done`.
- **Ambiguous** — mixed or partial evidence → **do NOT flip.** Report it and let
  the user decide.

Edit the item files directly, or go through `itemlib.write_item` — either is
fine, since you are changing existing files rather than creating new ones.

## Step 5 — Regenerate the exports and hand back

```bash
python3 items/scripts/export_todo.py
```

Then the **hand-back, which is mandatory**: list every flip you made — item id,
old status, new status, and the one-line evidence that justified it — plus the
ambiguous ones you left alone.

This list is the guardrail. Flipping statuses on your own judgment is only
acceptable because every flip is visible and reversible in one place. A run that
silently changed thirty statuses would be worse than no run at all.

## When to stop

After the flips and the regenerated exports, stop. **Do not commit** — the user
owns that step.

## Don't

- Don't trust the `status:` field. That's the entire point of the skill.
- Don't flip on a bare marker, a commit subject, or an item body's own claim.
  Code and git, or it doesn't count.
- Don't mark something `done` when the user hasn't signed off — that's
  `pending-review`.
- Don't delete an item to mark it finished.
- Don't hand-edit `TODO.md` / `DONE.md` or anything under `items/exports/` —
  regenerate them.
- Don't run any importer that rebuilds the store FROM a TODO file; it would
  clobber live item edits with stale data.
- Don't omit the hand-back, and don't force a flip you can't evidence.
- Don't `git add` or commit.
