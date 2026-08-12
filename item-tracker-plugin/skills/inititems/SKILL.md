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
cp "$CLAUDE_PLUGIN_ROOT/item-store/itemlib.py" \
   "$CLAUDE_PLUGIN_ROOT/item-store/export_todo.py" items/scripts/
```

If `$CLAUDE_PLUGIN_ROOT` isn't set — the skill was copied into
`~/.claude/skills/` by hand rather than installed as a plugin — the two files
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

```bash
ls TODO.md TODO.txt 2>/dev/null
```

**No existing TODO** → skip to step 7. The store starts empty, which is fine;
the user files into it with `/additem`.

**A TODO exists** → read it in full, then work out its conventions before
converting anything:

```bash
grep -nE '^#+ ' TODO.md          # the section structure
```

Note three things, and derive all of them from the file rather than assuming:

- **The section structure.** Headers become the `section:` field. Deeply nested
  headers usually collapse: a top-level header is the section, and entries under
  it are items.
- **What one item looks like.** A bullet? A third-level header with prose under
  it? This decides where one item ends and the next begins, and getting it wrong
  produces either one enormous item or a hundred fragments.
- **The status markers in use.** Checkboxes, emoji, inline tags like `[FIXED]`,
  or position under a "landed" heading. Collect the distinct ones with their
  counts.

## Step 4 — Ask about the marker mapping (do NOT guess)

The status vocabulary is `backlog`, `needs-spec`, `in-progress`,
`pending-review`, `done`. Mapping the file's markers onto it is the one thing
that cannot be derived: an hourglass might mean "in progress" in one project and
"waiting for the user to sign off" in another, and getting it backwards
mislabels the whole store on day one.

Show the user the distinct markers you found, with counts and one example line
each, and **ask** with AskUserQuestion. Propose a mapping — an unticked checkbox
is almost certainly `backlog`, a tick almost certainly `done` — and let them
correct it. If a marker is genuinely ambiguous even after asking, map it to
`backlog` and list those items in the report so they're easy to find.

Ask about priority in the same pass, if the file encodes it. If it doesn't,
every item gets `priority: 3` — say so rather than inventing a ranking from
where things happen to sit in the file.

## Step 5 — Convert, through itemlib

Create the items **through `itemlib.write_item`** so slugs, quoting and
front-matter layout are right by construction. Get today's date from
`date +%Y-%m-%d`.

Per entry:

- **`title`** — the entry's own title, cleaned up but not reworded. Keep the
  user's nouns. Roughly 60 characters; if the entry's first line is a paragraph,
  condense to a title and keep the full text in the body.
- **`id`** — `itemlib.slugify(title)`. **Check for collisions** as you go: two
  entries called "Fix the crash" in different sections produce the same slug and
  the second would silently overwrite the first. On a collision, disambiguate
  with a word from the section and note it in the report.
- **`section`** — the header it lived under. `Uncategorized` if it had none.
- **`status`** — from the mapping agreed in step 4.
- **`priority`** — from the file if it encodes it, else 3.
- **`created`** — a date the entry itself states, if it has one; otherwise
  today. Don't fabricate a plausible-looking older date.
- **`updated`** — today.
- **`tests`** — test filenames the entry names, if any; else empty.
- **Body** — HTML. The first `<p>` is the one-line summary; everything else
  follows as detail. **Carry the entry's full text across.** Losing detail in
  conversion is the failure mode that matters: the item is the only copy people
  will read afterwards. Preserve file references, dates, decisions and
  sub-checkboxes (`[x]` / `[ ]` / `[~]` as literal text inside `<li>`).

Work in batches and keep count. On a large TODO this is the slow part; say how
many you've done if the user is watching.

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
- Don't delete or edit the source TODO; rename it and band it.
- Don't hand-roll slugs or front matter; go through `itemlib`.
- Don't write your own itemlib; copy the one that ships with the plugin.
- Don't drop detail to make items tidy. An item is the only copy that gets read
  afterwards.
- Don't invent dates, priorities, or acceptance criteria the source didn't have.
- Don't commit.
