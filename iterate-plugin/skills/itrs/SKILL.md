---
name: itrs
description: Build and run the current project on the iOS Simulator, then iterate (build, test, fix) until the in-flight task is complete and verified. Build and test commands come from the repo's own `make itr-info` declaration, never guessed. All testing goes through the project's test-control interface; screenshots go ONLY through the project's own capture path or `xcrun simctl io screenshot` — never osascript or screencapture. Use when the user says "itrs", "/itrs", or asks to iterate on the Simulator until done.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# itrs

"Iterate on the iOS Simulator until it's done." Build and run on the Simulator,
exercise the change through the project's own test-control interface, fix what's
wrong, and repeat until the task is complete and verified.

**Do NOT stop after the first build**, and do not stop at the first green run.

The Simulator sibling of `/itrm` (macOS) and `/itri` (connected device).

## Step 0 — ask the repo what its commands are

```bash
make -s --no-print-directory itr-info
```

The keys this skill uses:

| Key | Used for |
| --- | --- |
| `build-sim` | The build-and-run-on-Simulator command. |
| `launch-env` | Environment the app needs so a test client can drive it. |
| `port` | The control port: a number, or `auto`. |
| `client` | The test client that talks to the running app. |
| `tests` | Where the live test suite lives. |
| `screenshot` | The project's own capture path. |

**If there is no `itr-info` target, or a key you need is missing: ask the user
once**, then offer to add the target. **Do not guess a build command.**

## The loop

1. **Build and run on the Simulator** with the `build-sim` command, from the
   repo root.
2. **Launch with the control interface enabled**, using `launch-env`. When
   relaunching, terminate any already-running copy first — most launch tools
   have a flag for this. A leftover Simulator instance squatting the app is a
   classic false positive: it answers, it passes, and it is running the previous
   build.
3. **Resolve the port — never hardcode it.**
   - `port=auto` → the app takes a free port and publishes it for discovery. Let
     the client auto-connect.
   - a number → point the client at it, after checking what is already
     listening.
4. **Drive the specific feature you changed.** Read back state, assert it
   behaves.
5. **Diagnose and fix.** Edit the source. Go back to step 1.
6. **Repeat until complete** — verified through the interface, not merely
   compiled.

## Running the Simulator and a desktop build at the same time

This is normal, and it is where the Simulator loop most often goes wrong: both
instances are yours, both answer, and a client that picks one arbitrarily will
happily run your whole suite against the desktop build while you believe you are
testing the Simulator. Every assertion passes and nothing was tested.

If the project's client can select a platform explicitly, do that. If it cannot,
run only one at a time, and check which one you are actually connected to before
trusting a result.

## Testing rules

- **The project's own automation only.** Never drive the application with
  `osascript` or any AppleScript or UI-scripting.
- **Write new test scripts when you need them**, in the directory `tests` names.
  Check where the *live* suite is first.
- **Test the feature, not the world.** Do NOT run a full regression sweep unless
  the user explicitly asks.

## Screenshots — the project's capture path or `simctl` ONLY

**Never** `osascript`, **never** `screencapture`. Which of the two to use is not
a matter of taste — they show different things:

- **Real on-screen and clipping questions → `xcrun simctl io screenshot`.** It
  captures the actual Simulator framebuffer, so it shows true clipping and
  layout. If the app is landscape-only, the framebuffer comes out rotated;
  rotate the image before reading it.
- **Component and state snapshots → the project's own capture** (the
  `screenshot` key). Convenient and reliable, but it typically renders a
  component in isolation and therefore **hides on-screen clipping**. Do not
  trust it for a layout or clipping question.

## Port discipline

Stale Simulator instances and other sessions can squat the control port and hand
you plausible-looking results against the wrong binary. Prefer `auto`. If the
port is fixed, confirm what is actually listening (`lsof -iTCP:$PORT`) and
switch ports rather than killing whatever is there.

## Simulator troubles that are not your bug

Worth ruling out before debugging the application:

- A Simulator runtime version that crashes at audio or graphics startup, before
  any application code runs. Try a different runtime version before assuming
  your change caused it.
- A launch screen that appears not to have changed: Simulator caches the launch
  snapshot. Erase the device's content or delete the cached snapshot rather than
  concluding the change didn't take.
- Preferences left over from a previous install producing a false negative.
  Uninstall and reinstall before believing a settings-related failure.

## When you're done

State plainly what you changed, how you verified it on the Simulator, and the
observed result. If something still fails after iterating, say so with the
actual output — don't claim completion you didn't reach.
