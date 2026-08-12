---
name: inititems
description: Create an items/ store in a repo that doesn't have one — install the two helper scripts, and if the repo has an existing hand-edited TODO.md, convert each of its entries into an item file, deriving sections and statuses from the file's own conventions and asking about the marker mapping rather than guessing. Non-destructive: the old TODO.md is renamed to TODO.legacy.md with a banner, never deleted or edited. Use when the user says "inititems", "/inititems", or asks to set up, adopt, bootstrap or migrate to the item store.
tools: Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion
---

# inititems

Set a repo up with an `items/` store — the one-file-per-item tracker where each
file's `status:` field is the source of truth — and, if the repo already tracks
work in a hand-edited `TODO.md`, bring that work across.

Run once per repo. Everything after it is `/additem`, `/updateitems`,
`/verifyitems`.

## The rule that governs the whole skill

**The source is never modified and never deleted.** A conversion that eats the
only copy of a work list, and gets a marker mapping subtly wrong on the way, is
unrecoverable. The original `TODO.md` is renamed to `TODO.legacy.md` with a
banner explaining what happened — it stays in git history and on disk, readable,
until the user is satisfied the store is right and deletes it themselves.

## Step 1 — Refuse if a store already exists

```bash
ls items/*.md items/scripts/itemlib.py 2>/dev/null | head
```

If **anything** comes back, stop. A store is already here; this skill would
either duplicate it or overwrite it. Say what you found and point the user at
`/whereitems` to see the current state, or `/additem` to add to it.

Also confirm this is a git repo (`git rev-parse --show-toplevel`). Not a hard
requirement, but the conversion is much safer when it's revertible, and the user
should know if it isn't.

## Step 2 — Install the helper scripts

```bash
mkdir -p items/scripts
cp "$CLAUDE_PLUGIN_ROOT"/item-store/{itemlib.py,export_todo.py,init_items.py} items/scripts/
```

If `$CLAUDE_PLUGIN_ROOT` isn't set — the skill was copied into
`~/.claude/skills/` by hand rather than installed as a plugin — the three files
are in the `item-store/` directory of the item-tracker plugin. Find them, or ask
the user where the plugin lives. **Do not write your own version of them**; the
skills depend on their exact interface.

Verify they work before going further:

```bash
python3 -c "import sys; sys.path.insert(0,'items/scripts'); import itemlib; print('itemlib ok', itemlib.ITEMS_DIR)"
```

`ITEMS_DIR` must point at this repo's `items/`. If it doesn't, the scripts are
in the wrong place — they must sit at `<repo>/items/scripts/`, because the
library derives the repo root from its own location.

## Step 3 — Is there anything to convert?

The file is whatever this project calls it — `TODO.md`, `TODO.txt`, `NOTES.md`,
`backlog.md`. Look, don't assume, and if the user named a file when invoking the
skill, use that one:

```bash
ls TODO* todo* NOTES* notes* BACKLOG* backlog* 2>/dev/null
```

**No existing TODO** → skip to step 7. The store starts empty, which is fine;
the user files into it with `/additem`.

**More than one candidate** → ask which, or whether to convert several. Each
conversion run appends to the same store, so a second file needs `--force` and
should be done as a separate, deliberate run.

**A TODO exists** → let the converter analyze it. **Do not read the file and
hand-write the items yourself.** On a file of any size that drifts: the first
twenty items come out one way and the last twenty another, and nothing is
re-runnable when the marker mapping turns out wrong. The script is
deterministic and the conversion can simply be redone.

```bash
python3 items/scripts/init_items.py TODO.md --scan
```

That writes nothing. It reports:

- **the entry boundary it detected** — `header:3`, `bullet`, or `para`, meaning
  where one item ends and the next begins. Override with `--entry-level` if it
  guessed wrong.
- **the sections it found**, from the headers above the entries, with counts
- **every distinct status marker**, with counts and an example of each
- **sample entry titles with line numbers** — read these. In a file with no
  headers the file's own title line or a legend can look exactly like a task,
  and this is where you catch that.

Read the scan out to the user before going further. If the entry count is
obviously wrong — three items from a 900-line file, or 400 from a 50-line one —
the boundary is wrong. Re-scan with an explicit `--entry-level` rather than
converting and hoping.

## Step 4 — Ask about the marker mapping (do NOT guess)

The status vocabulary is `backlog`, `needs-spec`, `in-progress`,
`pending-review`, `done`. Mapping the file's markers onto it is the one thing
that cannot be derived: an hourglass might mean "in progress" in one project and
"waiting for the user to sign off" in another, and getting it backwards
mislabels the whole store on day one.

Show the user the markers the scan found, with counts and the example of each,
and **ask** with AskUserQuestion. Propose a mapping — an unticked checkbox is
almost certainly `backlog`, a tick almost certainly `done` — and let them
correct it. The target vocabulary is `backlog`, `needs-spec`, `in-progress`,
`pending-review`, `done`.

The trap worth naming to the user: a marker meaning "I think this is finished,
waiting for you to confirm" maps to **`pending-review`**, not `done`. Projects
that use an hourglass or a "pending" tag almost always mean the former, and
mapping it to `done` marks work as signed-off that nobody has looked at.

Priority: if the file encodes one, say so and ask whether to carry it. If it
doesn't, every item gets `priority: 3` — say that rather than inventing a
ranking from where things happen to sit in the file.

## Step 5 — Convert, with a dry run first

```bash
python3 items/scripts/init_items.py TODO.md \
    --map "⬜=backlog,🟡=in-progress,✅=done" --dry-run
```

The dry run prints one line per item — status, id, title — and writes nothing.
Scan it for the two things that are cheap to fix now and awkward later: items
whose title is obviously a fragment (the boundary was wrong), and statuses that
look wrong in bulk (the mapping was wrong). Fix and re-run the dry run until it
reads correctly, then drop `--dry-run`.

The script handles the mechanical parts so they're right on every item rather
than the first twenty: slugs through `itemlib.slugify`, deterministic
disambiguation when two entries produce the same slug, front matter through
`itemlib.write_item`, markdown inline spans converted to HTML, and lazily
wrapped bullet continuations joined back onto their bullet instead of being
shredded into fragments.

It reports any marker it saw that your `--map` didn't cover, and what those
entries fell back to. Don't ignore that line — it means the scan and the mapping
disagreed.

**Summaries.** The first `<p>` of each item is its one-line summary. The script
promotes the entry's first prose line when there is one, and otherwise repeats
the title, because inventing a summary is worse than a dull one. Expect a fair
number of items whose summary equals their title; `/updateitems` sharpens them
as it touches them.

If `--entry-level para` was used — a plain text file with no headers — check the
first few items for the file's own title line masquerading as a task, and delete
it if present.

## Step 6 — Retire the source, don't delete it

Rename it and add a banner at the top explaining what happened, so nothing —
human or agent — mistakes it for the live tracker afterwards:

```bash
git mv TODO.md TODO.legacy.md    # plain mv if not in git
```

The banner should say: this file is retired, the tracker is now `items/*.md`,
use the item skills (`/whereitems`, `/additem`, `/updateitems`, `/verifyitems`)
and not the flat-TODO ones, and it is kept only as a record of the conversion.

This matters more than it looks. A stale `TODO.md` left at the repo root beside
a live store is the single most common way work gets recorded in the wrong
place: it looks entirely plausible, and a skill or a person reading it gets a
confident answer that is months out of date.

Do the same for a `DONE.md` if one exists and its contents were converted.

## Step 7 — Generate the views and hand back

```bash
python3 items/scripts/export_todo.py
```

Then verify the store loads cleanly, which also proves every file you wrote is
well-formed:

```bash
python3 - <<'PY'
import sys, collections; sys.path.insert(0, "items/scripts"); import itemlib as il
items = il.load_items()
print(len(items), "items —", dict(collections.Counter(f["status"] for f in items)))
PY
```

`load_items` raises on a malformed file, so a clean run is real evidence.

**Report:**

- how many items were created, broken down by status and section
- the marker mapping that was used, so a wrong answer in step 4 is visible now
  rather than discovered in a month
- any slug collisions you disambiguated
- any entries you could not confidently convert, by name — better to list six
  awkward ones than to quietly flatten them
- that the original is at `TODO.legacy.md`, unmodified, and that deleting it is
  the user's call once they've checked the store

Then suggest reading `items/exports/TODO.generated.md` and comparing it against
`TODO.legacy.md` side by side. That comparison is the real acceptance test, and
it is much easier now than later.

**Do not commit.** The user owns that step — and for a change this large they
should look first.

## Don't

- Don't run this in a repo that already has a store.
- Don't guess the status-marker mapping; ask.
- Don't hand-write the item files. Run the converter — it is deterministic and
  re-runnable, which hand-conversion of a long file is not.
- Don't delete or edit the source TODO; rename it and band it.
- Don't write your own itemlib; copy the one that ships with the plugin.
- Don't drop detail to make items tidy. An item is the only copy that gets read
  afterwards.
- Don't invent dates, priorities, or acceptance criteria the source didn't have.
- Don't commit.
