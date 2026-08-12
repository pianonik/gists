# item-tracker

Five skills for a project that tracks work as **one markdown file per item**
under `items/`, where each file's `status:` field is the source of truth and
`TODO.md` / `DONE.md` are generated views rather than hand-edited files.

## Setting it up

The skills call two helper scripts that live in your repo. Working copies are
included here, so this is the whole installation:

```bash
mkdir -p items/scripts && cp item-store/*.py items/scripts/
```

Standard-library Python 3, no dependencies. See
[item-store/README.md](item-store/README.md) for what they do, and
[ITEM-STORE-FORMAT.md](ITEM-STORE-FORMAT.md) for the item file format.

**In a repo without an item store, all five skills stop cleanly** and point you
at the flat-`TODO.md` equivalents in the **project-docs** plugin. Installing
this costs nothing in a repo that doesn't use the format.

## The skills

| Skill | Counterpart | Does |
| --- | --- | --- |
| `/whereitems` | `/wherex` | Reads `history.md`, `README.md` and the store; summarizes where the project stands. Read-only. |
| `/additem <text>` | `/addtodo` | Files one new item. Derives title, slug and section from the store's live conventions; **asks for the priority** rather than defaulting, because priority is the user's call. |
| `/updateitems` | `/updatex` | Writes the session into the store — flips status, stamps dates, refines bodies, creates follow-up items — then `history.md`, then regenerates the exports. |
| `/updateitemplan` | `/updateplan` | Re-derives the structural `TODO-parallel.md`, after verifying each item's `status:` against the real code and git log, and flipping the ones that have verifiably shipped. |
| `/planning-items-review` | `/planning-review` | The deep audit: store and docs against source, dead code, status drift, what is really built. Read-only; reports drift but never flips a status itself. |

## Who flips a status

Worth being explicit, because the five skills deliberately differ:

- `/additem` only ever writes `backlog`.
- `/updateitems` flips the status of items **this conversation** worked on.
- `/updateitemplan` flips a status **only on verified code and git evidence**,
  and lists every flip at the end so you can reverse it.
- `/planning-items-review` **never** flips anything. It reports drift and
  suggests `/updateitemplan` if there's a lot of it.
- Nothing marks an item `done` on your behalf when the work merely appears
  finished — that goes to `pending-review`, awaiting your sign-off.

None of them commits. That's yours.
