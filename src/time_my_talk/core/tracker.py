"""Progress tracking through the script."""

import re
from typing import List, Optional

from .script import Script
from .types import ProgressStatus


class ProgressTracker:
    """Tracks progress through a script by matching recognized speech."""

    def __init__(
        self,
        script: Script,
        skip_tolerance: int = 3,
        look_ahead_window: int = 100,
        sequence_match_length: int = 3,
    ):
        """Initialize progress tracker.

        Args:
            script: The Script object to track progress through
            skip_tolerance: Number of unmatched words to tolerate before considering a skip
            look_ahead_window: How many words ahead to search when detecting a skip
            sequence_match_length: Number of consecutive words that must match to confirm a skip location
        """
        self.script = script
        self.skip_tolerance = skip_tolerance
        self.look_ahead_window = look_ahead_window
        self.sequence_match_length = sequence_match_length
        self.current_index = 0
        self.last_matched_text = ""
        self._unmatched_count = 0
        self._recent_unmatched_words: List[str] = []

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
            self._recent_unmatched_words.clear()
            return True

        # Try looking ahead within tolerance (for filler words/mistakes)
        for look_ahead in range(1, self.skip_tolerance + 1):
            check_index = self.current_index + look_ahead
            if check_index < len(self.script.words):
                if self.script.words[check_index].normalized == word:
                    # Found a match ahead - advance to it
                    self.current_index = check_index + 1
                    self._unmatched_count = 0
                    self._recent_unmatched_words.clear()
                    return True

        # No match found - collect this word for potential skip detection
        self._unmatched_count += 1
        self._recent_unmatched_words.append(word)

        # Keep buffer size reasonable
        if len(self._recent_unmatched_words) > self.sequence_match_length * 2:
            self._recent_unmatched_words.pop(0)

        # If too many unmatched, search ahead for where we might have jumped to
        if self._unmatched_count > self.skip_tolerance:
            new_position = self._search_ahead_for_match()
            if new_position is not None:
                # Found a match! Jump to the new position
                self.current_index = new_position
                self._unmatched_count = 0
                self._recent_unmatched_words.clear()
                return True
            else:
                # No match found, reset counter and keep trying
                self._unmatched_count = 0
                self._recent_unmatched_words.clear()

        return False

    def _search_ahead_for_match(self) -> Optional[int]:
        """Search ahead in the script for a matching sequence of words.

        When the speaker skips a section, this method looks ahead to find where
        they likely jumped to by matching recent unmatched words.

        Returns:
            The script index where a match was found, or None if no match
        """
        if len(self._recent_unmatched_words) < self.sequence_match_length:
            return None

        # Get the most recent words to search for
        search_sequence = self._recent_unmatched_words[-self.sequence_match_length :]

        # Search within the look-ahead window
        search_end = min(
            len(self.script.words), self.current_index + self.look_ahead_window
        )

        # Start searching a bit ahead of current position to avoid false positives
        search_start = self.current_index + self.skip_tolerance + 1

        for start_idx in range(search_start, search_end):
            # Check if we have enough words left to match the sequence
            if start_idx + self.sequence_match_length > len(self.script.words):
                break

            # Try to match the sequence at this position
            match_count = 0
            for i, search_word in enumerate(search_sequence):
                script_word = self.script.words[start_idx + i].normalized
                if script_word == search_word:
                    match_count += 1

            # If all words in the sequence match, we found the skip location
            if match_count == self.sequence_match_length:
                # Return the position after the matched sequence
                return start_idx + self.sequence_match_length

        return None

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
        self._recent_unmatched_words.clear()
