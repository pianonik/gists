---
name: updateitems
description: Reflect the current conversation's work into the ITEM STORE (items/*.md, one markdown file per item) instead of a hand-edited TODO.md — flip status, stamp dates, refine bodies, create new item files — then history.md and README.md, then regenerate the generated views. The item-store counterpart of /updatex. Use when the user says "updateitems", "/updateitems", or asks to record the session into the items/ store. If the project has a flat hand-edited TODO.md and no items/ store, use /updatex instead.
tools: Read, Edit, Write, Bash, Grep, Glob
---

# updateitems

Record the work done in the current conversation into the **item store** — the
`items/*.md` one-file-per-item tracker where each file's `status:` field is its
open/done state and the store is the source of truth. `TODO.md` and `DONE.md`
are *generated* views, never hand-edited.

The item-store sibling of `/updatex`: same job, different substrate.

## First: confirm this project uses the item store

The store is `items/*.md` at the repo root, each file front matter plus a body
whose first paragraph is the one-line summary. Helper scripts live in
`items/scripts/` (`itemlib.py`, `export_todo.py`). If there is **no `items/`
store**, STOP and tell the user to run `/updatex` instead. Do not invent one.

## What to update, in this order

1. **`items/*.md`** — the tracker itself:
   - **Items finished or advanced this session** → update `status:` and stamp
     `updated:` to today. Refine the summary paragraph and body if the work
     changed what the item means or left a smaller remainder.
   - **New work, ideas, or follow-ups surfaced** → create one new
     `items/<slug>.md` per item.
   - Never DELETE an item to mark it done — set `status: done`. The store keeps
     done items and the export splits open from done by status. Only remove a
     file if the item was genuinely bogus or a duplicate AND the user asks.
2. **`history.md`** — prepend one or more dated entries at the TOP.
3. **`README.md`** — only if substantive architecture, concepts or workflows
   changed. Most sessions don't need it.
4. **Regenerate the exports** — `python3 items/scripts/export_todo.py`, so the
   generated views reflect the store.

If `history.md` or `README.md` is missing, note it and continue. Don't create
them unless asked.

## Gather facts BEFORE writing

Don't write from memory alone — context may have been compacted.

- **`date +%Y-%m-%d`** — today. Sessions cross midnight; never trust an earlier
  in-context date.
- **`git log --oneline -20`** and **`git diff HEAD~N`** — what actually changed
  and why. Quote short hashes in `history.md`.
- Read `items/scripts/export_todo.py` if you need to confirm where this repo's
  exports land.

## The item file format

```markdown
---
id: <slug>                 # kebab-case of the title; the filename is <id>.md
title: <Title>             # quote if it contains ':' or '#'
section: <Section>         # e.g. "Audio Chain"; "Uncategorized" if none fits
status: in-progress        # backlog | needs-spec | in-progress | pending-review | done
priority: 3                # 1 = highest .. 5 = lowest; user-owned
needs_spec: false
created: YYYY-MM-DD
updated: YYYY-MM-DD
tests:
  - test_foo.py            # bare list; empty is just "tests:"
---

<p><one-sentence, plain-English summary — the subtitle></p>

<full detail, prose; carry over specifics — file references, decisions, remainder>
```

Rules:

- **Slug** = lowercase, every run of non-alphanumerics becomes one `-`, trimmed,
  capped at 48 characters on a `-` boundary. That's `itemlib.slugify()`. For a
  NEW file, create it *through* itemlib so the slug and quoting match byte for
  byte:
  ```bash
  python3 - <<'PY'
  import sys; sys.path.insert(0, "items/scripts"); import itemlib as il
  fm = {"id": il.slugify("My New Item"), "title": "My New Item",
        "section": "Uncategorized", "status": "backlog", "priority": 3,
        "needs_spec": False, "created": "<today>", "updated": "<today>",
        "tests": []}
  print(il.write_item(il.ITEMS_DIR, fm, "<p>One-liner.</p>\n\n<p>Detail.</p>"))
  PY
  ```
  Stamp real dates from `date +%Y-%m-%d`.
- **Status vocabulary**: `backlog`, `needs-spec`, `in-progress`,
  `pending-review`, `done`. When the work finishes an item but the user still
  has to sign off, use **`pending-review`, not `done`**.
- **Stamp `updated:` to today on ANY edit** — status, body or priority.
- **Preserve user-owned metadata** — `priority`, `created`, `section` — across
  edits. Change one only if the work explicitly changed it. `created` never
  moves once set.
- **Net-new items** get `created` and `updated` = today, and `priority: 3`
  unless the user set one.
- Front matter is a controlled YAML subset (`key: value` scalars plus `- item`
  lists). Editing an existing file's front matter by hand is fine, but **fail
  loud** rather than silently reshaping a file whose front matter is malformed —
  that's the itemlib contract.

## history.md

Same conventions as `/updatex`:

- **Newest entries at the TOP.**
- Heading `## YYYY-MM-DD (qualifier) — short summary`. Read the current top entry
  and match its style.
- Technical, narrative, mid-length. Cite file paths and commit short hashes. The
  entry is the *narrative around* the commits, not a copy of the commit
  messages.
- After prepending, trim to a rolling window. Older entries MOVE, never delete,
  into `history-archive.md`:
  ```bash
  python3 "$CLAUDE_PLUGIN_ROOT/../project-docs-plugin/skills/updatex/trim_history.py"
  ```
  That path assumes both plugins are installed. If only this one is, the trimmer
  is at `~/.claude/skills/updatex/trim_history.py`; if neither resolves, skip
  the trim and say so rather than inventing a trimmer. If it reports
  `history-archive.md` is NEW and untracked, run `git add history-archive.md` so
  the next commit includes it — but do not commit.

## README.md

Skip unless the session introduced something the README's structure misses: a
new subsystem, build target, convention, external dependency, format invariant,
or architectural shift. A bug fix or a tuning does NOT warrant a README touch.
When you do touch it, extend the most relevant existing section.

## When to stop

After the store, `history.md`, `README.md` and the regenerated exports, stop.
**Do not commit** — the user runs their commit step separately. Report in one or
two sentences: how many items touched and created, which docs, that exports were
regenerated. Say so if you skipped the README.

## Don't

- Don't hand-edit `TODO.md` / `DONE.md` — regenerate them from the store.
- Don't delete an item to "complete" it — set `status: done`.
- Don't run any reverse importer that rebuilds the store FROM `TODO.md` — it
  would clobber live item edits.
- Don't fabricate — verify against `git log` / `git diff`.
- Don't reorder existing `history.md` entries; only prepend. Don't gut existing
  item bodies while editing — refine them.
- Don't `git add` or commit. Sole exception: a newly created
  `history-archive.md`, which `git commit -a` would otherwise skip.
