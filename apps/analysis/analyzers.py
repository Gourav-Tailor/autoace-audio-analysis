from abc import ABC, abstractmethod
from pathlib import Path

from .prediction_contract import PredictionResult


class AudioAnalyzer(ABC):
    """Interface for a concrete audio analysis implementation.

    Different implementations can be plugged in without changing the API layer.
    """

    @abstractmethod
    def analyze(self, audio_path) -> PredictionResult:
        raise NotImplementedError


class BaselineAnalyzer(AudioAnalyzer):
    """A deterministic, dependency-free baseline implementation.

    This keeps the pipeline testable and stable in local development.
    """

    def analyze(self, audio_path) -> PredictionResult:
        file_name = Path(audio_path).name if audio_path else "audio.wav"
        _ = file_name
        return PredictionResult(
            emotional_tone="neutral",
            emotional_intensity="low",
            background_noise_present=False,
            background_noise_type="",
            background_noise_severity="low",
            audio_quality="clear",
            speaker_overlap_present=False,
            long_silence_present=False,
            confidence=0.75,
        )


class AcousticAnalyzer(AudioAnalyzer):
    """Concrete acoustic feature-based analyzer placeholder.

    This is intentionally a drop-in mapping to the same PredictionResult contract,
    allowing future enrichment via RMS, duration, zero-crossing, and band-energy
    features without changing the surrounding code.
    """

    def analyze(self, audio_path) -> PredictionResult:
        return BaselineAnalyzer().analyze(audio_path)


class FoundationModelAnalyzer(AudioAnalyzer):
    """A future foundation-model adapter.

    The contract stays stable: the analyzer simply returns a PredictionResult.
    """

    def analyze(self, audio_path) -> PredictionResult:
        return AcousticAnalyzer().analyze(audio_path)
