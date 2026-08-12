# item-store — the scripts your repo needs

The skills in this plugin don't read and write item files themselves. They call
these three, which live **in your repo**, so the store's format and its tooling
stay versioned together with the content.

## Install

```bash
mkdir -p items/scripts
cp item-store/{itemlib.py,export_todo.py,init_items.py} items/scripts/
```

That's the whole installation. All three are standard-library Python 3, no
dependencies. `/inititems` does this for you.

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

## init_items.py

Converts a hand-written TODO file into a store. The file can be `TODO.md`,
`TODO.txt`, `NOTES.md` — anything; pass its path. It does not have to be tidy.

```bash
python3 items/scripts/init_items.py TODO.md --scan      # analyze, write nothing
python3 items/scripts/init_items.py TODO.md --map "⬜=backlog,🟡=in-progress,✅=done" --dry-run
python3 items/scripts/init_items.py TODO.md --map "⬜=backlog,🟡=in-progress,✅=done"
```

`--scan` first, always. It reports the entry boundary it detected, the sections,
every distinct status marker with counts and an example, and sample entry titles
with line numbers. You need that before you can write a sensible `--map`, and
it's where you catch a boundary guess that's wrong.

| Flag | |
| --- | --- |
| `--scan` | Analyze and print; write nothing. |
| `--entry-level` | `header:N`, `bullet`, or `para` — where one item ends and the next begins. Auto-detected; override when the guess is wrong. |
| `--map` | `MARKER=status,...`. Markers are **never** guessed: the same glyph means different things in different projects. |
| `--default-status` | For entries with no recognized marker. Default `backlog`. |
| `--dry-run` | Print one line per item; write nothing. |
| `--force` | Write into a store that already has items. |

What it handles so you don't have to: sections from the headers above each
entry, slugs through `slugify` with deterministic disambiguation on collision,
front matter through `write_item`, markdown inline spans (`**bold**`,
`` `code` ``) converted to HTML, and lazily wrapped bullet continuations joined
back onto their bullet rather than shredded into fragments.

Two things it will not do:

- **It never modifies or deletes the source.** Retiring the old TODO is a
  separate, deliberate step.
- **It refuses to write into a populated store** without `--force`. Converting
  twice into one directory merges two readings of the same file, which is very
  hard to unpick later.

Entry titles become item titles verbatim, and an item's summary is its first
prose line, or its title when the entry has no prose. It does not invent
summaries, priorities, or dates.
