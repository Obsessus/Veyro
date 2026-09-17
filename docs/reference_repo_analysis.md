# Comparative Analysis of Reference Gesture-Controlled Virtual Mouse Repositories

**Project:** Veyro  
**Author:** Obsessus & Contributors  
**Status:** Phase 0 Completed Analysis  
**Date:** September 2026  

---

## Executive Summary

Before implementing **Veyro**, we conducted a thorough code-level architectural analysis of existing open-source gesture-controlled mouse implementations across 12 distinct repositories. 

The universal findings across nearly all existing repositories:
1. **Always-On Trap:** Almost 100% of open-source implementations run an un-gated, continuous loop where every hand movement in frame manipulates the system pointer. This makes concurrent activities (e.g. eating, typing, gesturing casually) practically impossible.
2. **2D Landmark Vulnerability:** Most rely on 2D normalized screen-space landmarks, making pinch and posture thresholds scale-variant and sensitive to camera distance and hand orientation.
3. **Crude Smoothing or Jitter:** Most repos use fixed-parameter Exponential Moving Averages (EMA), forcing a painful tradeoff between sluggish lag and cursor jitter.
4. **Pinch/Dwell Click Flaws:** Discrete actions rely either on pinching (which causes cursor drift at release and is awkward with wet/oily hands) or dwell timers (which introduce 0.8s+ delays incompatible with quickly skipping ads or closing windows).

**Veyro's Innovation:**
- A strict **three-stage state machine**: `IDLE/TRAY` → `SUMMONED` (via accessible hotkey) → `ARMED` (via held open palm) → `DISARMED`.
- **Velocity-based forward jab ("snake bite") click detection** using 3D world landmark trajectory without requiring finger pinch.
- **Adaptive velocity-weighted smoothing** yielding responsive fast moves and rock-solid stationary targeting.
- Separation of concerns: **perception**, **decision**, and **actuation** decoupled for 100% headless unit testability.

---

## Part 1: Initial Spec Reference Repositories

### 1. `maanjk/hand-gesture-virtual-mouse`
- **Gestures & Implementation:** Tracks index fingertip (landmark 8) for cursor movement; distance between index tip (8) and thumb tip (4) for left click; middle (12) + thumb (4) for right click. Uses `np.interp` to scale camera frame to screen resolution.
- **Strongest Part:** Straightforward implementation of screen interpolation and basic thresholding.
- **Weakest Part:** Fixed Euclidean pixel distance thresholds; severe jitter near boundaries; always active when hand is visible.
- **What Veyro Borrows / Does Differently:** We discard pixel-space thresholds in favor of 3D world landmarks (`hand_world_landmarks` in meters) to achieve camera distance invariance.

### 2. `Ghorbel37/hand-gesture-control-suite`
- **Gestures & Implementation:** Multi-mode control suite (mouse, volume, slide presentations). Mode switching via specific finger counts.
- **Strongest Part:** Broad feature ambition and clean separation of modes via finger configurations.
- **Weakest Part:** Mode confusion; finger counting using 2D y-coordinates (`tip.y < pip.y`) fails when hand is tilted or angled toward the camera.
- **What Veyro Borrows / Does Differently:** We avoid mode complexity in Phase 1 and use directional vectors in 3D rather than naive 2D y-coordinate comparisons.

### 3. `VASANI007/AI-Gesture-Control-System`
- **Gestures & Implementation:** Uses OpenCV and MediaPipe Hands; controls volume with thumb-index distance and mouse with index tip.
- **Strongest Part:** Visual feedback drawing directly on OpenCV frames.
- **Weakest Part:** Monolithic script; heavy dependency on PyAutoGUI with default pause parameters introducing perceptible cursor latency (~100ms).
- **What Veyro Borrows / Does Differently:** We use `pynput` for native non-blocking mouse events and keep UI/HUD strictly detached from core tracking.

### 4. `sintucoder/virtual_mouse`
- **Gestures & Implementation:** Minimal baseline script mapping landmark 8 to cursor position; pinch for click.
- **Strongest Part:** Highly readable, minimal boilerplate.
- **Weakest Part:** No debounce, no hysteresis, zero protection against false triggers.
- **What Veyro Borrows / Does Differently:** We enforce rolling window debouncing and hysteresis gates on all state transitions.

### 5. `DEVRAJ-20/AI-Virtual-Mouse`
- **Gestures & Implementation:** Frame reduction margin (`frameR`) to allow reaching screen corners without extreme hand displacement. Basic moving average smoothing.
- **Strongest Part:** Frame margin technique (`frameR`) creates an effective active workspace inside the camera frame.
- **Weakest Part:** Cursor oscillation when holding hand stationary; no arm/disarm mechanism.
- **What Veyro Borrows / Does Differently:** We adopt the `frameR` boundary concept in `config.py` (`FRAME_REDUCTION_X`, `FRAME_REDUCTION_Y`), but replace the simple moving average with velocity-adaptive smoothing.

---

## Part 2: Deep Dive into Extended Open-Source Implementations

### 6. `takeyamayuki/NonMouse` (Key Inspiration for Hotkey Integration)
- **Gestures & Implementation:** Index tip for cursor; thumb touching index PIP joint (landmark 6, not tip 8) for left click; 1.5s dwell for right click; index+middle tips touching for cursor freeze.
- **Armed Mechanism:** Hold `Alt` (Windows) or `Cmd` (macOS) via global `pynput.keyboard.Listener`. System only tracks while the modifier key is held down.
- **Strongest Part:** 
  1. Decoupling cursor landmark (tip 8) from click landmark (PIP 6) so clicking does not displace cursor.
  2. Cursor freeze ("parking brake") when index and middle tips touch.
  3. Global keyboard listener architecture.
- **Weakest Part:** Requiring the user to *continually hold* a key defeats touchless operation when hands are soiled; Alt key triggers Windows menu bars.
- **Veyro Decision:** We adopt the global `pynput` keyboard listener architecture, but use a **single toggle press** (Caps Lock long-press) rather than a continuous hold, and pair it with an **open palm arming gesture**. We also adopt the cursor freeze and PIP click concepts as backup/precision tools.

### 7. `Kisses99/airmouse` (Lumina Air Mouse — Production Reference)
- **Gestures & Implementation:** MediaPipe Tasks API (`HandLandmarker`); 3D world landmarks; dwell click (0.8s hover); pinch-drag; fist right-drag; scroll via two fingers.
- **Strongest Part:** 
  1. Scale-invariant 3D world coordinates (`hand_world_landmarks` in physical meters).
  2. Velocity-adaptive smoothing: lerp between `MIN_ALPHA` and `MAX_ALPHA` based on hand speed.
  3. DirectShow (`cv2.CAP_DSHOW`) Windows camera optimization.
- **Weakest Part:** Dwell-only clicking is painfully slow (0.8s per click) for quick actions like clicking "Skip Ad".
- **Veyro Decision:** Adopt world landmarks in meters, DirectShow backend, and the adaptive velocity smoothing algorithm. Replace the slow dwell click with our rapid velocity jab ("snake bite").

### 8. `Viral-Doshi/Gesture-Controlled-Virtual-Mouse`
- **Gestures & Implementation:** Bitmask finger encoding (4 bits representing index, middle, ring, pinky extension); multi-frame debounce counter; dual-hand roles (major hand cursor, minor hand scroll).
- **Strongest Part:** Binary bitmask state encoding (`self.finger |= 1 << (3 - idx)`) and multi-frame `cnt` debounce counter.
- **Weakest Part:** Dependent on obsolete `autopy` (incompatible with Python 3.9+).
- **Veyro Decision:** We adopt the binary bitmask gesture representation for clean O(1) state resolution and the multi-frame debounce counter pattern.

### 9. `4shil/kinemouse`
- **Gestures & Implementation:** Named state machine (`IDLE`, `PINCH_1`, `DRAG`); centralized `config.py`.
- **Strongest Part:** Modular architecture separating capture, gesture classification, and mouse actions.
- **Weakest Part:** Always-on execution loop; absolute cursor mapping without relative gain adjustments.
- **Veyro Decision:** Enforce strict modular separation between perception, decision, and action layers.

---

## Architectural Decision Matrix

| Architectural Problem | Flawed Approach in Prior Repos | Veyro Engineering Solution | Borrowed / Inspired By |
|---|---|---|---|
| Accidental Triggers | Always-on loop; immediate action on any frame | 3-stage gate: Hotkey Summon → Open Palm Arm → Gesture Actions → Fist/Timeout Dismiss | Original design + NonMouse listener |
| Scale / Distance Variation | Fixed pixel distance thresholds | MediaPipe `hand_world_landmarks` (3D meters, wrist-relative) | Lumina AirMouse |
| Pointer Jitter vs Lag | Fixed alpha EMA or naive moving average | Velocity-adaptive EMA (`alpha = lerp(min, max, speed / threshold)`) | Lumina AirMouse |
| Click Displacement | Pinching tip-to-tip moves the pointer at the moment of click | Velocity-spike forward jab ("snake bite") + optional thumb-to-PIP click | Original concept + NonMouse PIP trigger |
| Edge Reachability | Full 1:1 camera-to-screen mapping requires excessive reach | Bounded active inner zone (`FRAME_REDUCTION_X/Y`) with linear interpolation | DEVRAJ-20 & GuhanAein |
| Gesture Code Cleanliness | Nested chains of `if/elif/else` coordinate checks | Binary bitmask encoding (`0b1000 = index`, `0b1111 = palm`, etc.) | Viral-Doshi |
| OS Latency | `pyautogui.moveTo()` with forced internal sleep delays | `pynput.mouse.Controller` direct event dispatch | NonMouse / pynput |

---

## Phase 0 Sign-Off

The comparative research conducted above directly dictates the architecture and parameter set codified in `src/gestures/config.py`, `src/tracking/mediapipe_tracker.py`, and `src/tracking/smoothing.py`. Phase 0 is complete.
