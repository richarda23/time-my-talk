"""Tests for ProgressTracker."""

import pytest

from time_my_talk.core.script import Script
from time_my_talk.core.tracker import ProgressTracker


def make_script(tmp_path, text):
    f = tmp_path / "script.txt"
    f.write_text(text)
    return Script(str(f), split_compounds=False)


@pytest.fixture
def simple_tracker(tmp_path):
    script = make_script(tmp_path, "one two three four five six seven eight nine ten")
    return ProgressTracker(script, skip_tolerance=2, look_ahead_window=20, sequence_match_length=3)


# ---------------------------------------------------------------------------
# Basic matching
# ---------------------------------------------------------------------------


def test_initial_state(simple_tracker):
    status = simple_tracker.get_status()
    assert status.current_word_index == 0
    assert status.percentage == 0.0
    assert status.total_words == 10


def test_sequential_match_advances_index(simple_tracker):
    simple_tracker.update("one two three")
    status = simple_tracker.get_status()
    assert status.current_word_index == 3


def test_full_script_match(simple_tracker):
    simple_tracker.update("one two three four five six seven eight nine ten")
    status = simple_tracker.get_status()
    assert status.current_word_index == 10
    assert status.percentage == 100.0


def test_percentage_calculation(simple_tracker):
    simple_tracker.update("one two three four five")
    status = simple_tracker.get_status()
    assert status.percentage == pytest.approx(50.0)


def test_last_matched_text_updated(simple_tracker):
    simple_tracker.update("one two three")
    assert simple_tracker.last_matched_text != ""


# ---------------------------------------------------------------------------
# Filler word tolerance
# ---------------------------------------------------------------------------


def test_filler_words_skipped_within_tolerance(simple_tracker):
    # "um uh" are fillers between "one" and "two" — within skip_tolerance=2
    simple_tracker.update("one um uh two three")
    status = simple_tracker.get_status()
    assert status.current_word_index == 3


def test_single_filler_word_skipped(simple_tracker):
    simple_tracker.update("one um two")
    status = simple_tracker.get_status()
    assert status.current_word_index == 2


# ---------------------------------------------------------------------------
# Section skip detection
# ---------------------------------------------------------------------------


def test_section_skip_jumps_ahead(tmp_path):
    script = make_script(
        tmp_path,
        "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    )
    tracker = ProgressTracker(
        script,
        skip_tolerance=2,
        look_ahead_window=20,
        sequence_match_length=3,
    )
    # Speak first word then jump to "eta theta iota"
    tracker.update("alpha")
    assert tracker.current_index == 1

    tracker.update("eta theta iota")
    # After skip detection, should be at index 9 (past "eta theta iota")
    assert tracker.current_index == 9


def test_no_false_skip_when_words_match_sequentially(simple_tracker):
    # Normal flow should not trigger a spurious skip
    simple_tracker.update("one two")
    simple_tracker.update("three four")
    assert simple_tracker.current_index == 4


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_reset_returns_to_start(simple_tracker):
    simple_tracker.update("one two three")
    simple_tracker.reset()
    status = simple_tracker.get_status()
    assert status.current_word_index == 0
    assert status.percentage == 0.0
    assert simple_tracker.last_matched_text == ""


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_update_past_end_is_safe(simple_tracker):
    simple_tracker.update("one two three four five six seven eight nine ten")
    # Updating past the end should not raise
    simple_tracker.update("eleven twelve")
    assert simple_tracker.current_index == 10


def test_empty_transcription(simple_tracker):
    simple_tracker.update("")
    assert simple_tracker.current_index == 0


def test_empty_script(tmp_path):
    script = make_script(tmp_path, "")
    tracker = ProgressTracker(script)
    status = tracker.get_status()
    assert status.percentage == 0.0
    assert status.total_words == 0
