# Maintaining this repo

Notes for editing and releasing these skills. Users of the skills don't need
this file.

## Where things are

| | |
| --- | --- |
| Working copy | `~/Developer/claude-skills` |
| Remote | `git@github.com:pianonik/gists.git`, branch `main` |
| Published as | `pianonik/gists` — the name people type into `/plugin marketplace add` |

The directory name and the repo name differ on purpose: the local directory says
what it holds, the repo name matches the marketplace convention.

## Making a change

```bash
cd ~/Developer/claude-skills
# edit
git add -A && git commit -m "..." && git push
```

Anyone who has already run `/plugin marketplace add pianonik/gists` gets the
change the next time their marketplace refreshes. There is no build step and no
release process — the repo is the artifact.

Use a plain `git commit` here. This repo is not part of any tree that has a
commit wrapper, and it has no branch-tagging convention.

## Layout

```
.claude-plugin/marketplace.json     lists the five plugins
<name>-plugin/
  .claude-plugin/plugin.json        name, description, version, license
  README.md                         what the plugin is for
  skills/<skill>/SKILL.md           the skill itself
```

A skill is its `SKILL.md`: YAML front matter with `name`, `description` and
`tools`, then markdown instructions. The `description` is what Claude matches
against when deciding whether the skill applies, so it should name the trigger
words and say plainly what the skill does.

Adding a skill to an existing plugin means one new directory under that plugin's
`skills/`. Adding a plugin means a new top-level directory plus an entry in
`marketplace.json`.

## Rules these skills are written to

Two, and they are the reason the skills port at all.

**No project-specific facts in a skill.** Build command, base branch, commit
convention, tracker layout, test runner — derive them from the repo at run time,
or read them from a declared contract like the `itr-info` Makefile target, or
ask the user once. Never bake in an answer that happens to be right for one
project.

**Fail loud.** When a skill cannot work something out, it stops and says what is
missing. It does not pick a plausible default. A skill that guesses a build
command wastes a build cycle at best and installs the wrong artifact at worst,
and an unattended session will not notice either.

Also: no `model:` pin in the front matter, so a skill inherits whatever model the
session is using. And no references to anything outside the repo — a link to a
private note is dead weight for everyone else.

## Testing before pushing

There is no test suite. What is worth checking by hand:

```bash
# JSON parses
for f in .claude-plugin/marketplace.json */.claude-plugin/plugin.json; do
  python3 -c "import json,sys; json.load(open(sys.argv[1])); print('ok', sys.argv[1])" "$f"
done

# every skill has name and description front matter
for f in */skills/*/SKILL.md; do
  grep -q '^name:' "$f" && grep -q '^description:' "$f" || echo "BAD FRONT MATTER: $f"
done

# the item-store scripts still compile and round-trip
python3 -m py_compile item-tracker-plugin/item-store/*.py
```

If a skill contains shell, run the shell. Fragments that look obviously correct
are where the bugs are — a branch-detection snippet that works on a repo with a
remote and fails on one without, for instance. Test against a repo on `main`
with no remote, a repo on `master`, and a real repo with an origin.

Before pushing, check nothing personal has crept in: absolute home paths, a
private project name, an internal hostname, a colleague's name.

## Relationship to the private originals

These are the generalized descendants of a personal `~/.claude/skills`
collection. The two sets are **not** synced, and the private ones are still what
runs day to day on the machine they were written for.

Consequences worth remembering:

- A fix made here does not reach the private copies, and the reverse.
- The private `/itrm` and its siblings have their build commands written
  directly inside them. The public ones read `make itr-info`. Switching to the
  public ones in an old project means adding that target first.
- Three skills were renamed on the way out, because the originals meant nothing
  outside their home project: a project-specific review skill became
  `/projectreview`, a wrapper-script skill became `/commit`, and a disk tool
  became `/diskusage`.
