"""Script parsing and tokenization."""

import re
from pathlib import Path
from typing import List

from .types import Word


class Script:
    """Loads and manages a presentation script."""

    def __init__(self, file_path: str, split_compounds: bool = True):
        """Load script from file.

        Args:
            file_path: Path to the script text file
            split_compounds: Whether to split compound/CamelCase words for better speech recognition matching
        """
        self.file_path = Path(file_path)
        self.split_compounds = split_compounds
        self.original_text = self._load_file()
        if self.split_compounds:
            self.original_text = self._preprocess_compounds(self.original_text)
        self.words = self._tokenize()

    def _load_file(self) -> str:
        """Load the script file content."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Script file not found: {self.file_path}")

        return self.file_path.read_text(encoding="utf-8")

    @staticmethod
    def _preprocess_compounds(text: str) -> str:
        """Preprocess text to split compound and CamelCase words.

        This helps speech recognition match better since spoken phrases like
        "NHS England" will be transcribed as separate words but might be
        written as "NHSEngland" in the script.

        Args:
            text: Original text

        Returns:
            Text with compound words split
        """
        # Split on transitions from lowercase to uppercase (camelCase)
        # But preserve sequences of all caps (NHS, WCAG) as single units initially
        # Then split long sequences of caps if followed by lowercase

        # Insert space between lowercase and uppercase: devOps -> dev Ops
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

        # Insert space between sequence of caps and a following lowercase: HTMLParser -> HTML Parser
        text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)

        # Split acronyms that are likely spoken letter by letter (3+ caps in a row at word boundary)
        # WCAG -> W C A G, but preserve if part of a longer word
        def split_acronym(match):
            acronym = match.group(1)
            if len(acronym) >= 3:
                # Split into individual letters with spaces
                return " ".join(acronym)
            return acronym

        # Match 3+ capital letters as a standalone "word" (with word boundaries)
        text = re.sub(r"\b([A-Z]{3,})\b", split_acronym, text)

        return text

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
