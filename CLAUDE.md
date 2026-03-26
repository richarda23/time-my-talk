# Claude Code Instructions for TimeMyTalk

## Project Overview

TimeMyTalk is a presentation timing tool that uses **local speech recognition** (Vosk) to help presenters practice talks. It listens to the speaker via microphone, matches speech to a prepared script, and provides real-time feedback on pace and progress.

**Key principle**: All speech recognition happens locally - no cloud services, no data sent anywhere. Privacy is a core feature.

## Architecture

```
CLI Interface (Rich terminal UI)
    ↓
Core Timing Engine (script.py, tracker.py, pace.py)
    ↓
Speech Recognition (Vosk + PyAudio)
```

The core modules are UI-agnostic and designed to be reusable in other interfaces (web, MS Teams, etc.).

### Core Components

1. **Script** (`core/script.py`) - Loads and tokenizes presentation scripts
   - Normalizes words (lowercase, strips punctuation)
   - Maintains original text positions for context display

2. **ProgressTracker** (`core/tracker.py`) - Matches recognized speech to script position
   - **Critical feature**: Section skip detection with look-ahead search
   - Tolerates filler words ("um", "uh") via configurable skip_tolerance
   - When too many words don't match, searches ahead for matching sequences

3. **PaceCalculator** (`core/pace.py`) - Compares actual vs expected progress
   - Linear progress assumption (uniform pace throughout)
   - Configurable tolerance window (default ±30 seconds)

4. **SpeechRecognizer** (`speech/recognizer.py`) - Wraps Vosk
   - Auto-downloads model on first run (~40MB)
   - Yields recognized text chunks continuously

## Section Skip Detection (Key Feature)

**User requirement**: Presenters need to skip sections to catch up if running behind.

**Implementation** (`tracker.py`):
- Collects recent unmatched words in a buffer
- When `skip_tolerance` exceeded, triggers `_search_ahead_for_match()`
- Searches up to `look_ahead_window` words ahead (default: 100)
- Requires `sequence_match_length` consecutive words to match (default: 3)
- If found, jumps to that position and continues tracking

**Parameters** (all configurable):
```python
ProgressTracker(
    script,
    skip_tolerance=3,           # words to tolerate for fillers
    look_ahead_window=100,      # how far ahead to search
    sequence_match_length=3     # consecutive words needed to confirm skip
)
```

## Development Conventions

### Code Style
- Type hints on function arguments
- Docstrings for public APIs
- Keep functions focused and modular
- PEP 8 formatting

### Git Workflow
- Feature branches for new work
- Descriptive commit messages
- Clean merge history to main
- Co-authored commits: `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`

### Dependencies
- **Python**: 3.10+ required
- **Vosk**: Pinned to 0.3.44 (latest with macOS ARM support)
- **PyAudio**: Requires system-level PortAudio (`brew install portaudio` on macOS)
- **Rich**: Terminal UI
- **Click**: CLI argument parsing

### Installation Method
- **Preferred**: `uv sync` (fast, reliable)
- **Alternative**: Standard pip with venv
- First run auto-downloads Vosk model to `models/` directory (gitignored)

## Important Technical Notes

### Platform Compatibility
- **Tested**: macOS 15.0+ (Apple Silicon)
- **Should work**: Linux, Windows (not tested)
- Vosk 0.3.44 is latest version with ARM support - don't upgrade blindly

### Performance Considerations
- Real-time speech recognition is CPU-intensive
- Requires 16GB RAM minimum, 32GB recommended
- UI refresh rate: 2Hz (configurable in cli/main.py)

### File Structure
```
src/time_my_talk/
├── speech/          # Audio capture and Vosk integration
├── core/            # Core timing logic (UI-agnostic)
└── cli/             # Terminal UI (Rich-based)
```

## Testing

Currently no automated tests. Manual testing approach:
```bash
# Verify imports
python -c "from time_my_talk.cli.main import main; print('✓ Imports OK')"

# Test with sample script (requires microphone)
uv run python -m time_my_talk.cli.main examples/sample_script.txt --duration 5
```

## Future Enhancements

See README "Next Steps" section for roadmap. Key items:
- MS Teams integration (core logic ready, needs web UI + backend)
- Section/slide markers for multi-part talks
- Session summaries and export
- Unit tests with mock audio

## Gotchas

1. **Don't skip git hooks** - never use `--no-verify` unless explicitly requested
2. **Vosk version pinning** - 0.3.44 is intentional for ARM compatibility
3. **PyAudio dependency** - requires system library, can't be pure Python
4. **Model download** - first run needs internet, then fully offline
5. **Skip detection** - relies on finding exact word sequences, may fail with heavy paraphrasing

## When Making Changes

### To Progress Tracking
- Test with sample script that has repetitive words (can cause false matches)
- Consider impact on both normal flow and skip detection
- Parameters should remain configurable

### To Speech Recognition
- Changes here affect latency and accuracy trade-offs
- Larger Vosk models = better accuracy but slower download
- Don't change audio parameters without testing on real hardware

### To CLI Interface
- Keep terminal UI responsive (avoid blocking operations)
- Rich library handles live updates - use Live context manager
- Color coding: green = on pace, yellow = ahead, red = behind

## Repository

- **GitHub**: https://github.com/richarda23/time-my-talk
- **License**: MIT
- **Main branch**: `main`
- **Active development**: Yes (new project, v0.1.0)

## Contact Pattern

When suggesting changes:
1. Read relevant code first
2. Consider both normal and edge cases
3. Maintain configurability
4. Keep privacy/local-first principle
5. Don't add features beyond what's requested
