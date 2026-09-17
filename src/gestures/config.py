"""
Veyro — Central Configuration
==============================
Every tunable constant lives here. Never use magic numbers inline.
Tweak these values during testing. Do not commit personal overrides —
create a config_local.py (gitignored) that imports and overrides these.

Confirmed working environment:
  Python  : 3.13
  OpenCV  : 5.0.0
  MediaPipe: 1.0.1
  Camera  : DroidCam at index 1, 1280x720
"""

# ──────────────────────────────────────────────
# CAMERA
# ──────────────────────────────────────────────

# OpenCV device index. DroidCam is at index 0 (MSMF).
CAMERA_INDEX: int = 0

# Capture resolution (DroidCam default is 640x480 or HD 1280x720)
CAMERA_WIDTH: int = 640
CAMERA_HEIGHT: int = 480

# Use DirectShow backend on Windows (set False for DroidCam which uses MSMF)
USE_DSHOW: bool = False

# ──────────────────────────────────────────────
# MEDIAPIPE
# ──────────────────────────────────────────────

# Path to the downloaded HandLandmarker model file
# Download via: python -m src.tracking.download_model
MEDIAPIPE_MODEL_PATH: str = "models/hand_landmarker.task"

# Max hands to track (1 = lower CPU, faster, sufficient for MVP)
MAX_NUM_HANDS: int = 1

# Minimum detection confidence to accept a hand detection
MIN_DETECTION_CONFIDENCE: float = 0.7

# Minimum tracking confidence to keep tracking (vs re-detect)
MIN_TRACKING_CONFIDENCE: float = 0.6

# ──────────────────────────────────────────────
# SMOOTHING (Cursor Jitter Elimination & Butter-Smooth Tracking)
# ──────────────────────────────────────────────

# One-Euro Filter Parameters:
# Lower MIN_CUTOFF = heavier smoothing when stationary (eradicates hand tremor).
ONE_EURO_MIN_CUTOFF: float = 0.4

# BETA: Velocity coefficient. Higher = zero lag during fast movement.
ONE_EURO_BETA: float = 0.025

# D_CUTOFF (Hz): Cutoff frequency for velocity derivative calculation.
ONE_EURO_D_CUTOFF: float = 1.0

# Stationary Deadzone (in screen pixels):
# Micro-movements within this radius (14px) are completely filtered out,
# ensuring the cursor stays rock-solid when holding still on an icon.
SMOOTH_DEADZONE_PIXELS: float = 14.0

# Smooth transition factor when hand first appears (prevents jumping)
SMOOTH_EASE_IN_RATE: float = 0.25

# ──────────────────────────────────────────────
# SCREEN MAPPING
# ──────────────────────────────────────────────

# Reduction border (pixels) — only the inner crop of the camera frame
# maps to the full screen. Reduces edge jitter, amplifies perceived range.
# e.g. frameR=150 on 1280px → active zone is [150, 1130] → maps to [0, screenW]
FRAME_REDUCTION_X: int = 150
FRAME_REDUCTION_Y: int = 100

# ──────────────────────────────────────────────
# GESTURE DETECTION (3D world landmarks, meters)
# ──────────────────────────────────────────────

# Pinch threshold (meters, world space): thumb tip ↔ index PIP joint.
# Below = click engaged. Above PINCH_RELEASE = click released (hysteresis).
PINCH_ENGAGE_DIST: float = 0.04   # ~4cm physical
PINCH_RELEASE_DIST: float = 0.06  # ~6cm — wider to prevent flicker

# Palm detection: fraction of fingers that must be extended to count as "palm"
# 1.0 = all 4 fingers extended (index, middle, ring, pinky)
PALM_FINGER_RATIO: float = 1.0

# Fist detection: fraction of fingers that must be curled to count as "fist"
FIST_FINGER_RATIO: float = 1.0

# Cursor freeze: index tip ↔ middle tip distance (meters) below which
# the cursor is locked in place ("parking brake" gesture)
FREEZE_DIST: float = 0.03  # ~3cm

# ──────────────────────────────────────────────
# VELOCITY CLICK ("the snake bite")
# ──────────────────────────────────────────────

# Minimum speed (normalized units/frame) of index fingertip to qualify
# as the start of a jab. Below this = normal cursor movement.
CLICK_VELOCITY_THRESHOLD: float = 0.04

# Number of frames to check for deceleration AFTER the speed spike.
# The jab must be followed by slowing down (not sustained movement).
CLICK_DECEL_FRAMES: int = 4

# Minimum frames between two consecutive clicks (debounce).
# At 30fps, 15 frames = 0.5s minimum between clicks.
CLICK_COOLDOWN_FRAMES: int = 15

# ──────────────────────────────────────────────
# STATE MACHINE TIMING
# ──────────────────────────────────────────────

# Frames a gesture must be consistently detected before triggering a
# state transition. Prevents single-frame misreads from firing actions.
DEBOUNCE_FRAMES: int = 8

# Seconds the palm must be held to ARM the system (SUMMONED → ARMED)
PALM_HOLD_SECONDS: float = 2.0

# Seconds the fist must be held to DISARM (ARMED → IDLE)
FIST_HOLD_SECONDS: float = 3.0

# Seconds with no recognized gesture before auto-disarm (safety timeout)
AUTO_DISARM_TIMEOUT: float = 10.0

# Seconds after summoning with no arm gesture before returning to tray
SUMMON_TIMEOUT: float = 8.0

# ──────────────────────────────────────────────
# HOTKEY
# ──────────────────────────────────────────────

# Duration (seconds) Caps Lock must be held to summon/dismiss Veyro.
# Long press prevents accidental triggers.
HOTKEY_HOLD_SECONDS: float = 1.0

# ──────────────────────────────────────────────
# DEV / DEBUG MODE
# ──────────────────────────────────────────────

# Set to True via --dev flag at launch. Shows camera preview + debug overlay.
# Never True in production.
DEV_MODE: bool = False

# Show landmark skeleton on the camera preview in dev mode
DEV_SHOW_LANDMARKS: bool = True

# Show gesture label + confidence on dev preview
DEV_SHOW_GESTURE_LABEL: bool = True

# Show velocity meter on dev preview (for click tuning)
DEV_SHOW_VELOCITY: bool = True
