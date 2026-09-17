# Veyro — Finalized Product Vision
**Version:** 3.0 — Vision locked
**Updated:** 2026-09-17
**Status:** Vision confirmed. No code written yet.

---

## The One-Line Description

> A privacy-first, hotkey-summoned, 3D gesture overlay that gives you mouse control for 10–30 seconds when your hands can't touch a keyboard — then disappears completely.

---

## The Real Use Case (Never Forget This)

```
You're eating. Hands are oily.
A YouTube ad plays.
You can't touch your keyboard or mouse.
You press ONE hotkey.
A translucent overlay appears — like Gemini on Android.
You point your index finger.
Cursor follows it.
You jab forward (fast).
Click. Ad skipped.
You make a fist.
Overlay disappears. Camera off. Done.
Total time: ~5 seconds.
```

That is the product. Everything is designed to make that sequence as fast, reliable, and natural as possible.

---

## Non-Negotiable Product Rules

1. **Camera is NEVER on without explicit user action.** Privacy is non-negotiable.
2. **Basics must be perfect before adding features.** Zero tolerance for jitter, lag, or misclick in Phase 1.
3. **No camera preview window in production.** It interrupts whatever the user is watching/doing.
4. **Not a mouse replacement.** A temporary override. Get in, do the thing, get out.
5. **3D detection only.** 2D skeleton tracking is not reliable enough. All gesture thresholds use 3D world landmarks.

---

## System Lifecycle

```
┌─────────────────────────────────────────────────────┐
│  TRAY STATE (default)                               │
│  • Tray icon only                                   │
│  • ZERO camera usage                                │
│  • Only hotkey listener active (~0% CPU)            │
└──────────────────┬──────────────────────────────────┘
                   │ [Hotkey pressed]
                   ▼
┌─────────────────────────────────────────────────────┐
│  SUMMONED STATE                                     │
│  • Camera activates instantly                       │
│  • Translucent overlay appears (Gemini-style)       │
│  • System watching — NOT yet acting on gestures     │
│  • Waiting for ARM gesture                          │
└──────────────────┬──────────────────────────────────┘
                   │ [Arm gesture detected]
                   ▼
┌─────────────────────────────────────────────────────┐
│  ARMED STATE                                        │
│  • Gestures control the computer                   │
│  • Index finger → cursor follows                   │
│  • Fast jab → left click                           │
│  • [Other gestures — Phase 2]                      │
└──────────────────┬──────────────────────────────────┘
                   │ [Dismiss gesture] OR [Hotkey again]
                   │ OR [Timeout — no gesture N seconds]
                   ▼
┌─────────────────────────────────────────────────────┐
│  TRAY STATE (back to default)                       │
│  • Camera closes completely                         │
│  • Overlay disappears                               │
│  • Back to zero CPU, zero camera                   │
└─────────────────────────────────────────────────────┘
```

---

## 3D Detection — Why And How

### Why Not 2D
2D skeleton tracking cannot distinguish:
- Finger pointing **forward** (toward camera) vs. **sideways** vs. **curling toward camera**
- These all project to the same 2D shape — the detector gets confused

### What We Use
MediaPipe Tasks API provides `hand_world_landmarks` — 21 points in **3D world space**:
- Coordinates in **meters**
- **Wrist-relative** (wrist = origin)
- **Scale-invariant** — same values whether hand is 30cm or 80cm from camera
- Full X, Y, Z depth information

**Every gesture threshold is computed in 3D world space. Never in 2D pixels.**

This is what the production AirMouse (Kisses99) uses. It's the only approach that works reliably in real conditions.

---

## Phase 1 — The Foundation (Must Be Perfect)

These four things must work flawlessly before anything else is touched:

### 1. Activation / Deactivation
- Hotkey → system summons (TBD: `Ctrl+Space` or user-configured)
- Arm gesture → ARMED
- Dismiss gesture → back to tray
- Timeout (no gesture for N seconds) → auto-dismiss
- **Standard:** Zero false activations. Zero stuck states. Instant response.

### 2. 3D Cursor Control
- Index finger (landmark 8) position → cursor position
- Adaptive velocity smoothing:
  - Slow hand → heavy smoothing (precision)
  - Fast hand → light smoothing (responsiveness)
- Dead zone: micro-tremors below movement threshold are ignored
- Frame reduction: only inner zone of camera frame maps to screen (reduces edge jitter)
- **Standard:** Indistinguishable from a real mouse in smoothness. Zero jitter.

### 3. Index Finger Jab = Left Click ("The Snake Bite")
- Track velocity of index fingertip (landmark 8) frame-to-frame
- Click fires when: velocity spike detected + followed by deceleration
- NOT a pinch. NOT a dwell. A fast forward jab, then stop.
- Debounced: minimum N frames between clicks
- **Standard:** Zero misclicks. Zero missed intentional clicks. Feels instant.

### 4. Deactivation
- Specific gesture (fist / palm push / TBD) OR hotkey again → immediate dismiss
- Camera closes. Overlay gone. System silent.
- **Standard:** Always works. No stuck armed states.

---

## Phase 2 — Extensions (After Phase 1 Is Perfect)

Only begin after Phase 1 is demonstrably reliable in real daily use.

| Feature | Gesture (tentative) |
|---|---|
| Scroll | Index + middle fingers up, vertical hand movement |
| Drag & drop | Pinch + move |
| Tab switch / skip | Fast lateral hand swipe |
| Right click | Thumb to middle finger pinch OR left-click dwell |
| Copy / paste | TBD — possibly voice or specific gesture combo |

---

## Phase 3 — Future (Much Later)

- Voice commands (hybrid: gesture for cursor, voice for commands)
- Additional gestures based on real usage patterns
- Multi-monitor support
- Mobile companion app (DroidCam / IP Webcam integration)

---

## UI Specification

### Production Mode (what the user sees)
- Translucent overlay — appears when summoned, disappears when dismissed
- Shows current state: ARMED indicator (small colored element)
- NO camera preview window
- Does NOT interrupt video, games, or any fullscreen content
- Inspired by: Gemini overlay on Android — "software has arrived, does its job, vanishes"

### Development Mode (what we see while building)
- Camera preview window ON
- Landmarks drawn on the hand (debug visualization)
- Gesture label + confidence score displayed
- Velocity meter for click detection tuning
- Toggled by `--dev` flag at launch

---

## Technical Decisions (Locked)

| Decision | Choice | Reason |
|---|---|---|
| Hand detection | MediaPipe Tasks API (`HandLandmarker`) | Modern API, provides 3D world landmarks |
| Gesture coordinates | `hand_world_landmarks` (3D meters) | Scale-invariant, works at any camera distance |
| Cursor coordinates | `hand_landmarks` (2D normalized) + adaptive smoothing | 2D is correct for screen mapping |
| Smoothing | Adaptive velocity-based EMA | Borrowed from AirMouse — best in class |
| Click detection | Velocity spike + deceleration (jab) | Novel, natural, works with oily hands |
| Mouse control | `pynput` | No forced delays, native rate |
| Hotkey listener | `pynput.keyboard.Listener` (global) | Works without window focus |
| Camera | `cv2.VideoCapture` + `cv2.CAP_DSHOW` (Windows) | Low latency |
| Camera state | OFF by default, ON only when summoned | Privacy |
| Background process | System tray (minimal) | Hotkey listener needs a process, not a full app |
| Gesture encoding | Bitmask (4 bits per finger state) | Clean, extensible |
| Debounce | Multi-frame counter | Prevents single-frame false triggers |

---

## All Design Decisions — Locked ✅

| Decision | Answer |
|---|---|
| **Hotkey** | User-configurable. Default: `Caps Lock long press 1s` — single large key, pressable with knuckle/wrist/side of hand when fingers are oily |
| **Why this hotkey** | Two-key combos need precise finger placement — wrong when hands are dirty. One big key you can hit with any part of your hand. |
| **Arm gesture** | Open palm facing camera, held ~0.5s |
| **Dismiss gesture** | Fist held ~0.5s, OR hotkey again, OR N-second timeout |
| **Click** | Index finger fast forward jab (velocity spike + deceleration) |
| **Camera** | OFF by default. ON only when summoned. Closes on dismiss. |
| **Overlay** | Translucent, Gemini-style. No camera preview in production. |

---

## What Specifically Does NOT Get Built (Ever, Unless Vision Changes)

- Custom CNN/model training — MediaPipe already solves hand detection
- Cloud/API calls for gesture processing — must be 100% local, real-time
- Always-on camera — privacy is non-negotiable
- Camera preview in production — interrupts user experience
- Feature bloat before Phase 1 is perfect — discipline is the product

---

*Vision is locked. Next: GitHub repository setup, then Phase 1 implementation planning.*
