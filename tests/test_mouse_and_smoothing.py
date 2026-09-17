"""
Unit tests for AdaptiveSmoother and MouseController (Phase 1b).
These tests run completely headlessly without requiring a camera or physical screen interaction.
"""

import pytest
from src.tracking.smoothing import AdaptiveSmoother
from src.actions.mouse import MouseController


class TestAdaptiveSmoother:
    def test_first_frame_initialization(self):
        smoother = AdaptiveSmoother()
        x, y = smoother.update(500.0, 300.0)
        assert x == 500.0
        assert y == 300.0

    def test_deadzone_suppresses_micro_jitter(self):
        smoother = AdaptiveSmoother()
        smoother.update(500.0, 300.0)

        # Small micro-movement below SMOOTH_DEADZONE
        x_micro, y_micro = smoother.update(500.0005, 300.0005)
        assert x_micro == 500.0
        assert y_micro == 300.0

    def test_adaptive_smoothing_gradual_convergence(self):
        smoother = AdaptiveSmoother()
        smoother.update(100.0, 100.0)

        # Move to 200.0, 200.0
        x1, y1 = smoother.update(200.0, 200.0)
        # Should be between 100 and 200 (smoothed)
        assert 100.0 < x1 < 200.0
        assert 100.0 < y1 < 200.0

        # After several frames of holding at 200, converges within deadzone radius of 200
        for _ in range(30):
            x1, y1 = smoother.update(200.0, 200.0)

        assert abs(x1 - 200.0) <= smoother.deadzone_pixels
        assert abs(y1 - 200.0) <= smoother.deadzone_pixels

    def test_reset_clears_state(self):
        smoother = AdaptiveSmoother()
        smoother.update(100.0, 100.0)
        smoother.reset()
        # After reset, next update acts as new initial frame
        x, y = smoother.update(900.0, 800.0)
        assert x == 900.0
        assert y == 800.0


class TestMouseController:
    @pytest.fixture
    def controller(self):
        # Controlled 1920x1080 screen, 640x480 camera
        return MouseController(
            screen_size=(1920, 1080),
            camera_size=(640, 480),
        )

    def test_screen_boundary_clamping_left_top(self, controller):
        # Value well to the left and above the frame reduction boundary
        target_x, target_y = controller.map_camera_to_screen(0.0, 0.0)
        assert target_x == 0.0
        assert target_y == 0.0

    def test_screen_boundary_clamping_right_bottom(self, controller):
        # Value well past the frame reduction boundary
        target_x, target_y = controller.map_camera_to_screen(640.0, 480.0)
        assert target_x == 1919.0
        assert target_y == 1079.0

    def test_center_mapping(self, controller):
        # Center of camera maps approximately to center of screen
        target_x, target_y = controller.map_camera_to_screen(320.0, 240.0)
        assert abs(target_x - 1919.0 / 2) < 5.0
        assert abs(target_y - 1079.0 / 2) < 5.0

    def test_move_to_returns_clamped_integer_tuple(self, controller):
        int_x, int_y = controller.move_to(320.0, 240.0)
        assert isinstance(int_x, int)
        assert isinstance(int_y, int)
        assert 0 <= int_x < 1920
        assert 0 <= int_y < 1080
