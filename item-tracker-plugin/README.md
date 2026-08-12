# item-tracker

Six skills for a project that tracks work as **one markdown file per item**
under `items/`, where each file's `status:` field is the source of truth and
`TODO.md` / `DONE.md` are generated views rather than hand-edited files.

## Setting it up

**Run `/inititems` once.** It creates `items/`, installs the two helper scripts,
and — if the repo already has a hand-edited `TODO.md` — converts each entry into
an item file. It asks you how to map the file's status markers onto the store's
vocabulary rather than guessing, because that mapping is the one thing that
cannot be derived: an hourglass means "in progress" in one project and "waiting
for sign-off" in another.

It never edits or deletes the original. `TODO.md` is renamed to
`TODO.legacy.md` with a banner explaining what happened, so you can put the
generated view beside it, check the conversion, and delete it yourself when
satisfied.

To set up by hand instead:

```bash
mkdir -p items/scripts && cp item-store/*.py items/scripts/
```

Standard-library Python 3, no dependencies. See
[item-store/README.md](item-store/README.md) for what the scripts do, and
[ITEM-STORE-FORMAT.md](ITEM-STORE-FORMAT.md) for the item file format.

**In a repo without an item store, the other five skills stop cleanly** and
point you at the flat-`TODO.md` equivalents in the **project-docs** plugin.
Installing this costs nothing in a repo that doesn't use the format.

## The skills

| Skill | Counterpart | Does |
| --- | --- | --- |
| `/inititems` | — | Creates the store. Converts an existing `TODO.md` into items, non-destructively. Run once per repo. |
| `/whereitems` | `/wherex` | Reads `history.md`, `README.md` and the store; summarizes where the project stands. Read-only. |
| `/additem <text>` | `/addtodo` | Files one new item. Derives title, slug and section from the store's live conventions; **asks for the priority** rather than defaulting, because priority is the user's call. |
| `/updateitems` | `/updatex` | Writes the session into the store — flips status, stamps dates, refines bodies, creates follow-up items — then `history.md`, then regenerates the exports. |
| `/verifyitems` | `/verifytodo` | Audits every item's `status:` against the real code and git log, flips what has verifiably shipped, flips back any `done` item that turns out incomplete, reports the ambiguous. |
| `/planning-items-review` | `/planning-review` | The deep audit: store and docs against source, dead code, status drift, what is really built. Read-only. |

## Who flips a status

Worth being explicit, because the skills deliberately differ:

- `/inititems` sets the initial statuses, from a mapping **you** confirmed.
- `/additem` only ever writes `backlog`.
- `/updateitems` flips the status of items **this conversation** worked on.
- `/verifyitems` flips a status **only on verified code and git evidence**, and
  lists every flip at the end so you can reverse it. This is the only skill that
  audits the whole store and corrects it.
- `/planning-items-review` **never** flips anything. It reports drift and
  suggests `/verifyitems` if there's a lot of it.
- Nothing marks an item `done` on your behalf when the work merely appears
  finished — that goes to `pending-review`, awaiting your sign-off.

None of them commits. That's yours.
