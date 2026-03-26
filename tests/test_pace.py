"""Tests for PaceCalculator."""

import pytest

from time_my_talk.core.pace import PaceCalculator
from time_my_talk.core.types import PaceStatus


@pytest.fixture
def calculator():
    """10-minute talk, 5% tolerance (= 30s)."""
    return PaceCalculator(target_duration_minutes=10.0, tolerance_percentage=5.0)


# ---------------------------------------------------------------------------
# On pace
# ---------------------------------------------------------------------------


def test_exactly_on_pace(calculator):
    # 5 min elapsed out of 10 = 50% expected; actual 50%
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=50.0)
    assert status.is_on_pace
    assert status.seconds_ahead == pytest.approx(0.0)


def test_within_tolerance_is_on_pace(calculator):
    # 5 min elapsed; actual 52% (1.2% ahead = 7.2s, within 30s tolerance)
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=52.0)
    assert status.is_on_pace


def test_just_inside_tolerance_boundary(calculator):
    # 30s ahead = exactly at tolerance edge → on pace
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=55.0)
    # 5% of 600s = 30s; 55%-50% = 5% of 600s = 30s
    assert status.is_on_pace


# ---------------------------------------------------------------------------
# Ahead of pace
# ---------------------------------------------------------------------------


def test_significantly_ahead(calculator):
    # 5 min elapsed; actual 70% (20% ahead = 120s)
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=70.0)
    assert not status.is_on_pace
    assert status.seconds_ahead > 0
    assert status.status_text.endswith("seconds ahead")


def test_seconds_ahead_calculation(calculator):
    # 10% ahead of expected at midpoint = 60s ahead (10% of 600s)
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=60.0)
    assert status.seconds_ahead == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Behind pace
# ---------------------------------------------------------------------------


def test_significantly_behind(calculator):
    # 5 min elapsed; actual 30% (20% behind = 120s)
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=30.0)
    assert not status.is_on_pace
    assert status.seconds_ahead < 0
    assert status.status_text.endswith("seconds behind")


def test_seconds_behind_calculation(calculator):
    # 10% behind expected at midpoint = 60s behind
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=40.0)
    assert status.seconds_ahead == pytest.approx(-60.0)


# ---------------------------------------------------------------------------
# PaceStatus.status_text
# ---------------------------------------------------------------------------


def test_status_text_on_pace(calculator):
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=50.0)
    assert status.status_text == "On pace"


def test_status_text_ahead(calculator):
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=70.0)
    assert "ahead" in status.status_text


def test_status_text_behind(calculator):
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=30.0)
    assert "behind" in status.status_text


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_expected_percentage_capped_at_100():
    calc = PaceCalculator(target_duration_minutes=5.0)
    # Elapsed > target duration
    status = calc.calculate_pace(elapsed_seconds=400, actual_percentage=80.0)
    assert status.expected_percentage == pytest.approx(100.0)


def test_actual_percentage_capped_at_100(calculator):
    status = calculator.calculate_pace(elapsed_seconds=300, actual_percentage=120.0)
    assert status.actual_percentage == pytest.approx(100.0)


def test_at_start_on_pace(calculator):
    status = calculator.calculate_pace(elapsed_seconds=0, actual_percentage=0.0)
    assert status.is_on_pace
    assert status.seconds_ahead == pytest.approx(0.0)


def test_update_target_duration(calculator):
    calculator.update_target_duration(20.0)
    assert calculator.target_duration_seconds == pytest.approx(1200.0)
    assert calculator.tolerance_seconds == pytest.approx(60.0)  # 5% of 1200
