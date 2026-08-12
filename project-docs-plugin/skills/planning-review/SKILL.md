---
name: planning-review
description: Review the whole state of a project — TODO.md, history.md, README.md, docs/*, and the source — to surface inconsistencies, suspicious or dead code, stale TODO items, and the true state of in-flight work versus its planning docs. Use when the user says "planning-review", "/planning-review", or asks to review the state of everything, audit the project, or check what is stale or dead before deciding what to work on next. ONLY for a repo whose tracker is a hand-edited TODO.md: if the repo has an items/ store (items/*.md with items/scripts/itemlib.py), stop and use /planning-items-review instead, even when a TODO.md also exists — a stale hand-authored TODO.md often sits alongside a live item store.
tools: Read, Bash, Grep, Glob, Agent, Write
---

# planning-review

A read-by-default project audit. The goal is to tell the user where things
actually stand — separating what's *built and verified* from what's *only
planned*, finding the drift between docs and code, and flagging stale TODO items
and dead code — so they can decide what to work on next. This is a review, not a
build: do not change behavior or commit anything unless the user explicitly asks.

## Step 0 — check for an item store FIRST (mandatory)

Before reading `TODO.md`, before anything else:

```bash
ls items/scripts/itemlib.py 2>/dev/null; ls items/*.md 2>/dev/null | head -3
```

If either produces output, this project's tracker is the **item store**, not
`TODO.md`. **Stop and tell the user to run `/planning-items-review` instead.**

This check is unconditional and comes first. It is NOT conditional on `TODO.md`
being missing — a repo can have both: a live `items/` store *and* a stale
hand-authored `TODO.md` still sitting at the repo root from before the store
existed, large and entirely plausible-looking. An audit built on that file
reports a work list that is months out of date, in the confident voice of a
fresh review — the most damaging thing this skill can produce. **The presence of
`TODO.md` proves nothing. The presence of `items/` is decisive.**

## When to use

- "Review the current state of this project."
- "Look for inconsistencies, dead code, irrelevant TODO items, report back."
- Before picking a project back up after time away, when a `/wherex`-style
  summary isn't deep enough — the user wants the *gaps* found, not just the
  headline state.

## Orientation (do this first, in parallel)

Read the canonical context files from the cwd — the same ones `/wherex` reads,
but go deeper:

1. `README.md` — architecture and conventions. Read in full if reasonable.
2. `TODO.md` — current work items. Note its size; it may have become a
   changelog.
3. `history.md` — newest entries at top. Often huge — do NOT read it all; sample
   the head.
4. `ls docs/` and any focus docs the user named (a plan doc, a manual).
5. `git log --oneline -20`, `git status`, `git branch -a`.

Prefer parallel Read and Bash calls — these are independent.

## Fan out the investigation (the core of the skill)

The value is in **comparing planning docs against the actual source**. Spawn
**parallel agents** (the Agent tool — `general-purpose` for doc-versus-code
analysis, `Explore` for breadth searches), one per major area the orientation
surfaced. This keeps file dumps out of the main context; you keep the
conclusions.

Typical agents to launch concurrently, adapted to the project:

- **Per in-flight feature: a "docs versus code" reality check.** For each big
  piece of work the docs describe, have an agent answer: *does the
  implementation actually exist, how much of it, and does the code match what
  the doc claims?* The most important output is the honest status — "planning
  docs plus dead bindings, zero implementation" versus "engine landed,
  calibration unbuilt". Watch especially for **manuals and specs written in
  shipping-product voice for features that don't exist yet**.
- **Dead-code and suspicious-code sweep** (`Explore`): orphaned files not
  referenced in any build list and not imported anywhere — be careful with
  glob-based builds, where "not listed in the build file" does not mean dead, so
  verify imports too; leftover carryover from a previous generation of the
  project; debug probes and breadcrumbs left in; stale `FIXME` / `HACK` / `TODO`
  comments that contradict the live code; commented-out blocks of abandoned
  work. Group findings by confidence: high, medium, low.
- **Plan-readiness check** for any plan the user may start soon: is the smallest
  first step well-scoped and grounded in the *current* code? What is genuinely
  blocking versus deferred to later phases?

Give each agent the repo path, the specific docs to read, the exact searches to
run, and "report file references, read-only, do NOT edit." Launch them in a
single message so they run in parallel.

## Cross-check the cheap inconsistencies yourself

While the agents run, verify the things a grep settles fast:

- **Stale status markers.** If `git status` is clean but the docs say
  "UNCOMMITTED" or "commit this batch", those are stale — the work shipped.
  Spot-check one: is the named file actually tracked?
- **TODO as changelog.** Count finished items versus genuinely open ones. A TODO
  dominated by done items is hiding the real work list.
- **Dangling references** in data and config files — references to scripts or
  paths that no longer exist.
- **Doc citations into the source** that have drifted off the code they cite.

## Report back

Synthesize one scannable report. The user may be reading it later, tired.
Structure it roughly:

1. **Overall snapshot** — branch, clean or dirty, what just landed.
2. **The user's stated focus area** — its real state and what's next.
3. **Each big piece of work** — built-and-verified versus planned-only, with
   file references.
4. **Inconsistencies and doc drift.**
5. **Suspicious or dead code**, grouped by confidence.
6. **Genuinely open items** currently buried in the TODO.
7. **Suggested next moves** — including what can proceed independently without
   colliding.

Use `file:line` references throughout — they're clickable. Quote the agents'
concrete findings, not their process.

## Optional: persist the report, and a safe pass

- If asked, save the report to `docs/<YYYY-MM-DD>-review.md`, taking the date
  from `date +%Y-%m-%d` and never from earlier in the conversation.
- If the user says "make a pass at what's safe": do ONLY behavior-neutral,
  build-neutral, unambiguous fixes — for example deleting a provably stale
  comment that misleads. Leave anything needing the user's judgment — design-doc
  prose, shipped data, TODO restructuring, deletions — flagged but untouched.
  Note exactly what you changed and what you deliberately left. Do not commit;
  the user owns that step.

## Don't

- Don't edit source or docs as part of the review itself — it's read-only until
  the user opts into a pass.
- Don't trust a doc's "verified" or "landed" claim at face value — confirm
  against the code.
- Don't read all of `history.md`; sample the head.
- Don't commit anything.
