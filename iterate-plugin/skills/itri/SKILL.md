---
name: itri
description: Build the current project to a connected iOS device, then iterate (build, test, fix) until the in-flight task is complete and verified on the device. Build and test commands come from the repo's own `make itr-info` declaration, never guessed. All testing goes through the project's test-control interface, forwarded to the host over USB; screenshots go ONLY through the project's own capture path — never osascript or screencapture. Use when the user says "itri", "/itri", or asks to iterate on device until done.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# itri

"Iterate on device until it's done." Build to the connected iOS device,
exercise the change through the project's own test-control interface, fix what's
wrong, and repeat until the task is complete and verified **on the device**.

**Do NOT stop after the first build**, and do not stop at the first green run.

The device sibling of `/itrm` (macOS) and `/itrs` (Simulator).

## Step 0 — ask the repo what its commands are

```bash
make -s --no-print-directory itr-info
```

The keys this skill uses:

| Key | Used for |
| --- | --- |
| `build-ios` | The build-and-install-to-device command. |
| `launch-env` | Environment the app needs so a test client can drive it. |
| `local-port` | The **host-side** port a USB forwarder maps to the device. |
| `port` | The port on the device itself. |
| `client` | The test client that talks to the running app. |
| `tests` | Where the live test suite lives. |
| `screenshot` | How this project captures a screenshot from the running app. |

**If there is no `itr-info` target, or a key you need is missing: ask the user
once** for the build command, how the app is launched so a script can drive it,
and how the control port reaches the host. Then offer to add an `itr-info`
target. **Do not guess a build command** — on a device build the wrong target
can install the wrong artifact, and you will then be testing something you did
not build.

## Which device

If more than one device is connected, or the build needs a device identifier,
**ask which one** rather than picking. Phone and tablet are different targets
with different layouts, and testing the wrong one produces confident wrong
answers. If the user has already said which device this session is about, honor
that.

## The loop

1. **Build and install to the device** with the `build-ios` command, from the
   repo root.
2. **Launch with the control interface enabled**, using `launch-env`.
3. **Reach the control port over USB.** This is the part that differs from the
   macOS and Simulator siblings:
   - **`port=auto` does NOT mean host-side discovery on a device.** The app's
     rendezvous file — the thing a client reads to discover the port — lives *on
     the device*, in the app's own container, and is not reachable from the Mac.
     On a device, `auto` means "connect to the USB-forwarded local port the
     build set up."
   - Use `local-port` for the host side. A device build normally starts a USB
     forwarder mapping `localhost:<local-port>` through to the device; point the
     client there.
   - If the repo declares no `local-port` and the build starts no forwarder, say
     so and ask — do not fall back to testing on macOS instead.
4. **Drive the specific feature you changed.** Read back state, assert it
   behaves.
5. **Diagnose and fix.** Edit the source. Go back to step 1.
6. **Repeat until complete** — the change works on the device, verified through
   the interface, not merely compiled.

## Testing rules

- **The project's own automation only.** Never drive the application with
  `osascript` or any AppleScript or UI-scripting.
- **Write new test scripts when you need them**, in the directory `tests` names.
  Check where the *live* suite is first; a project can have a dead legacy test
  tree alongside the real one.
- **Verify on the same target you built.** You built to the device, so verify on
  the device: relaunch with the control interface enabled and the port
  forwarded. Do not substitute a macOS run for device verification — the whole
  point of this skill rather than `/itrm` is that the device behaves differently.
- **Test the feature, not the world.** Do NOT run a full regression sweep unless
  the user explicitly asks.

## Screenshots — the project's own capture path ONLY

If you take a screenshot it MUST go through the command in the `screenshot` key.
**Never** `osascript`, **never** `screencapture`. If the project declares no
`screenshot` key, ask rather than reaching for a desktop tool.

## Port discipline

Stale device and Simulator instances, and other sessions, can squat the control
port and hand you plausible-looking results **against the wrong binary**. Before
each run confirm what is actually listening (`lsof -iTCP:$PORT`) and switch to a
different port rather than killing whatever is there.

A device that has gone to sleep refuses the connection instantly rather than
timing out. An immediate connection-reset usually means "wake the device", not
"the app is broken" — check that before debugging the app.

## When you're done

State plainly what you changed, how you verified it on the device, and the
observed result. If something still fails after iterating, say so with the
actual output — don't claim completion you didn't reach.
