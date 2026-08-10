import math
import struct
import wave
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

    This keeps the pipeline testable and stable in local development. The
    analyzer intentionally defaults to a neutral, low-intensity detection path
    when no audio file is available. When a real WAV is provided, the acoustic
    analyzer below can derive a richer prediction contract from frame data.
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
    """Concrete dependency-free acoustic-feature baseline.

    The analyzer uses the Python standard-library audio API to read PCM WAV files,
    derive a compact feature vector (RMS energy, zero-crossing rate, silence ratio,
    duration, and simple energy distribution), and then classify those features
    according to the assignment's contract.

    The mapping is intentionally conservative: the model does not attempt to infer
    emotion from loudness alone, and the task 9 labels stay within the contract's
    allowed values.
    """

    def analyze(self, audio_path) -> PredictionResult:
        if not audio_path:
            return BaselineAnalyzer().analyze(audio_path)

        if not Path(audio_path).exists():
            return BaselineAnalyzer().analyze(audio_path)

        try:
            features = self._read_wave_features(audio_path)
        except (OSError, EOFError, ValueError):
            return BaselineAnalyzer().analyze(audio_path)

        tone, intensity = self._emotion_detectors(features)
        noise_present, noise_type, noise_severity = self._noise_detectors(features)
        audio_quality = self._quality_detector(features, noise_present, noise_severity)
        overlap_present = self._overlap_detector(features)
        silence_present = self._silence_detector(features)
        confidence = self._confidence(features)

        return PredictionResult(
            emotional_tone=tone,
            emotional_intensity=intensity,
            background_noise_present=noise_present,
            background_noise_type=noise_type,
            background_noise_severity=noise_severity,
            audio_quality=audio_quality,
            speaker_overlap_present=overlap_present,
            long_silence_present=silence_present,
            confidence=confidence,
        )

    def _read_wave_features(self, audio_path):
        """Read a mono/stereo PCM file and derive aggregate acoustic features."""
        with wave.open(str(audio_path), "rb") as wav:
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            channels = wav.getnchannels()
            frame_count = wav.getnframes()
            raw_frames = wav.readframes(frame_count)

        if sample_width == 1:
            sample_bytes = raw_frames
            sample_values = [byte - 128 for byte in sample_bytes]
            samples = self._normalize_8bit(sample_values)
        elif sample_width == 2:
            sample_values = struct.unpack(
                "<" + "h" * (len(raw_frames) // 2), raw_frames
            )
            samples = [value / 32768.0 for value in sample_values]
        elif sample_width == 4:
            sample_values = struct.unpack(
                "<" + "i" * (len(raw_frames) // 4), raw_frames
            )
            samples = [value / 2147483648.0 for value in sample_values]
        else:
            raise ValueError(
                "Unsupported PCM sample width; expected 8, 16 or 32 bit audio"
            )

        if channels > 1:
            downmixed = []
            per_channel = len(samples) // channels
            for idx in range(per_channel):
                value = 0.0
                for channel in range(channels):
                    value += samples[channel * per_channel + idx]
                downmixed.append(value / channels)
            samples = downmixed

        if not samples:
            return {
                "duration": 0.0,
                "sample_rate": sample_rate,
                "rms": 0.0,
                "zcr": 0.0,
                "silence_ratio": 0.0,
                "peak": 0.0,
                "energy_variance": 0.0,
            }

        duration = len(samples) / sample_rate
        rms = self._root_mean_square(samples)
        zcr = self._zero_crossing_rate(samples)
        silence_ratio = self._silence_ratio(samples)
        peak = max(abs(value) for value in samples)
        energy_variance = self._energy_variance(samples)
        low_band_ratio = self._low_band_energy_ratio(samples)

        return {
            "duration": duration,
            "sample_rate": sample_rate,
            "rms": rms,
            "zcr": zcr,
            "silence_ratio": silence_ratio,
            "peak": peak,
            "energy_variance": energy_variance,
            "low_band_ratio": low_band_ratio,
        }

    def _normalize_8bit(self, samples):
        return [value / 128.0 for value in samples]

    def _root_mean_square(self, samples):
        if not samples:
            return 0.0
        return math.sqrt(sum(value * value for value in samples) / len(samples))

    def _zero_crossing_rate(self, samples):
        if len(samples) < 2:
            return 0.0
        crossings = 0
        for previous, current in zip(samples, samples[1:], strict=False):
            if (previous >= 0 and current < 0) or (previous < 0 and current >= 0):
                crossings += 1
        return crossings / (len(samples) - 1)

    def _silence_ratio(self, samples):
        if not samples:
            return 0.0
        threshold = max(0.015, 0.05 * max(abs(value) for value in samples))
        silent = sum(1 for value in samples if abs(value) < threshold)
        return silent / len(samples)

    def _energy_variance(self, samples):
        if not samples:
            return 0.0
        rms = self._root_mean_square(samples)
        return sum((abs(value) - rms) ** 2 for value in samples) / len(samples)

    def _low_band_energy_ratio(self, samples):
        """A cheap proxy for broad spectral distribution in the absence of FFT."""
        if len(samples) < 2:
            return 0.0
        window = max(16, len(samples) // 16)
        windows = []
        for start in range(0, len(samples) - window, window):
            block = samples[start : start + window]
            windows.append(sum(abs(value) for value in block) / len(block))
        if not windows:
            return 0.0
        return sum(windows) / len(windows)

    def _emotion_detectors(self, features):
        """Map broad acoustic layout to task 9 tone and intensity labels."""
        rms = features.get("rms", 0.0)
        zcr = features.get("zcr", 0.0)
        energy_variance = features.get("energy_variance", 0.0)
        duration = features.get("duration", 0.0)

        if rms < 0.02 or duration <= 0.0:
            tone = "neutral"
            intensity = "low"
        elif energy_variance > 0.025 or zcr > 0.20:
            tone = "frustrated"
            intensity = "high"
        elif zcr > 0.12:
            tone = "upset"
            intensity = "medium"
        elif rms > 0.35:
            tone = "satisfied"
            intensity = "high"
        else:
            tone = "neutral"
            intensity = "medium" if rms > 0.11 else "low"

        return tone, intensity

    def _noise_detectors(self, features):
        """Identify obvious noise-like or technical-failure characteristics."""
        silence_ratio = features.get("silence_ratio", 0.0)
        rms = features.get("rms", 0.0)
        zcr = features.get("zcr", 0.0)
        peak = features.get("peak", 0.0)

        noise_present = False
        noise_type = ""
        severity = "low"

        if silence_ratio > 0.55 or features.get("duration", 0.0) <= 0.0:
            noise_present = True
            noise_type = "silence-heavy"
            severity = "medium"
        elif rms < 0.03 and peak < 0.05:
            noise_present = True
            noise_type = "low-energy signal"
            severity = "high"
        elif zcr > 0.18:
            noise_present = True
            noise_type = "spectral / high-activity noise"
            severity = "medium"
        elif rms > 0.30:
            noise_present = False
            noise_type = ""
            severity = "low"

        return noise_present, noise_type, severity

    def _quality_detector(self, features, noise_present, noise_severity):
        if noise_present or noise_severity == "high":
            return "poor"
        if noise_severity == "medium":
            return "noisy"
        return "clear"

    def _overlap_detector(self, features):
        """A conservative overlap hint in a single-channel baseline.

        Speaker overlap is not directly recoverable from a single-stream waveform
        without multi-channel sources, so the baseline reports overlap only when
        the signal exhibits high-energy contention that looks like a multi-speaker
        blend and the frame variance is not calm.
        """
        rms = features.get("rms", 0.0)
        energy_variance = features.get("energy_variance", 0.0)
        zcr = features.get("zcr", 0.0)
        if rms > 0.36 and (energy_variance > 0.04 or zcr > 0.16):
            return True
        return False

    def _silence_detector(self, features):
        return features.get("silence_ratio", 0.0) > 0.55

    def _confidence(self, features):
        """Confidence escalates when the signal is measurable and stable."""
        duration = features.get("duration", 0.0)
        if duration <= 0:
            return 0.15
        rms = features.get("rms", 0.0)
        ratio = features.get("silence_ratio", 0.0)
        quality = 0.45 + min(0.35, max(0.0, rms) * 0.70)
        penalty = 0.25 if ratio > 0.55 else 0.0
        return min(0.95, max(0.35, quality - penalty))


class FoundationModelAnalyzer(AudioAnalyzer):
    """A future foundation-model adapter.

    The contract stays stable: the analyzer simply returns a PredictionResult.
    """

    def analyze(self, audio_path) -> PredictionResult:
        return AcousticAnalyzer().analyze(audio_path)
