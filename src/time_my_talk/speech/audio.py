"""Audio input handling for microphone capture."""

import pyaudio
from typing import Generator


class AudioInput:
    """Handles microphone audio input."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 4096,
        channels: int = 1,
    ):
        """Initialize audio input.

        Args:
            sample_rate: Audio sample rate in Hz (Vosk typically uses 16000)
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1 for mono)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None

    def start(self) -> None:
        """Start capturing audio from the microphone."""
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

    def read_chunks(self) -> Generator[bytes, None, None]:
        """Read audio data in chunks.

        Yields:
            Audio data chunks as bytes

        Raises:
            RuntimeError: If stream not started
        """
        if self.stream is None:
            raise RuntimeError("Audio stream not started. Call start() first.")

        while True:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                yield data
            except Exception as e:
                print(f"Error reading audio: {e}")
                break

    def stop(self) -> None:
        """Stop capturing audio and cleanup resources."""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def cleanup(self) -> None:
        """Cleanup PyAudio resources."""
        self.stop()
        self.pyaudio_instance.terminate()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
