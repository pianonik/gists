---
name: planning-items-review
description: Review the whole state of an ITEM-STORE project — items/*.md (each file's status field IS its open/done state), history.md, README.md, docs/*, and the source — to surface inconsistencies, suspicious or dead code, stale item statuses, and the true state of in-flight work versus its planning docs. The item-store counterpart of /planning-review. Use when the user says "planning-items-review", "/planning-items-review", or asks to review or audit the state of everything in a repo whose source of truth is items/*.md. If the project has a flat hand-edited TODO.md and no items/ store, use /planning-review instead.
tools: Read, Bash, Grep, Glob, Agent, Write
---

# planning-items-review

A read-by-default project audit for an **item-store** project. The goal is to
tell the user where things actually stand — separating what's *built and
verified* from what's *only planned*, finding the drift between the store, the
docs and the code, and flagging stale statuses and dead code — so they can
decide what to work on next. This is a review, not a build: do not change
behavior or commit anything unless the user explicitly asks.

The item-store sibling of `/planning-review`: same job, different substrate.
Here `TODO.md` and `DONE.md` are *generated* exports — never a source, never
hand-edited.

## First: confirm this project uses the item store

The store is `items/*.md` at the repo root, each file front matter plus a body
whose first paragraph is the one-line summary. Helper scripts live in
`items/scripts/` (`itemlib.py`, `export_todo.py`). If there is **no `items/`
store**, STOP and tell the user to run `/planning-review` instead. Do not invent
one.

## When to use

- "Review the current state of this project."
- "Look for inconsistencies, dead code, stale items, report back."
- Before picking a project back up after time away, when a `/whereitems`-style
  summary isn't deep enough — the user wants the *gaps* found.

## Orientation (do this first, in parallel)

1. `README.md` — architecture and conventions. Read in full if reasonable.
2. The **item store** — do NOT read every `items/*.md` by hand, and do NOT run
   `export_todo.py`, which *writes* the generated views. Load it read-only:

   ```bash
   python3 - <<'PY'
   import sys, collections
   sys.path.insert(0, "items/scripts")
   import itemlib as il                     # fails loud on a malformed item — useful signal
   items = il.load_items()
   print("STORE:", len(items), "items —", dict(collections.Counter(f["status"] for f in items)))
   rank = {s: i for i, s in enumerate(
       ["pending-review", "in-progress", "needs-spec", "backlog", "done"])}
   open_items = [f for f in items if f["status"] != "done"]
   open_items.sort(key=lambda f: (f.get("section", ""), rank.get(f["status"], 9), f.get("priority", 3)))
   sec = None
   for f in open_items:
       if f.get("section") != sec:
           sec = f.get("section"); print(f"\n[{sec}]")
       print(f"  {f['status']:14} P{f.get('priority', 3)}  [{f['id']}]  {f['title']}")
   PY
   ```

3. `history.md` — newest at top. Often huge — do NOT read it all; sample the head.
4. `ls docs/` and any focus docs the user named, including `TODO-parallel.md`.
5. `git log --oneline -20`, `git status`, `git branch -a`. Feature branches are
   often local-only and short-lived, so absent from `git branch -a` may mean
   merged-and-deleted, not lost.

Prefer parallel Read and Bash calls — these are independent.

## Fan out the investigation (the core of the skill)

The value is in **comparing the store and the planning docs against the actual
source**. Spawn **parallel agents** (the Agent tool — `general-purpose` for
doc-versus-code analysis, `Explore` for breadth searches), one per major area or
section. This keeps file dumps out of the main context; you keep the
conclusions.

Typical agents to launch concurrently, adapted to the project:

- **Per item cluster: a "status versus code" reality check.** Group items by
  section, one agent per cluster. For each `in-progress` item: *does the partial
  implementation actually exist, how much, and does the code match what the item
  body claims?* For `backlog` and `needs-spec` items: has surprise code already
  landed them? The most valuable drift is an **open item that has secretly
  finished** or a **`done` item that's actually incomplete** — spot-check done
  claims only when they look suspect. The most important output is the honest
  status: "planning prose plus dead bindings, zero implementation" versus
  "engine landed, calibration unbuilt".
- **Docs versus code** for any big feature the docs describe. Watch for
  **manuals and specs written in shipping-product voice for features that don't
  exist yet**.
- **Dead-code and suspicious-code sweep** (`Explore`): orphaned files not
  referenced in any build list and not imported anywhere — careful with
  glob-based builds, where "not in the build file" doesn't mean dead, so verify
  imports too; leftover carryover from a previous generation of the project;
  debug probes and breadcrumbs left in; stale `FIXME` / `HACK` / `TODO` comments
  that contradict the live code; commented-out blocks of abandoned work. Group
  by confidence: high, medium, low.
- **Plan-readiness check** for any plan the user may start soon: is the smallest
  first step well-scoped and grounded in the *current* code? What's genuinely
  blocking versus deferred?

Give each agent the repo path, the item text plus specific docs to read, the
exact searches to run, and "report file references, read-only, do NOT edit."
Launch them in a single message so they run in parallel.

## Cross-check the cheap inconsistencies yourself

While the agents run:

- **Stale generated exports.** Are `TODO.md` / `DONE.md` older than the newest
  `items/*.md`? `ls -lt items/*.md TODO.md DONE.md` settles it. Stale exports
  mean someone edited the store without regenerating — flag it; the fix is
  `/updateitems`' export step, not a hand edit here.
- **Stale status claims.** If `git status` is clean but an item body or
  `history.md` says "uncommitted", that's stale — the work shipped. Spot-check
  one: is the named file actually tracked?
- **`pending-review` pile-up.** Items done but awaiting the user's sign-off. A
  big pile means the real blocker is review, not work. Call those out
  separately.
- **Dangling references** in item bodies and config files — to scripts,
  branches, or paths that no longer exist.
- **Doc citations into the source** that have drifted off the code.

## Report back

One scannable report. The user may be reading it later, tired.

1. **Overall snapshot** — branch, clean or dirty, what just landed, store counts
   by status.
2. **The user's stated focus area** — its real state and what's next.
3. **Each big piece of work** — built-and-verified versus planned-only, with
   file references.
4. **Status drift** — open items that look secretly finished, done items that
   look incomplete, `pending-review` awaiting sign-off. Report the drift; do NOT
   flip any `status:` field — that's `/updateitemplan`'s job. Suggest it if the
   drift is broad.
5. **Inconsistencies and doc drift**, including stale exports.
6. **Suspicious or dead code**, grouped by confidence.
7. **Genuinely open items** — the real work list from the store, by section.
8. **Suggested next moves**, including what can proceed independently without
   colliding.

Use `file:line` references throughout — they're clickable. Quote the agents'
concrete findings, not their process.

## Optional: persist the report, and a safe pass

- If asked, save the report to `docs/<YYYY-MM-DD>-review.md`, taking the date
  from `date +%Y-%m-%d`.
- If the user says "make a pass at what's safe": do ONLY behavior-neutral,
  build-neutral, unambiguous fixes. Leave anything needing the user's judgment —
  design-doc prose, shipped data, item `status:` flips, item-body restructuring,
  deletions — flagged but untouched. Note exactly what you changed and what you
  deliberately left. Do not commit.

## Don't

- Don't edit source, docs or items as part of the review — it's read-only until
  the user opts into a pass.
- Don't flip any item's `status:` — report drift; `/updateitemplan` owns flips.
- Don't run `export_todo.py` or hand-edit `TODO.md` / `DONE.md` — they're
  generated views, and this skill is read-only.
- Don't trust a `status:` field or a doc's "verified" claim at face value.
- Don't read all of `history.md`; sample the head.
- Don't commit anything.
- Don't invent an item store if there isn't one — send the user to
  `/planning-review`.
