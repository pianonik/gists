---
name: itrm
description: Build the current project on macOS, then iterate (build, test, fix) until the in-flight task is complete and verified. Build and test commands come from the repo's own `make itr-info` declaration, never guessed. All testing goes through the project's test-control interface; new test scripts are written when needed; screenshots go ONLY through the project's own capture path — never osascript or screencapture. Use when the user says "itrm", "/itrm", or asks to iterate on macOS until done.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# itrm

"Iterate on macOS until it's done." Build the project, exercise the change
through the project's own test-control interface, fix what's wrong, and repeat
until the task is actually complete and verified.

**Do NOT stop after the first build**, and do not stop at the first green run.
A change that compiles is not a change that works.

The macOS sibling of `/itri` (connected device) and `/itrs` (Simulator). For a
build that includes audio-plugin formats, use `/itrp`.

## Step 0 — ask the repo what its commands are

```bash
make -s --no-print-directory itr-info
```

It prints `key=value` lines. The keys this skill uses:

| Key | Used for |
| --- | --- |
| `build-macos` | The build command. |
| `launch-env` | Environment the app needs so a test client can drive it. |
| `port` | The control port: a number, or `auto`. |
| `client` | The test client that talks to the running app. |
| `tests` | Where the live test suite lives, so a new test lands beside the real ones. |
| `screenshot` | How this project captures a screenshot from the running app. |
| `instances` | How to list and kill your own running instances. |

**If there is no `itr-info` target, or a key you need is missing: ask the user
once**, in one message, for the specific things you're missing — the build
command, how to launch the app so a script can drive it, and how its tests are
run. Then offer to add an `itr-info` target so the next run doesn't ask. **Do
not guess a build command** and do not go hunting through the Makefile for
something that looks plausible; running the wrong target wastes a full build
cycle and can install the wrong artifact.

If the project has no test-control interface at all, say so plainly and ask how
the user wants the change verified before you start looping. Do not substitute
manual eyeballing and call it verified.

## The loop

1. **Build.** Run the `build-macos` command from the repo root, which is the
   current working directory.
2. **Launch with the control interface enabled**, using `launch-env`, so the
   test client can drive the app.
3. **Resolve the port — never hardcode it.**
   - `port=auto` → the app takes a free port and publishes it for discovery. Let
     the client auto-connect; pass no port at all.
   - a number → point the client at that port, after checking what is already
     listening (see "Port discipline" below).
4. **Drive the specific feature you changed.** Read back state, assert it
   behaves. Use the `client` command and the suite under `tests`.
5. **Diagnose and fix.** Edit the source. Go back to step 1.
6. **Repeat until complete** — the change works, verified through the interface,
   not merely compiled.

## Testing rules

- **The project's own automation only.** All testing and inspection goes through
  the project's test-control interface or test suite. Never drive the
  application with `osascript` or any AppleScript or UI-scripting. It is
  unreliable, it needs a human watching, and it silently does the wrong thing
  when a window isn't where it was.
- **Write new test scripts when you need them.** If the existing tests don't
  cover what you changed, add one, in the directory `tests` names. Prefer a
  reusable test file over throwaway one-liners when the check is worth keeping.
  Check where the *live* suite is before adding: a project can have a dead
  legacy test tree alongside the real one, and a test added to the dead tree
  never runs.
- **Test the feature, not the world.** Exercise the in-flight change. Do NOT run
  a full regression sweep unless the user explicitly asks for one.

## Screenshots — the project's own capture path ONLY

If you take a screenshot it MUST go through the command in the `screenshot` key.
**Never** `osascript`, **never** `screencapture`, never any other desktop
capture tool. If the project declares no `screenshot` key, ask rather than
reaching for a desktop tool.

## Port discipline

Other sessions and stale instances can squat a fixed control port and hand you
plausible-looking results **against the wrong binary** — every assertion passes,
none of them tested what you built.

Prefer `auto` where the project supports it. If the port is fixed, confirm what
is actually listening first (`lsof -iTCP:$PORT`) and switch ports rather than
killing whatever is there; it may belong to another person's session.

If the repo declares an `instances` command, use it to list and clean up **your
own** instances, and use it rather than killing processes by name pattern — in a
project where several checkouts build identically-named binaries, a name-pattern
kill takes out other people's work.

Kill your instances when the round ends.

## When you're done

State plainly what you changed, how you verified it, and the observed result. If
something still fails after iterating, say so with the actual output — don't
claim completion you didn't reach.
