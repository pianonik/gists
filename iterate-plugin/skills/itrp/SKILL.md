---
name: itrp
description: Build the current project on macOS in ALL formats — standalone plus the audio-plugin targets — then iterate (build, test, fix) until the in-flight task is complete. Standalone testing goes through the project's test-control interface; plugin formats are verified through the project's plugin gate (validators plus a scriptable test host). Commands come from the repo's own `make itr-info` declaration, never guessed. Screenshots go ONLY through the project's own capture path. Use when the user says "itrp", "/itrp", or asks to iterate on macOS including the plugins.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# itrp

"Iterate on macOS, plugins included, until it's done." The all-formats sibling
of `/itrm`: where that one builds only the standalone application, this builds
**every** macOS format — standalone and the audio-plugin targets — verifies the
change in **both** worlds, fixes what's wrong, and repeats.

**Do NOT stop after the first build**, and do not stop at the first green run.

## Step 0 — ask the repo what its commands are

```bash
make -s --no-print-directory itr-info
```

The keys this skill uses:

| Key | Used for |
| --- | --- |
| `build-all` | The all-formats build command. |
| `launch-env` | Environment the standalone needs so a test client can drive it. |
| `port` | The control port: a number, or `auto`. |
| `client` | The test client that talks to the running standalone. |
| `tests` | Where the live test suite lives. |
| `plugin-gate` | The command that validates the built plugins. |
| `screenshot` | The project's own capture path. |

**If there is no `itr-info` target, or a key you need is missing: ask the user
once** for the all-formats build command and the plugin validation command, then
offer to add the target. **Do not guess** — an all-formats build is expensive,
and running the standalone-only target instead means the plugin half of the work
was never built.

## The loop

1. **Build all formats** with the `build-all` command, from the repo root.
2. **Verify the standalone side** through the test-control interface: launch
   with `launch-env`, resolve the port from `port` (prefer `auto`; never
   hardcode), drive the specific feature you changed, and assert it behaves.
3. **Verify the plugin side through the plugin gate.** A build that only ran in
   the standalone proves **nothing** about the plugins — they load into a
   different host, with a different lifecycle, different buffer sizes, and
   different threading.

   Run the `plugin-gate` command. What a good gate does, and what to check yours
   does:
   - It **installs the freshly built plugins** where hosts look for them, then
     runs the validators. Pairing a validation step with plugins you rebuilt but
     did not reinstall tests the *previous* build — a silent false pass.
   - It runs the format validators, then any scenario suite the project has.

   For a feature-focused check, **add or extend a scenario in the project's test
   host** rather than eyeballing the plugin in a digital audio workstation.
4. **Diagnose and fix.** Edit the source. Go back to step 1.
5. **Repeat until complete** — the change works in the standalone **and** the
   plugin formats pass the gate.

## Testing rules

- **The project's own automation only.** Application testing goes through the
  test-control interface; plugin testing goes through the validators and the
  scriptable test host. Never drive an application or a digital audio workstation
  with `osascript` or any AppleScript or UI-scripting.
- **Write new test scripts when you need them** — a test in the suite `tests`
  names, or a scenario in the plugin test host for plugin-side behavior.
- **Test the feature, plus the plugin gate.** Do NOT run a full regression sweep
  unless the user explicitly asks.

## Screenshots — the project's own capture path ONLY

If you take a screenshot it MUST go through the command in the `screenshot` key.
**Never** `osascript`, **never** `screencapture`.

## Port discipline

Stale instances and other sessions can squat a fixed control port and hand you
plausible-looking results against the wrong binary. Prefer `auto` where the
project supports it. If the port is fixed, confirm what is actually listening
(`lsof -iTCP:$PORT`) and switch ports rather than killing whatever is there.

## When you're done

State plainly what you changed and how you verified it — **both** the
test-interface result for the standalone and the validator or test-host result
for the plugins — with the observed output. If something still fails after
iterating, say so with the actual output; don't claim completion you didn't
reach. In particular, don't report the plugin side as verified on the strength
of the standalone passing.
