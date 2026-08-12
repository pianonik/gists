---
name: addtodo
description: Add a quick to-do item to the project's TODO.md (the repo-root TODO.md in the current working directory), auto-routed to the most relevant existing section (or a new subsection if nothing fits). The item is whatever the user types after /addtodo. Use when the user says "/addtodo <text>", "addtodo", or asks to drop a new task or idea into TODO.md. ONLY for a repo whose tracker is a hand-edited TODO.md: if the repo has an items/ store (items/*.md with items/scripts/itemlib.py), stop and use /additem instead, even when a TODO.md also exists — a stale hand-authored TODO.md often sits alongside a live item store.
tools: Read, Grep, Bash, Edit
---

# addtodo

Capture the text the user typed after `/addtodo` as a new **open** to-do item and
insert it into `TODO.md` **where it makes sense** — under the existing section
whose topic it matches, or as a new subsection if nothing fits. This is fast
capture: place it, report where it landed, don't make the user choose.

## Step 0 — check for an item store FIRST (mandatory)

Before touching `TODO.md`, before anything else:

```bash
ls items/scripts/itemlib.py 2>/dev/null; ls items/*.md 2>/dev/null | head -3
```

If either produces output, this project's tracker is the **item store**, not
`TODO.md`. **Stop and tell the user to run `/additem` instead.** Do not edit
`TODO.md`.

This check is unconditional and comes first. It is NOT conditional on `TODO.md`
being missing — a repo can have both: a live `items/` store *and* a stale
hand-authored `TODO.md` still sitting at the repo root from before the store
existed, large and entirely plausible-looking. Filing an item into that file
puts it where nobody will look for it. **The presence of `TODO.md` proves
nothing. The presence of `items/` is decisive.**

## Then: find the file

`TODO.md` lives at the repo root, which is the current working directory. If
there is **no `TODO.md` in the cwd**, say so and stop — don't create one
unprompted.

## Steps

### 1. Get the item text

The item is everything the user typed after `/addtodo`. If it's empty, ask what
to add and stop — don't guess.

### 2. Learn the file's actual structure

Never assume a section scheme. Derive the live one:

```bash
grep -nE '^#+ ' TODO.md
```

Then read enough of `TODO.md` around the one or two candidate sections to place
the item sensibly and to avoid duplicating something already there.

While you're reading, note two things about the file's own conventions, because
you must match them rather than impose your own:

- **The status marker it uses for not-started work** — a checkbox, an emoji, a
  bare bullet. A fresh item is not-started; give it whatever this file uses for
  that. Never give it a marker that means "in progress", "done", or "awaiting
  review".
- **Whether some section is a review queue rather than an inbox.** A section
  named something like "pending confirmation" holds work that is finished and
  waiting on the user. New ideas do not go there.

### 3. Pick the destination

- Match the item's topic to the **most relevant existing section**, using the
  headers you just derived.
- If it extends a specific subsection, **append it there as a bullet**.
- If it's a distinct new topic with no good home, **add a new subsection** under
  the closest top-level section, matching the file's own numbering or naming
  scheme.
- If two sections fit equally and it actually matters which, ask briefly.
  Otherwise pick the closest and say which one in the report.

### 4. Insert it, disturbing nothing else

- Append at the **end of the chosen subsection** — insert immediately before the
  next header, anchoring on that header so surrounding content is untouched.
- Match the file's bullet style and wrap long lines to roughly the surrounding
  width.
- Stamp its origin so it's traceable. Get the date from `date +%Y-%m-%d`, then
  write it the way the file already stamps things, e.g.
  `- **(added <date>)** <the item>`.
- Lightly clean the user's phrasing — fix obvious typos, make it a readable
  sentence — but keep their meaning. Do **not** invent scope, acceptance
  criteria, or an approach they didn't ask for. If the raw note is cryptic,
  preserve it close to verbatim rather than over-interpreting.

### 5. Report back

Tell the user exactly where it landed (section name) and show the lines you
added. Offer to move it if the placement isn't right.

**Do not commit.** Touch only `TODO.md` — not `DONE.md`, not `TODO-parallel.md`,
and not `history.md` or `README.md` (recording those is `/updatex`'s job).

## Don't

- Don't put a new item in a review/confirmation queue section — that's for
  finished work awaiting sign-off, not an inbox.
- Don't mark a new item as in-progress or done — it's not-started.
- Don't move, re-status, or restructure other items; add only the one.
- Don't commit, and don't update `history.md` or `README.md`.
