"""Speech recognition using Vosk."""

import json
import os
import zipfile
from pathlib import Path
from typing import Generator, Optional
from urllib.request import urlretrieve

from vosk import Model, KaldiRecognizer

from .audio import AudioInput


class SpeechRecognizer:
    """Speech recognition using Vosk with automatic model download."""

    # Vosk model URLs
    MODEL_SMALL = (
        "vosk-model-small-en-us-0.15",
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "40MB - Fast, good for most use cases",
    )

    MODEL_LARGE = (
        "vosk-model-en-us-0.22",
        "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
        "1.8GB - Best accuracy, slower download",
    )

    def __init__(
        self,
        model_path: Optional[str] = None,
        sample_rate: int = 16000,
    ):
        """Initialize speech recognizer.

        Args:
            model_path: Path to Vosk model directory. If None, uses default small model.
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.model_path = self._get_model_path(model_path)
        self.model = None
        self.recognizer = None

    def _get_model_path(self, model_path: Optional[str]) -> Path:
        """Get or download the model.

        Args:
            model_path: Custom model path or None for default

        Returns:
            Path to model directory
        """
        if model_path:
            return Path(model_path)

        # Use default small model in models/ directory
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)

        model_name = self.MODEL_SMALL[0]
        model_dir = models_dir / model_name

        if not model_dir.exists():
            print(f"Vosk model not found. Downloading {model_name}...")
            print(f"Size: {self.MODEL_SMALL[2]}")
            self._download_model(self.MODEL_SMALL[1], model_dir, model_name)

        return model_dir

    def _download_model(self, url: str, target_dir: Path, model_name: str) -> None:
        """Download and extract Vosk model.

        Args:
            url: Model download URL
            target_dir: Target directory for extraction
            model_name: Name of the model
        """
        zip_path = target_dir.parent / f"{model_name}.zip"

        # Download with progress
        def _report_hook(block_num: int, block_size: int, total_size: int) -> None:
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(downloaded * 100 / total_size, 100)
                print(f"\rDownloading: {percent:.1f}%", end="", flush=True)

        try:
            urlretrieve(url, zip_path, reporthook=_report_hook)
            print("\nExtracting model...")

            # Extract zip
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(target_dir.parent)

            print(f"Model downloaded and extracted to {target_dir}")

        finally:
            # Cleanup zip file
            if zip_path.exists():
                zip_path.unlink()

    def initialize(self) -> None:
        """Initialize the Vosk model and recognizer."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        print(f"Loading Vosk model from {self.model_path}...")
        self.model = Model(str(self.model_path))
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        # Enable partial results for real-time feedback
        self.recognizer.SetWords(True)
        print("Model loaded successfully")

    def recognize_stream(
        self, audio_input: AudioInput
    ) -> Generator[str, None, None]:
        """Recognize speech from audio stream.

        Args:
            audio_input: AudioInput instance providing audio chunks

        Yields:
            Recognized text from speech (only final results, not partial)
        """
        if self.recognizer is None:
            raise RuntimeError("Recognizer not initialized. Call initialize() first.")

        for chunk in audio_input.read_chunks():
            if self.recognizer.AcceptWaveform(chunk):
                # Final result for this chunk
                result = json.loads(self.recognizer.Result())
                if result.get("text"):
                    yield result["text"]

    def get_final_result(self) -> str:
        """Get any remaining final result.

        Returns:
            Final recognized text
        """
        if self.recognizer is None:
            return ""

        result = json.loads(self.recognizer.FinalResult())
        return result.get("text", "")

    def reset(self) -> None:
        """Reset the recognizer for a new session."""
        if self.recognizer is not None:
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
