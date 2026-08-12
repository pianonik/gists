---
name: additem
description: Add a NEW item to the project's items/ store (items/*.md, one markdown file per item). The text after /additem is a plain-English description of what the item is; the skill derives a title and slug, routes it to a section, asks for a priority if the description doesn't state one, writes the file through itemlib, and regenerates the generated views. Use when the user says "/additem <text>", "additem", or asks to add a new item to the items store. If the project has a flat hand-edited TODO.md and no items/ store, use /addtodo instead.
tools: Read, Grep, Glob, Bash, Edit, Write, AskUserQuestion
---

# additem

Capture the text the user typed after `/additem` as a **new item file** in the
`items/` store — the one-file-per-item tracker where each file's `status:` field
is its open/done state and `TODO.md` / `DONE.md` are *generated* views. This is
fast capture: create the item, route it to a sensible section, report where it
landed. The only thing you stop to ask about is **priority** (step 3).

## First: confirm this project uses the item store

The store is `items/*.md` at the repo root, with helper scripts in
`items/scripts/` (`itemlib.py`, `export_todo.py`). If there is **no `items/`
store**, say so and stop — don't create one. If the project instead has a flat
hand-edited `TODO.md`, point the user at `/addtodo`.

## Steps

### 1. Get the description

Everything the user typed after `/additem`. If it's empty, ask what the item is
and stop — don't guess.

### 2. Check for a duplicate

Grep the store for the description's key words (`grep -il '<keyword>' items/*.md`)
and skim the hits' summary paragraphs. If an existing item clearly already
covers it, don't create a twin — report the existing item's id and summary, and
ask whether to extend that item's body instead. A merely *related* item is fine;
mention it in the new body as a `[[slug]]` cross-reference if useful.

### 3. Priority — use the stated one, otherwise ASK

- If the description states a priority — a number ("priority 2", "P1") or clear
  words ("urgent" or "top priority" → 1, "high" → 2, "low" → 4, "someday" or
  "nice to have" → 5) — use it and don't ask.
- **Otherwise ask with AskUserQuestion** (single-select, header "Priority"):
  `1 — highest, drop everything`, `2 — high`, `3 — normal`, `4 — low`. "Other"
  covers 5 and someday.

Do not silently default. The priority field is user-owned, so a fresh item gets
the number the user picked, not a guess.

### 4. Derive title, section, and slug

- **Title**: condense the description to a short imperative title, roughly 60
  characters or less. Keep the user's nouns; don't invent scope.
- **Section**: derive the live section names from the store — do NOT hard-code
  them; they differ per project and drift over time:
  ```bash
  grep -h '^section:' items/*.md | sort | uniq -c | sort -rn
  ```
  Route to the best-matching existing section, or `Uncategorized` if nothing
  fits. Don't coin a new section name for a single item. If two sections fit
  equally and it matters, pick the closer one and say so in the report.
- **Slug**: comes from `itemlib.slugify(title)` in step 5. Never hand-roll it.

### 5. Create the item through itemlib

Write the file *through* itemlib so the slug, quoting and front-matter layout
match the rest of the store byte for byte. Get today from `date +%Y-%m-%d` first
— never trust a date from earlier in the conversation — then:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "items/scripts"); import itemlib as il
title = "<Title from step 4>"
fm = {"id": il.slugify(title), "title": title,
      "section": "<Section from step 4>", "status": "backlog",
      "priority": <priority from step 3>, "needs_spec": False,
      "created": "<today>", "updated": "<today>", "tests": []}
body = """<p><one-sentence plain-English summary></p>

<p><the user's description, lightly cleaned, plus a date and origin note></p>"""
print(il.write_item(il.ITEMS_DIR, fm, body))
PY
```

Field rules — the store contract:

- **`status: backlog`.** A fresh `/additem` item is not-started work. Never
  `in-progress`, `pending-review` or `done`. Use `needs-spec` with
  `needs_spec: true` only if the user explicitly says it needs a spec first.
- **Body is HTML**: `<p>` for paragraphs, `<ul>`/`<li>` for lists,
  `<strong>`/`<em>`, `<code>` for inline code, `<h2>`–`<h4>` for headings,
  `<table>` for tables. The file is still `items/<slug>.md` and the front matter
  is unchanged — markdown allows raw HTML. Escape `<`, `>` and `&` inside prose
  as `&lt;` `&gt;` `&amp;`. Keep checkbox markers as literal text inside the
  `<li>` (`[x]`, `[ ]`, `[~]`) — that's how progress is tracked and grepped for.
- **The first paragraph IS the one-line summary** — a plain `<p>…</p>` with no
  label — then the detail. Keep the user's meaning: fix obvious typos, but do
  **not** invent scope, acceptance criteria, or an approach they didn't give. If
  the raw note is cryptic, preserve it near-verbatim in quotes rather than
  over-interpreting. Stamp its origin, e.g. `Filed via /additem, <date>: "<raw text>"`.

### 6. Regenerate the exports

```bash
python3 items/scripts/export_todo.py
```

`TODO.md` and `DONE.md` are build artifacts of the store — regenerate them,
never hand-edit them.

### 7. Report back

Tell the user the item's **id**, **section** and **priority**, and show the
summary paragraph. Offer to re-route or reword if the placement isn't right.

**Do not commit.** Touch only the new `items/<id>.md` and the regenerated
exports — not `history.md`, not `README.md`, not `TODO-parallel.md`. Recording
those is `/updateitems`' job.

## Don't

- Don't hand-edit `TODO.md` / `DONE.md` — only regenerate them.
- Don't skip the priority question when the description doesn't state one.
- Don't hand-roll the slug or the front matter — go through `itemlib`.
- Don't touch, re-status, or restructure other items; add only the one.
- Don't commit, and don't update `history.md` or `README.md`.
