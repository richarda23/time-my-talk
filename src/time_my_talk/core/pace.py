"""Pace calculation for presentation timing."""

from .types import PaceStatus


class PaceCalculator:
    """Calculates whether a speaker is on pace, ahead, or behind schedule."""

    def __init__(self, target_duration_minutes: float, tolerance_seconds: float = 30.0):
        """Initialize pace calculator.

        Args:
            target_duration_minutes: Target presentation duration in minutes
            tolerance_seconds: Tolerance in seconds for "on pace" status (default 30)
        """
        self.target_duration_seconds = target_duration_minutes * 60
        self.tolerance_seconds = tolerance_seconds

    def calculate_pace(
        self, elapsed_seconds: float, actual_percentage: float
    ) -> PaceStatus:
        """Calculate current pace status.

        Args:
            elapsed_seconds: Time elapsed since start
            actual_percentage: Actual progress percentage (0-100)

        Returns:
            PaceStatus with pace information
        """
        # Calculate expected percentage at this time
        expected_percentage = (
            (elapsed_seconds / self.target_duration_seconds * 100)
            if self.target_duration_seconds > 0
            else 0.0
        )

        # Ensure percentages don't exceed 100%
        expected_percentage = min(expected_percentage, 100.0)
        actual_percentage = min(actual_percentage, 100.0)

        # Calculate time difference
        # If actual > expected, we're ahead (positive seconds_ahead)
        # If actual < expected, we're behind (negative seconds_ahead)
        percentage_diff = actual_percentage - expected_percentage
        seconds_ahead = (
            percentage_diff / 100 * self.target_duration_seconds
            if self.target_duration_seconds > 0
            else 0.0
        )

        # Check if within tolerance
        is_on_pace = abs(seconds_ahead) <= self.tolerance_seconds

        return PaceStatus(
            elapsed_seconds=elapsed_seconds,
            expected_percentage=expected_percentage,
            actual_percentage=actual_percentage,
            seconds_ahead=seconds_ahead,
            is_on_pace=is_on_pace,
        )

    def update_target_duration(self, target_duration_minutes: float) -> None:
        """Update target duration.

        Args:
            target_duration_minutes: New target duration in minutes
        """
        self.target_duration_seconds = target_duration_minutes * 60
