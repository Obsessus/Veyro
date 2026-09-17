<div align="center">

# ✋ Veyro

### Gesture-controlled mouse — summoned in a second, gone when you're done.

*A privacy-first, hotkey-triggered hand tracking overlay for when your hands can't touch a keyboard.*

---

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## The Problem

You're eating. Your hands are oily. A YouTube ad starts playing.

You can't touch your keyboard. You can't touch your mouse. You just want to hit **Skip**.

That's it. That's the entire product.

---

## The Solution — In 5 Seconds

```
[Hold Caps Lock — 1 second]
        ↓
Translucent overlay appears. Camera activates.
        ↓
Show open palm → system arms itself
        ↓
Point index finger → cursor follows
Jab forward fast → click (skip that ad)
        ↓
Make a fist → overlay disappears, camera off
```

Veyro is **not** a mouse replacement. It's a temporary override — you summon it, do one thing, dismiss it. Then it's completely gone. No camera running in the background. No CPU usage. Nothing.

---

## Why This Is Different From Every Other Gesture Mouse

| Every other gesture mouse project | Veyro |
|---|---|
| Always-on — camera runs the entire session | **Camera is OFF until you summon it** |
| Acts on any hand movement it sees | **Three-stage gate: Hotkey → Palm → Gesture** |
| Built to replace the mouse entirely | **Built for a single moment: oily hands** |
| 2D landmark tracking (breaks at angles) | **Full 3D world landmarks (meters, scale-invariant)** |
| Click = pinch (hard with wet/oily hands) | **Click = fast index finger jab (no pinch needed)** |
| Feature-complete on day one, nothing works well | **Phase 1 perfected before Phase 2 starts** |

---

## How It Works — The Full Interaction Model

### State Machine

```
┌─────────────────────────────────────────────────────┐
│  TRAY (default)                                     │
│  • System tray icon only                            │
│  • Zero camera usage                                │
│  • Only hotkey listener active (~0% CPU)            │
└──────────────────┬──────────────────────────────────┘
                   │  Hold Caps Lock (1 second)
                   ▼
┌─────────────────────────────────────────────────────┐
│  SUMMONED                                           │
│  • Camera activates instantly                       │
│  • Translucent overlay appears                      │
│  • Watching — but NOT yet acting on gestures        │
│  • Waiting for the ARM gesture                      │
└──────────────────┬──────────────────────────────────┘
                   │  Open palm, held ~0.5s
                   ▼
┌─────────────────────────────────────────────────────┐
│  ARMED                                              │
│  • Index finger → cursor follows in real time       │
│  • Fast index jab forward → left click              │
│  • [Phase 2 gestures available here]                │
└──────────────────┬──────────────────────────────────┘
                   │  Fist held 0.5s
                   │  OR  Caps Lock again
                   │  OR  No gesture for N seconds
                   ▼
┌─────────────────────────────────────────────────────┐
│  TRAY (back to default)                             │
│  • Camera closes completely                         │
│  • Overlay disappears                               │
│  • Zero CPU, zero camera                            │
└─────────────────────────────────────────────────────┘
```

### Why Three Stages?
The Hotkey → Palm → Gesture sequence is intentional. Each stage is a deliberate signal:
- **Hotkey** = "I want gesture control right now"
- **Palm** = "I am intentionally giving commands" — prevents accidental activation
- **Gesture** = the actual command

No other open-source gesture mouse implements this full three-stage model.

---

## Gesture Vocabulary

### Phase 1 — MVP (Must Be Perfect Before Anything Else)

| Gesture | How It Works | Action |
|---|---|---|
| Open palm, held 0.5s | All fingers extended, facing camera | **Arm the system** |
| Index finger up | Index extended, others curled | **Cursor follows fingertip** |
| Fast index jab forward | Velocity spike on index tip + deceleration | **Left click** |
| Fist, held 0.5s | All fingers curled | **Disarm / dismiss** |

### Phase 2 — Extensions (After Phase 1 Is Flawless)

| Gesture | Action |
|---|---|
| Index + middle up, vertical movement | Scroll |
| Pinch + move | Drag and drop |
| Fast lateral hand swipe | Tab switch / media skip |
| Thumb + middle pinch | Right click |

### Phase 3 — Future

| Feature | Notes |
|---|---|
| Voice commands | Hybrid: gesture for cursor, voice for action |
| Copy / paste gestures | To be designed based on Phase 1/2 learnings |
| Additional gestures | Driven by real usage data, not speculation |

---

## The Click — "The Snake Bite"

Every existing gesture mouse uses one of:
- **Pinch** (thumb + index distance) — hard with oily/wet hands
- **Dwell** (hold still for 0.8s) — too slow for "skip ad" scenarios
- **Two-finger tap** — unintuitive

Veyro uses **velocity-based click detection** — not found in any reference implementation:

```
Track index fingertip position every frame
         ↓
Measure frame-to-frame velocity
         ↓
Detect: fast forward spike → then rapid deceleration
         ↓
That pattern = intentional jab = LEFT CLICK
         ↓
Debounce: minimum N frames before next click
```

Why this works: When you want to click something, you instinctively jab your finger toward it. That's the natural human motion. The snap-forward-then-stop is exactly what the system looks for.

---

## Why 3D Detection

Standard gesture mice use 2D landmark tracking. 2D cannot tell the difference between:
- A finger **pointing forward** (toward camera)
- A finger **pointing sideways**
- A finger **curling toward the camera**

These look identical in 2D. The detector gets confused constantly.

Veyro uses MediaPipe's `hand_world_landmarks` — **3D coordinates in meters, wrist-relative**:
- Full X, Y, Z information
- Scale-invariant (same values at 30cm or 80cm from camera)
- Every gesture threshold computed in 3D world space
- Never in pixels, never in 2D

This is the same approach used by the most production-ready open-source gesture mouse (Lumina Air Mouse), and it's the only approach that works reliably in real, messy, non-studio conditions.

---

## Privacy

> The camera is **never on** unless you pressed the hotkey in the last few seconds.

- Default state: system tray icon, zero camera usage
- Camera activates only on hotkey press
- Camera closes completely when dismissed — not paused, not minimized, **closed**
- No network calls. Everything runs locally. No data leaves your machine. Ever.

---

## Hotkey Design

The hotkey needs to be pressable with **oily hands** — no precise finger placement. That means:

- ✅ **Single large key** — pressable with a knuckle, wrist, or side of hand
- ❌ Two-key combos (`Ctrl+Space`) — require two precise finger placements

**Default: Hold `Caps Lock` for 1 second**

- Largest easily-reachable key on most keyboards
- Long-press prevents accidental triggers
- Pressable with literally any part of your hand
- User-configurable — change to any key in settings

---

## Tech Stack

| Tool | Role | Why |
|---|---|---|
| **MediaPipe Tasks API** (`HandLandmarker`) | 3D hand landmark detection | Modern API, provides `hand_world_landmarks` in meters. Pretrained, real-time on CPU. |
| **OpenCV** | Camera capture | `cv2.CAP_DSHOW` for low-latency Windows capture. Works identically with DroidCam / IP Webcam virtual devices. |
| **pynput** | Cursor movement + global hotkey | No forced delays, native mouse rate, global keyboard listener works without window focus |
| **pyautogui** | Discrete actions (scroll, click shortcuts) | Simpler API for one-shot events |
| **Adaptive EMA smoother** | Cursor jitter elimination | Velocity-weighted: heavy smoothing when still (precision), light when fast (responsiveness) |
| **pytest** | Testing state machine + gesture classifiers | Must run without a live camera |
| **PyQt / Tkinter** | Translucent overlay UI | Built last, after core gesture engine works headlessly |

**Explicitly not used:**
- Custom CNN / model training — MediaPipe already solves this
- Cloud APIs — must run 100% locally, real-time
- `autopy` — broken on Python 3.9+
- `pyautogui` for cursor movement — has forced 0.1s pause per move

---

## Repository Structure

```
Veyro/
├── src/
│   ├── capture/
│   │   └── camera.py              # OpenCV capture abstraction (webcam or DroidCam identical)
│   ├── tracking/
│   │   ├── mediapipe_tracker.py   # MediaPipe Tasks API wrapper, 3D landmark extraction
│   │   └── smoothing.py           # Adaptive velocity-based EMA filter
│   ├── gestures/
│   │   ├── classifier.py          # Bitmask encoder → (gesture_label, confidence)
│   │   ├── velocity.py            # Velocity-based click detector ("the snake bite")
│   │   └── config.py              # ALL thresholds as named constants — never magic numbers
│   ├── state_machine/
│   │   ├── states.py              # SystemState enum: TRAY / SUMMONED / ARMED / sub-states
│   │   ├── machine.py             # Transition logic, debounce, hysteresis, timeout disarm
│   │   └── debounce.py            # Multi-frame counter — prevents single-frame false triggers
│   ├── actions/
│   │   ├── mouse.py               # pynput mouse controller wrapper
│   │   └── keyboard.py            # Keyboard shortcuts (tab switch, media, etc.)
│   ├── hotkey/
│   │   └── listener.py            # Global pynput keyboard listener (works without focus)
│   └── overlay/
│       └── hud.py                 # Translucent status overlay (built last)
├── docs/
│   └── reference_repo_analysis.md # Phase 0: analysis of 7 reference repos
├── tests/
│   ├── test_gesture_classifiers.py
│   ├── test_velocity_click.py     # Tests for the snake bite click detector
│   ├── test_state_machine.py      # Mocked gesture events — no camera needed
│   └── fixtures/
│       └── landmark_sequences/    # Recorded gesture sequences for offline testing
├── benchmarks/
│   └── latency_report.md          # Real measured FPS + end-to-end latency numbers
├── requirements.txt
└── README.md
```

**Why this structure?**
`gestures/` (perception), `state_machine/` (decision), and `actions/` (effect) are strictly separate. This means:
1. The state machine can be unit-tested with zero camera using mocked gesture events
2. Gesture classifiers can be tested against recorded landmark sequences
3. Each layer can be tuned independently without touching the others

---

## Build Order

No phase starts before the previous one works reliably. No exceptions.

| Phase | Task | Done When |
|---|---|---|
| **0** | Reference repo analysis (`docs/reference_repo_analysis.md`) | Informed at least one concrete design decision |
| **1** | Camera + 3D tracking pipeline | MediaPipe landmarks visible in dev window, stable |
| **2** | Gesture classifiers | All Phase 1 gestures return correct label + confidence on recorded fixtures |
| **3** | State machine | All transitions work with mocked events — no camera needed |
| **4** | Adaptive smoothing + cursor control | Cursor feels like a real mouse — no jitter, no lag |
| **5** | Velocity click detector | Zero misclicks, zero missed intentional clicks in 10-minute test |
| **6** | Hotkey listener + tray process | Activates without window focus, camera off when idle |
| **7** | End-to-end MVP | Full loop works live in the actual use case (eating, ad playing) |
| **8** | Benchmarking | Real latency + FPS numbers documented |
| **9** | Translucent overlay | Gemini-style appearance/disappearance |
| **10** | Phase 2 gestures | Scroll, drag, tab switch — only after MVP is daily-use reliable |

---

## What Is Not Being Built

| Not building | Why |
|---|---|
| Always-on gesture control | Camera privacy + accidental input. The whole point is it's summoned, not always watching. |
| Mouse replacement | The use case is 10–30 second bursts, not full desktop navigation. |
| Custom hand detection model | MediaPipe is pretrained, real-time, and CPU-friendly. Reinventing it wastes project time. |
| Cloud/API gesture processing | Network latency per frame kills real-time. Runs 100% locally. |
| Camera preview in production | Interrupts whatever the user is watching. Dev mode has it, production does not. |
| Feature bloat in Phase 1 | A beautiful drag gesture on top of a jittery cursor is worse than a smooth cursor alone. |

---

## Reference Repos Analyzed

Seven open-source gesture mouse projects were studied before any design decisions were made:

| Repo | What We Learned From It |
|---|---|
| `Capslockb/tony-stark-hand-control` | `frame_reduction` + `np.interp` coordinate remapping — effective and simple |
| `Rcidshacker/airmouse` (Lumina) | Adaptive velocity smoothing, world landmarks for scale invariance, dwell click with visual arc |
| `4shil/kinemouse` | Named state machine, edge-triggered events, centralized config constants |
| `takeyamayuki/NonMouse` ⭐ | Global hotkey listener architecture, thumb-to-PIP-joint click, cursor freeze gesture |
| `happyananya/...` | Dual modality (hand + face), EAR-based blink detection |
| `GuhanAein/VirtualMouse` | Cleanest reference for `frameR` dead zone pattern |
| `Viral-Doshi/Gesture-Controlled-Virtual-Mouse` | Binary bitmask gesture encoding, signed distance, multi-frame debounce counter, dual-hand roles |

Full analysis: [`docs/reference_repo_analysis.md`](docs/reference_repo_analysis.md)

**Common gap across all seven:** None implement velocity-based click detection. None implement the full three-stage Hotkey → Palm → Gesture state machine. These are Veyro's original contributions.

---

## Camera Setup (DroidCam / IP Webcam)

Veyro treats DroidCam and IP Webcam as standard OpenCV video capture devices — no phone-specific code in the core logic.

**Setup:**
1. Install DroidCam on your phone and PC: [droidcam.app](https://www.droidcam.app)
2. Connect phone and PC on the same WiFi network
3. Open DroidCam on both — note the device index it appears as (usually `1` or `2`)
4. Set `CAMERA_INDEX` in `src/gestures/config.py` to that index
5. A regular webcam works identically — set `CAMERA_INDEX = 0`

---

## Known Limitations (Honest Assessment)

- **Single hand only** — multi-hand interaction is Phase 3
- **Absolute cursor mapping** — finger position maps 1:1 to screen region. Large displays require bigger arm movements. Relative (trackpad-style) mapping is a future improvement.
- **Lighting dependent** — MediaPipe degrades in very poor or strongly backlit conditions. A front-facing light source helps.
- **Windows-optimized** — `cv2.CAP_DSHOW` and tray app behavior are Windows-specific. macOS/Linux support is not a current goal.
- **Velocity click needs personal tuning** — the `CLICK_VELOCITY_THRESHOLD` constant in `config.py` may need adjustment based on individual hand speed. A first-launch calibration wizard is a future feature.
- **Alt key conflict (from NonMouse learnings)** — we use Caps Lock not Alt specifically to avoid this

---

## Contributing

This is an open-source project. If you want to contribute:

1. **Phase 1 is sacred** — don't submit Phase 2 features before Phase 1 is demonstrably solid
2. All gesture thresholds must be named constants in `config.py` — no magic numbers inline
3. Gesture classifiers must be testable without a camera (use fixture landmark sequences)
4. Every PR needs a note on which benchmark was run and what the result was

---

## License

MIT — do whatever you want with it. If you build something cool on top of it, a shoutout is appreciated but not required.

---

<div align="center">

*Built because sometimes your hands are just greasy.*

</div>
