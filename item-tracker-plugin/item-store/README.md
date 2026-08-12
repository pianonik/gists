# item-store — the two scripts your repo needs

The five skills in this plugin don't read and write item files themselves. They
call these two, which live **in your repo**, so the store's format and its
tooling stay versioned together with the content.

## Install

```bash
mkdir -p items/scripts
cp item-store/itemlib.py item-store/export_todo.py items/scripts/
```

That's the whole installation. Both are standard-library Python 3, no
dependencies, 240 lines between them.

Then put your items in `items/*.md` — see
[../ITEM-STORE-FORMAT.md](../ITEM-STORE-FORMAT.md) for the file format — and
run:

```bash
python3 items/scripts/export_todo.py
```

## itemlib.py

The library the skills import. What they use:

| Name | Does |
| --- | --- |
| `ITEMS_DIR` | Path to the store, derived from this file's own location. |
| `load_items(dir=ITEMS_DIR)` | Every item as a dict of front-matter fields plus `body` and `path`. |
| `load_item(path)` | One item, same shape. |
| `write_item(dir, front_matter, body)` | Writes `<dir>/<id>.md` with canonical field order and quoting. Returns the path. |
| `slugify(title)` | The id: lowercase, non-alphanumeric runs become `-`, capped at 48 characters on a `-` boundary. |

Two design points worth keeping if you modify it:

**It fails loud.** A malformed front-matter block, or a status outside the five
allowed values, raises rather than being skipped. A tracker that silently drops
an unreadable item reports a work list that is quietly missing something.

**`ITEMS_DIR` is derived from the file's own location**, not passed in. That is
what makes the store behave correctly inside a git worktree: running the script
from a worktree edits *that* worktree's copy of the store. The batch runner in
the worktree-batch plugin depends on this.

## export_todo.py

Regenerates `items/exports/TODO.generated.md` and `DONE.generated.md` from the
store — every open item and every done item, grouped by section, sorted by
priority then status.

It writes into `items/exports/` rather than over a repo-root `TODO.md`, so
adopting the store doesn't clobber a hand-authored file on day one. Point it at
the repo root once you're ready for it to own those files.

The generated files are build artifacts. Edit the items and re-run this; never
hand-edit the output.

Page titles come from the repo directory's name. Section order follows the
smallest `legacy_num` in each section, which keeps a migrated store in the order
people already know, and falls back to alphabetical for a store that never had
section numbers.
