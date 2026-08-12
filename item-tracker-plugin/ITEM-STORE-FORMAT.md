# The item store

The five skills in this plugin operate on a tracker where **each work item is
one markdown file** under `items/` at the repo root, and that file's `status:`
field is the single source of truth for whether the item is open or done.

`TODO.md` and `DONE.md` become *generated views* — build artifacts of the store,
never hand-edited. That is the whole reason the format exists: with a flat
`TODO.md`, two sessions editing two unrelated items collide in one file, and
"what is actually open" drifts from what the markers say. One file per item
removes both problems.

## The file

`items/<id>.md`, where `<id>` is the slug of the title:

```markdown
---
id: fix-preset-load-order
title: Fix preset load order
section: Audio Chain
status: in-progress
priority: 2
needs_spec: false
created: 2026-08-01
updated: 2026-08-12
tests:
  - test_preset_load.py
---

<p>One-sentence, plain-English summary — this first paragraph is the subtitle
shown in generated views.</p>

<p>Full detail: what the work is, decisions taken, what remains.</p>
```

### Front matter

A controlled YAML subset: `key: value` scalars plus `- item` lists. Nothing
nested. A parser for it should **fail loudly** on anything malformed rather than
silently reshaping the file.

| Field | Meaning |
| --- | --- |
| `id` | The slug. Matches the filename stem. Derived from the title, never hand-rolled. |
| `title` | Short imperative title, roughly 60 characters or less. Quote it if it contains `:` or `#`. |
| `section` | Grouping, e.g. `Audio Chain`. `Uncategorized` when nothing fits. Sections are whatever the store already uses — derive them, don't invent a scheme. |
| `status` | One of `backlog`, `needs-spec`, `in-progress`, `pending-review`, `done`. |
| `priority` | 1 highest to 5 lowest. **User-owned** — a skill never silently picks one. |
| `needs_spec` | Boolean. True when the item can't be worked until it is specified. |
| `created` | Date first filed. Never moves once set. |
| `updated` | Stamped to today on any edit — status, body, or priority. |
| `tests` | Bare list of test files that gate the item. Empty is just `tests:`. |

### The status vocabulary

- `backlog` — filed, not started. What a freshly captured item gets.
- `needs-spec` — needs to be specified before it can be worked.
- `in-progress` — partially built.
- `pending-review` — the work is finished but the user hasn't signed off. This
  is the important one: when a session completes an item, it goes here, not to
  `done`. A pile-up of `pending-review` means the real bottleneck is review, not
  work.
- `done` — finished and confirmed.

An item is never deleted to mark it finished; its status changes. The store
keeps done items, and the export splits open from done by status.

### The body

The body is HTML — `<p>`, `<ul>` / `<li>`, `<strong>`, `<em>`, `<code>`,
`<h2>` through `<h4>`, `<table>`. Markdown permits raw HTML, so an HTML body is
still a valid `.md` file, and the front matter is unchanged. Escape `<`, `>` and
`&` inside prose as `&lt;`, `&gt;`, `&amp;`.

The **first paragraph is the item's one-line summary** — a plain `<p>…</p>` with
no label. Everything after it is detail.

Progress checkboxes stay as literal text inside a `<li>`: `[x]` done, `[ ]` not
done, `[~]` partial. That is how progress is tracked and how it is grepped for.

Cross-reference another item with `[[its-id]]`.

## What the repo must provide

The skills call into two helper scripts that live in the repo, at
`items/scripts/`. They are deliberately repo-side rather than bundled here, so
the store's format and its tooling stay versioned together with the content.

### `items/scripts/itemlib.py`

The library. Skills import it with
`sys.path.insert(0, "items/scripts"); import itemlib`. It must expose:

| Name | Contract |
| --- | --- |
| `ITEMS_DIR` | Path to the store, derived from the module's own location so that running it from inside a git worktree edits *that* worktree's copy. |
| `load_items()` | Returns every item as a dict of the front-matter fields plus `body`. Raises on a malformed file — that failure is useful signal, not something to swallow. |
| `load_item(path)` | One item, same shape. Raises if the id is wrong. |
| `write_item(dir, front_matter, body)` | Writes `<dir>/<id>.md` with the canonical front-matter layout and quoting. Returns the path. Skills create items *through* this rather than by hand, so byte-level formatting stays consistent. |
| `slugify(title)` | Lowercase; every run of non-alphanumerics becomes one `-`; trimmed; capped at 48 characters on a `-` boundary. |

### `items/scripts/export_todo.py`

Regenerates the human-readable views — `TODO.md` and `DONE.md`, or files under
`items/exports/` — from the store, split by status and grouped by section.
Run after any write. Never hand-edit its output.

## Adopting this in a repo that doesn't have it

The skills all check for `items/scripts/itemlib.py` first and stop cleanly if it
isn't there, pointing you at the flat-`TODO.md` equivalents in the
**project-docs** plugin. So installing this plugin costs nothing in a repo that
doesn't use the format.

To adopt it, implement the two scripts above against this contract — the library
is roughly eighty lines of Python, since the front matter is a deliberately tiny
YAML subset — and put your existing items in `items/*.md`.
