"""Progress tracking through the script."""

import re
from typing import List

from .script import Script
from .types import ProgressStatus


class ProgressTracker:
    """Tracks progress through a script by matching recognized speech."""

    def __init__(self, script: Script, skip_tolerance: int = 3):
        """Initialize progress tracker.

        Args:
            script: The Script object to track progress through
            skip_tolerance: Number of unmatched words to tolerate before considering a skip
        """
        self.script = script
        self.skip_tolerance = skip_tolerance
        self.current_index = 0
        self.last_matched_text = ""
        self._unmatched_count = 0

    def update(self, transcribed_text: str) -> ProgressStatus:
        """Update progress based on newly transcribed text.

        Args:
            transcribed_text: Text recognized from speech

        Returns:
            Current progress status
        """
        # Normalize and tokenize the transcribed text
        words = self._tokenize(transcribed_text)

        # Try to match each word sequentially
        for word in words:
            if self._try_match_word(word):
                self.last_matched_text = transcribed_text[-50:]  # Keep last 50 chars

        return self.get_status()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text into words.

        Args:
            text: Text to tokenize

        Returns:
            List of normalized words
        """
        # Find all words
        pattern = r"\b[\w']+\b"
        words = re.findall(pattern, text)

        # Normalize each word
        normalized = []
        for word in words:
            normalized_word = word.lower()
            normalized_word = re.sub(r"[^\w']+$", "", normalized_word)
            normalized_word = re.sub(r"^[^\w']+", "", normalized_word)
            if normalized_word:  # Only add non-empty words
                normalized.append(normalized_word)

        return normalized

    def _try_match_word(self, word: str) -> bool:
        """Try to match a word against the current position in the script.

        Args:
            word: Normalized word to match

        Returns:
            True if a match was found and index was advanced
        """
        # Check if we've reached the end
        if self.current_index >= len(self.script.words):
            return False

        # Try to match at current position
        if self.script.words[self.current_index].normalized == word:
            self.current_index += 1
            self._unmatched_count = 0
            return True

        # Try looking ahead within tolerance (for filler words/mistakes)
        for look_ahead in range(1, self.skip_tolerance + 1):
            check_index = self.current_index + look_ahead
            if check_index < len(self.script.words):
                if self.script.words[check_index].normalized == word:
                    # Found a match ahead - advance to it
                    self.current_index = check_index + 1
                    self._unmatched_count = 0
                    return True

        # No match found
        self._unmatched_count += 1

        # If too many unmatched, maybe we skipped a section
        # For now, just continue without advancing
        if self._unmatched_count > self.skip_tolerance:
            # Could implement more sophisticated recovery here
            self._unmatched_count = 0

        return False

    def get_status(self) -> ProgressStatus:
        """Get current progress status.

        Returns:
            ProgressStatus with current position and percentage
        """
        percentage = (
            (self.current_index / len(self.script.words) * 100)
            if len(self.script.words) > 0
            else 0.0
        )

        return ProgressStatus(
            current_word_index=self.current_index,
            total_words=len(self.script.words),
            percentage=percentage,
            last_matched_text=self.last_matched_text,
        )

    def reset(self) -> None:
        """Reset progress to the beginning."""
        self.current_index = 0
        self.last_matched_text = ""
        self._unmatched_count = 0
