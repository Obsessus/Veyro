# Build Status

This document tracks the current phase and what's done / in progress / not started.
Update this every time a phase is completed.

---

## Current Phase: 1b — Cursor Control & Adaptive Smoothing

| Phase | Name | Status |
|---|---|---|
| 0 | Project setup & reference repo analysis | ✅ Complete |
| 1a | Camera + 3D tracking pipeline | ✅ Complete |
| 1b | Adaptive smoothing + cursor control | 🟡 In Testing |
| 1c | Velocity click detector ("snake bite") | ⬜ Not Started |
| 1d | State machine (TRAY → SUMMONED → ARMED) | ⬜ Not Started |
| 1e | Hotkey listener + tray process | ⬜ Not Started |
| 1f | End-to-end MVP (full loop works live) | ⬜ Not Started |
| 2a | Scroll gesture | ⬜ Not Started |
| 2b | Drag and drop | ⬜ Not Started |
| 2c | Tab switch / media skip | ⬜ Not Started |
| 2d | Right click | ⬜ Not Started |
| 3 | Translucent overlay UI | ⬜ Not Started |
| 4 | Benchmarking (latency + FPS report) | ⬜ Not Started |
| 5 | Voice commands | ⬜ Not Started |

---

## Phase Gate Rule

**No phase begins before the previous phase works reliably in real daily use.**

"Reliably" means: tested by a real person, with oily/messy hands, in the actual use case (eating, ad playing), for at least one week without regressions.

---

## Latest Benchmark
*Not yet measured — Phase 1 not complete.*

| Metric | Target | Measured |
|---|---|---|
| End-to-end latency (frame → action) | < 100ms | — |
| Sustained FPS | ≥ 25fps | — |
| False click rate (10 min session) | 0 | — |
| Missed intentional click rate | < 5% | — |
