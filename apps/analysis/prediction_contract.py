from dataclasses import dataclass
from typing import Literal

VALID_TONES = {"neutral", "satisfied", "frustrated", "upset", "distressed"}
VALID_INTENSITIES = {"low", "medium", "high"}
VALID_SEVERITIES = {"low", "medium", "high"}
VALID_QUALITIES = {"clear", "slightly_impaired", "severely_impaired"}


@dataclass(frozen=True)
class PredictionResult:
    emotional_tone: Literal["neutral", "satisfied", "frustrated", "upset", "distressed"]
    emotional_intensity: Literal["low", "medium", "high"]
    background_noise_present: bool
    background_noise_type: str
    background_noise_severity: Literal["low", "medium", "high"]
    audio_quality: Literal["clear", "slightly_impaired", "severely_impaired"]
    speaker_overlap_present: bool
    long_silence_present: bool
    confidence: float

    def __post_init__(self) -> None:
        if self.emotional_tone not in VALID_TONES:
            raise ValueError(
                "emotional_tone must be one of: "
                "neutral, satisfied, frustrated, upset, distressed"
            )
        if self.emotional_intensity not in VALID_INTENSITIES:
            raise ValueError("emotional_intensity must be one of: low, medium, high")
        if self.background_noise_severity not in VALID_SEVERITIES:
            raise ValueError(
                "background_noise_severity must be one of: low, medium, high"
            )
        if self.audio_quality not in VALID_QUALITIES:
            raise ValueError(
                "audio_quality must be one of: "
                "clear, slightly_impaired, severely_impaired"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be a float between 0 and 1")

    def to_dict(self) -> dict:
        return {
            "emotional_tone": self.emotional_tone,
            "emotional_intensity": self.emotional_intensity,
            "background_noise_present": self.background_noise_present,
            "background_noise_type": self.background_noise_type,
            "background_noise_severity": self.background_noise_severity,
            "audio_quality": self.audio_quality,
            "speaker_overlap_present": self.speaker_overlap_present,
            "long_silence_present": self.long_silence_present,
            "confidence": self.confidence,
        }
