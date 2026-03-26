"""Script parsing and tokenization."""

import re
from pathlib import Path
from typing import List

from .types import Word


class Script:
    """Loads and manages a presentation script."""

    def __init__(self, file_path: str):
        """Load script from file.

        Args:
            file_path: Path to the script text file
        """
        self.file_path = Path(file_path)
        self.original_text = self._load_file()
        self.words = self._tokenize()

    def _load_file(self) -> str:
        """Load the script file content."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Script file not found: {self.file_path}")

        return self.file_path.read_text(encoding="utf-8")

    def _tokenize(self) -> List[Word]:
        """Tokenize the script into words.

        Returns:
            List of Word objects with original text, normalized form, and positions
        """
        words = []
        # Find all words (sequences of alphanumeric characters and apostrophes)
        pattern = r"\b[\w']+\b"

        for match in re.finditer(pattern, self.original_text):
            original = match.group()
            normalized = self._normalize_word(original)

            word = Word(
                original=original,
                normalized=normalized,
                position=match.start(),
                index=len(words),
            )
            words.append(word)

        return words

    @staticmethod
    def _normalize_word(word: str) -> str:
        """Normalize a word for matching.

        Args:
            word: Original word

        Returns:
            Normalized word (lowercase, no punctuation)
        """
        # Convert to lowercase and remove non-alphanumeric except apostrophes
        normalized = word.lower()
        # Remove trailing punctuation but keep internal apostrophes
        normalized = re.sub(r"[^\w']+$", "", normalized)
        normalized = re.sub(r"^[^\w']+", "", normalized)
        return normalized

    @property
    def word_count(self) -> int:
        """Total number of words in the script."""
        return len(self.words)

    def get_context(self, word_index: int, context_words: int = 5) -> str:
        """Get text context around a word index.

        Args:
            word_index: Index of the word
            context_words: Number of words to include before and after

        Returns:
            String with context (e.g., "...and this is why we need...")
        """
        start_idx = max(0, word_index - context_words)
        end_idx = min(len(self.words), word_index + context_words + 1)

        context_words_list = [w.original for w in self.words[start_idx:end_idx]]
        context = " ".join(context_words_list)

        # Add ellipsis if truncated
        if start_idx > 0:
            context = "..." + context
        if end_idx < len(self.words):
            context = context + "..."

        return context
