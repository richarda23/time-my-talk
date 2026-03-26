"""Tests for Script parsing and tokenization."""

import pytest

from time_my_talk.core.script import Script


@pytest.fixture
def simple_script(tmp_path):
    f = tmp_path / "script.txt"
    f.write_text("Hello world. This is a test script.")
    return Script(str(f), split_compounds=False)


@pytest.fixture
def script_file(tmp_path):
    """Return a factory that writes text to a temp file and loads a Script."""

    def _make(text, split_compounds=False):
        f = tmp_path / "script.txt"
        f.write_text(text)
        return Script(str(f), split_compounds=split_compounds)

    return _make


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------


def test_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        Script(str(tmp_path / "missing.txt"))


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------


def test_word_count(simple_script):
    assert simple_script.word_count == 7


def test_words_have_correct_normalized_form(simple_script):
    normalized = [w.normalized for w in simple_script.words]
    assert normalized == ["hello", "world", "this", "is", "a", "test", "script"]


def test_words_have_correct_original(simple_script):
    originals = [w.original for w in simple_script.words]
    assert originals == ["Hello", "world", "This", "is", "a", "test", "script"]


def test_word_indices_are_sequential(simple_script):
    for i, word in enumerate(simple_script.words):
        assert word.index == i


def test_apostrophe_preserved(script_file):
    s = script_file("It's a good idea, don't you think?")
    normalized = [w.normalized for w in s.words]
    assert "it's" in normalized
    assert "don't" in normalized


def test_punctuation_stripped_from_normalization(script_file):
    s = script_file("Wait... Really?")
    normalized = [w.normalized for w in s.words]
    assert normalized == ["wait", "really"]


# ---------------------------------------------------------------------------
# Compound / CamelCase splitting
# ---------------------------------------------------------------------------


def test_camel_case_split(script_file):
    s = script_file("We use devOps practices.", split_compounds=True)
    normalized = [w.normalized for w in s.words]
    assert "dev" in normalized
    assert "ops" in normalized


def test_pascal_case_split(script_file):
    # HTMLParser -> "HTML Parser" (caps+lowercase split), then "HTML" -> "H T M L" (acronym split)
    s = script_file("HTMLParser is useful.", split_compounds=True)
    normalized = [w.normalized for w in s.words]
    assert "parser" in normalized
    # HTML (4 caps) gets further expanded to individual letters
    assert "h" in normalized and "t" in normalized and "m" in normalized and "l" in normalized


def test_acronym_split_three_plus_chars(script_file):
    s = script_file("WCAG guidelines.", split_compounds=True)
    normalized = [w.normalized for w in s.words]
    # WCAG -> W C A G (4 individual letters)
    assert "w" in normalized
    assert "c" in normalized
    assert "a" in normalized
    assert "g" in normalized


def test_two_char_acronym_not_split(script_file):
    # 2-char all-caps should NOT be expanded to individual letters
    s = script_file("AI is the future.", split_compounds=True)
    normalized = [w.normalized for w in s.words]
    assert "ai" in normalized


def test_split_compounds_false_preserves_camel(script_file):
    s = script_file("devOps practices.", split_compounds=False)
    normalized = [w.normalized for w in s.words]
    assert "devops" in normalized


# ---------------------------------------------------------------------------
# get_context
# ---------------------------------------------------------------------------


def test_get_context_middle(simple_script):
    context = simple_script.get_context(3, context_words=2)
    # word 3 is "is"; surrounding: "This is a test"
    assert "is" in context
    assert "..." in context  # truncated on both sides


def test_get_context_start(simple_script):
    context = simple_script.get_context(0, context_words=2)
    # At the start, no leading ellipsis
    assert not context.startswith("...")


def test_get_context_end(simple_script):
    last_idx = simple_script.word_count - 1
    context = simple_script.get_context(last_idx, context_words=2)
    # At the end, no trailing ellipsis
    assert not context.endswith("...")
