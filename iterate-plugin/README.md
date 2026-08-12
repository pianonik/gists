# iterate

Four skills that run a build → test → fix loop and **keep looping until the
change actually works** — not until it compiles, and not until the first green
run.

| Skill | Target |
| --- | --- |
| `/itrm` | macOS |
| `/itri` | A connected iOS device |
| `/itrs` | The iOS Simulator |
| `/itrp` | macOS, all formats — standalone plus audio-plugin targets |

They exist because "it built" is the weakest possible evidence, and because an
agent left to choose its own verification will reach for whatever is easiest —
which on a Mac means AppleScript and screenshots of the desktop. Both are
unreliable, and both need a human sitting there watching. These skills refuse
both and go through the project's own automation instead.

## The `itr-info` contract

Rather than assuming build commands, each skill asks the repo for them, through
one Makefile target:

```bash
make -s --no-print-directory itr-info
```

It prints `key=value` lines. Everything is optional; a skill reads the handful of
keys it needs, and if a key it needs is missing it **asks you once** and offers
to add it. It never guesses a build command.

| Key | Meaning |
| --- | --- |
| `build-macos` | Build the macOS standalone. Used by `/itrm`. |
| `build-ios` | Build and install to a connected iOS device. Used by `/itri`. |
| `build-sim` | Build and run on the iOS Simulator. Used by `/itrs`. |
| `build-all` | Build every format including plugins. Used by `/itrp`. |
| `launch-env` | Environment the app needs so a test client can drive it, e.g. a variable that enables a control interface. |
| `port` | The control port: a number, or `auto` when the app picks a free port and publishes it for discovery. |
| `local-port` | Device builds only: the host-side port that a USB forwarder maps to the device. |
| `client` | The test-client script or command that talks to the running app. |
| `tests` | Glob or directory of the live test suite, so new tests land beside the real ones. |
| `screenshot` | How this project captures a screenshot from the running app. |
| `plugin-gate` | The command that validates built plugins. Used by `/itrp`. |
| `instances` | How to list and kill *your own* running instances, for projects where several checkouts build identically-named binaries. |

### Example

```make
itr-info:
	@echo "build-macos=make dmf"
	@echo "build-ios=make dif"
	@echo "build-sim=make sim"
	@echo "build-all=make dm"
	@echo "launch-env=MYAPP_REMOTE_ENABLE=1 MYAPP_REMOTE_PORT=auto"
	@echo "port=auto"
	@echo "client=scripts/myapp_remote.py"
	@echo "tests=scripts/test_*.py"
	@echo "screenshot=snapshot verb via scripts/myapp_remote.py"
	@echo "plugin-gate=make validate-plugins"
	@echo "instances=python3 scripts/instances.py --kill-mine"
```

A project with no `make` at all can still use these skills — the first run asks
for the two or three commands it needs and offers to record them somewhere the
repo can keep them.

## Why `port=auto` matters

If the control port is a fixed number, anything else already listening on it —
a stale instance, another checkout's build, an unrelated tool — will answer your
test client and hand back plausible-looking results **from the wrong binary**.
Every assertion passes; none of them tested what you built.

`auto` means the app takes a free port and publishes it for discovery, so each
instance is reachable unambiguously. Where a project supports it, the skills
prefer it. Where the port is fixed, they check what is actually listening first
(`lsof -iTCP:$PORT`) and switch ports rather than killing whatever is there —
it may be another person's session.

## Screenshots

Only two sources are allowed: the project's own capture path (the `screenshot`
key) and, on the iOS Simulator, `xcrun simctl io screenshot`. Never
`screencapture`, never `osascript`.

The two are not interchangeable, and `/itrs` says so explicitly:

- **Real on-screen and clipping questions → the Simulator framebuffer.** It
  shows what is actually on screen, including clipping.
- **Component and state snapshots → the project's own capture.** Convenient and
  reliable, but it typically renders a component in isolation and therefore
  *hides* clipping. Don't trust it for a layout question.
