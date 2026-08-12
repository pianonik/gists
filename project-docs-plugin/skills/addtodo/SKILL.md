---
name: addtodo
description: Add a quick to-do item to the project's TODO.md (the repo-root TODO.md in the current working directory), auto-routed to the most relevant existing section (or a new subsection if nothing fits). The item is whatever the user types after /addtodo. Use when the user says "/addtodo <text>", "addtodo", or asks to drop a new task or idea into TODO.md.
tools: Read, Grep, Bash, Edit
---

# addtodo

Capture the text the user typed after `/addtodo` as a new **open** to-do item and
insert it into `TODO.md` **where it makes sense** — under the existing section
whose topic it matches, or as a new subsection if nothing fits. This is fast
capture: place it, report where it landed, don't make the user choose.

## First: find the file

`TODO.md` lives at the repo root, which is the current working directory. If
there is **no `TODO.md` in the cwd**, say so and stop — don't create one
unprompted. If the project instead tracks work as one markdown file per item
under `items/`, point the user at `/additem`.

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
