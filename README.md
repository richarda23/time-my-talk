# Time My Talk

A presentation timing tool that uses local speech recognition to help you practice and time your talks.

## Features

- **Real-time speech recognition** using Vosk (100% local, no cloud services)
- **Progress tracking** through your script as you speak
- **Pace indicator** showing whether you're ahead or behind schedule
- **Privacy-focused** - all processing happens on your machine
- **Modular architecture** - core logic can be integrated into other UIs (e.g., MS Teams)

## Requirements

- Python 3.10 or higher
- 16GB-32GB RAM (for comfortable operation)
- Microphone access
- macOS, Linux, or Windows

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd time-my-talk

# Install dependencies with uv
uv sync

# First run will download the Vosk speech recognition model (~40MB)
```

## Usage

```bash
# Basic usage
uv run time-my-talk path/to/script.txt --duration 10

# Example with sample script
uv run time-my-talk examples/sample_script.txt --duration 5
```

### Command Options

- `script_file` - Path to your presentation script (required)
- `--duration` - Target duration in minutes (required)

### Script Format

Your script should be a plain text file with the verbatim text you plan to speak. Example:

```
Welcome everyone to today's presentation on cloud computing.

In this talk, we'll explore three key concepts: scalability,
reliability, and cost optimization.

Let's start with scalability...
```

## How It Works

1. **Load Script** - Reads and tokenizes your presentation script
2. **Start Listening** - Captures audio from your microphone
3. **Recognize Speech** - Transcribes speech locally using Vosk
4. **Track Progress** - Matches recognized words to script position
5. **Calculate Pace** - Compares actual vs. expected progress
6. **Display Status** - Shows real-time feedback in the terminal

## Architecture

```
┌─────────────────────┐
│   CLI Interface     │  Terminal UI with Rich
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Core Timing Engine │  Progress tracking, pace calculation
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Speech Recognition  │  Vosk + PyAudio
└─────────────────────┘
```

The modular design allows the core timing logic to be reused in different interfaces (web, Teams, etc.).

## Development

### Project Structure

```
time-my-talk/
├── src/time_my_talk/
│   ├── speech/         # Speech recognition (Vosk integration)
│   ├── core/          # Core timing logic
│   └── cli/           # CLI interface
├── examples/          # Sample scripts
└── models/           # Downloaded Vosk models (gitignored)
```

### Running Tests

```bash
# TODO: Add tests
```

## Roadmap

- [ ] Visual script highlighting
- [ ] Section/slide markers for multi-part talks
- [ ] Session recording and replay
- [ ] Web UI for browser-based usage
- [ ] MS Teams integration
- [ ] Multiple language support

## Privacy

All speech recognition happens locally on your machine using Vosk. No audio or text is sent to external services. The Vosk model is downloaded once during setup and cached locally.

## License

TODO: Add license

## Contributing

Contributions welcome! Please open an issue or PR.
