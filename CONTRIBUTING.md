# Contributing to AirControl

First off — thanks for wanting to contribute. This is a real tool built for a real use case, and every improvement matters.

Read this before opening a PR. It's short.

---

## The One Rule That Overrides Everything

> **Phase 1 must be perfect before Phase 2 starts.**

If Phase 1 (activation, cursor smoothness, velocity click) isn't solid, no Phase 2 PR will be merged — no matter how good the feature is. This is a discipline decision, not a personal one. A beautiful drag gesture on top of a jittery cursor is worse than no drag gesture at all.

Check the current phase status in [`docs/BUILD_STATUS.md`](docs/BUILD_STATUS.md) before starting work.

---

## What You Can Contribute Right Now

| Area | What's Needed |
|---|---|
| `src/gestures/config.py` | Tuned threshold constants from real-world testing |
| `src/tracking/smoothing.py` | Better smoothing approaches (One-Euro filter, Kalman) |
| `tests/fixtures/` | Recorded landmark sequences for gesture testing |
| `benchmarks/` | Latency and FPS measurements on different hardware |
| `docs/` | Clearer setup instructions, DroidCam guides |

---

## Setup (Local Dev)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/aircontrol.git
cd aircontrol

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run in dev mode (camera preview + debug overlay)
python -m src --dev
```

---

## Rules for PRs

### ✅ Do
- Keep gesture thresholds as **named constants** in `src/gestures/config.py` — never inline magic numbers
- Write tests for any gesture classifier change — tests must pass without a live camera
- Run the relevant benchmark after your change and include results in the PR description
- Keep `gestures/` (perception), `state_machine/` (decision), and `actions/` (effect) as **strictly separate layers** — don't cross them
- Comment *why*, not *what* — the code says what; the comment should explain the reasoning

### ❌ Don't
- Add Phase 2 features while Phase 1 is still being perfected
- Use pixel-space thresholds for gesture detection — always use 3D world landmarks (meters)
- Use `pyautogui.moveTo()` for cursor movement — use `pynput` (no forced delays)
- Add `autopy` as a dependency — broken on Python 3.9+
- Submit AI-generated code you haven't actually read and understood

---

## Branching Convention

```
main              ← stable, always works
dev               ← active development, may be broken
feature/xxx       ← your feature branch, branch off dev
fix/xxx           ← bug fix branch
```

All PRs go to `dev`. `dev` → `main` only when a full phase is complete and tested.

---

## Commit Messages

```
type: short description (max 72 chars)

Optional longer explanation.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Examples:
```
feat: add multi-frame debounce to velocity click detector
fix: cursor drift when hand partially leaves frame
test: add fixture sequences for fist gesture detection
docs: add DroidCam camera index setup instructions
```

---

## Opening an Issue

Use the issue templates in `.github/ISSUE_TEMPLATE/`. They're short. Fill them out.

For **false click / misclick reports**: include the `CLICK_VELOCITY_THRESHOLD` value from your `config.py` and approximate camera distance. This is the most important tuning variable.

---

## Questions?

Open a discussion — not an issue. Issues are for bugs and concrete feature requests.

---

*The best contribution is a real-world test with messy hands and a plate of food nearby.*
