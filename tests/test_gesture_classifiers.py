"""
Unit tests for GestureClassifier and PostureHoldDetector.
Runs completely offline using mock 3D landmarks.
"""

from types import SimpleNamespace
import pytest
from src.gestures.classifier import GestureClassifier, GestureType, PostureHoldDetector


def create_mock_hand(finger_extension: dict) -> list:
    """
    Generate synthetic 3D landmarks in meters.
    wrist at (0,0,0).
    finger_extension: dict with keys 'thumb', 'index', 'middle', 'ring', 'pinky' (bool)
    """
    landmarks = [SimpleNamespace(x=0.0, y=0.0, z=0.0) for _ in range(21)]

    # Set MCP positions around wrist
    landmarks[5] = SimpleNamespace(x=0.02, y=0.08, z=0.0)    # index MCP
    landmarks[9] = SimpleNamespace(x=0.0, y=0.085, z=0.0)    # middle MCP
    landmarks[13] = SimpleNamespace(x=-0.02, y=0.08, z=0.0)  # ring MCP
    landmarks[17] = SimpleNamespace(x=-0.04, y=0.07, z=0.0)  # pinky MCP

    # Fingers configuration: (tip_i, pip_i, mcp_i)
    fingers = {
        "index": (8, 6, 5),
        "middle": (12, 10, 9),
        "ring": (16, 14, 13),
        "pinky": (20, 18, 17),
    }

    for name, (tip_i, pip_i, mcp_i) in fingers.items():
        mcp = landmarks[mcp_i]
        if finger_extension.get(name, False):
            # Extended straight up
            landmarks[pip_i] = SimpleNamespace(x=mcp.x, y=mcp.y + 0.04, z=0.0)
            landmarks[tip_i] = SimpleNamespace(x=mcp.x, y=mcp.y + 0.08, z=0.0)
        else:
            # Curled into palm
            landmarks[pip_i] = SimpleNamespace(x=mcp.x, y=mcp.y + 0.02, z=-0.02)
            landmarks[tip_i] = SimpleNamespace(x=mcp.x, y=mcp.y - 0.01, z=-0.02)

    # Thumb
    if finger_extension.get("thumb", False):
        landmarks[4] = SimpleNamespace(x=0.08, y=0.04, z=0.0)   # open wide
    else:
        landmarks[4] = SimpleNamespace(x=0.01, y=0.04, z=-0.01) # tucked

    return landmarks


class TestGestureClassifier:
    @pytest.fixture
    def classifier(self):
        return GestureClassifier()

    def test_open_palm_detection(self, classifier):
        hand = create_mock_hand({"thumb": True, "index": True, "middle": True, "ring": True, "pinky": True})
        res = classifier.classify(hand)
        assert res.label == GestureType.OPEN_PALM
        assert res.confidence >= 0.85

    def test_fist_detection(self, classifier):
        hand = create_mock_hand({"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False})
        res = classifier.classify(hand)
        assert res.label == GestureType.FIST
        assert res.confidence >= 0.90

    def test_pointing_detection(self, classifier):
        hand = create_mock_hand({"thumb": False, "index": True, "middle": False, "ring": False, "pinky": False})
        res = classifier.classify(hand)
        assert res.label == GestureType.POINTING
        assert res.confidence >= 0.90


class TestPostureHoldDetector:
    def test_hold_progress_and_trigger(self):
        detector = PostureHoldDetector(GestureType.OPEN_PALM, required_seconds=0.5)

        # Start hold
        trig, el = detector.update(GestureType.OPEN_PALM, timestamp=10.0)
        assert not trig
        assert el == 0.0
        assert detector.progress(timestamp=10.0) == 0.0

        # Halfway
        trig, el = detector.update(GestureType.OPEN_PALM, timestamp=10.25)
        assert not trig
        assert abs(el - 0.25) < 1e-4
        assert abs(detector.progress(timestamp=10.25) - 0.5) < 1e-4

        # Complete threshold reached
        trig, el = detector.update(GestureType.OPEN_PALM, timestamp=10.51)
        assert trig
        assert detector.progress(timestamp=10.51) == 1.0

    def test_hold_interrupted_resets(self):
        detector = PostureHoldDetector(GestureType.OPEN_PALM, required_seconds=0.5)
        detector.update(GestureType.OPEN_PALM, timestamp=10.0)
        detector.update(GestureType.OPEN_PALM, timestamp=10.4)  # 0.4s elapsed

        # Posture drops
        trig, el = detector.update(GestureType.UNKNOWN, timestamp=10.45)
        assert not trig
        assert el == 0.0
        assert detector.progress(timestamp=10.45) == 0.0
