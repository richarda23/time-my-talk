"""Shared type definitions for the core timing engine."""

from dataclasses import dataclass
from typing import List


@dataclass
class Word:
    """A word from the script with its original text and normalized form."""

    original: str
    normalized: str
    position: int  # Character position in original script
    index: int  # Word index in script


@dataclass
class ProgressStatus:
    """Current progress through the script."""

    current_word_index: int
    total_words: int
    percentage: float
    last_matched_text: str


@dataclass
class PaceStatus:
    """Pace information comparing actual vs. expected progress."""

    elapsed_seconds: float
    expected_percentage: float
    actual_percentage: float
    seconds_ahead: float  # Positive means ahead, negative means behind
    is_on_pace: bool  # True if within tolerance (e.g., ±30 seconds)

    @property
    def status_text(self) -> str:
        """Human-readable status."""
        if self.is_on_pace:
            return "On pace"
        elif self.seconds_ahead > 0:
            return f"{abs(self.seconds_ahead):.0f} seconds ahead"
        else:
            return f"{abs(self.seconds_ahead):.0f} seconds behind"
