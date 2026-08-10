import struct
import wave
from pathlib import Path

from apps.analysis.analyzers import AcousticAnalyzer, AudioAnalyzer, BaselineAnalyzer
from apps.analysis.prediction_contract import PredictionResult


def test_audio_analyzer_contract_exists_and_is_abstract():
    assert issubclass(AudioAnalyzer, object)
    assert AudioAnalyzer.__abstractmethods__


def test_baseline_analyzer_returns_prediction_contract():
    analyzer = BaselineAnalyzer()
    result = analyzer.analyze(Path("audio.wav"))
    assert isinstance(result, PredictionResult)
    assert result.to_dict()["confidence"] >= 0.0


def test_acoustic_analyzer_is_a_concrete_audio_analyzer():
    analyzer = AcousticAnalyzer()
    assert isinstance(analyzer, AudioAnalyzer)
    result = analyzer.analyze(Path("audio.wav"))
    assert isinstance(result, PredictionResult)


def test_prediction_result_accepts_valid_payload():
    result = PredictionResult(
        emotional_tone="frustrated",
        emotional_intensity="medium",
        background_noise_present=True,
        background_noise_type="office chatter",
        background_noise_severity="low",
        audio_quality="clear",
        speaker_overlap_present=False,
        long_silence_present=False,
        confidence=0.82,
    )

    assert result.emotional_tone == "frustrated"
    assert 0.0 <= result.confidence <= 1.0


def test_prediction_result_rejects_invalid_tone():
    try:
        PredictionResult(
            emotional_tone="angry",
            emotional_intensity="medium",
            background_noise_present=False,
            background_noise_type="",
            background_noise_severity="low",
            audio_quality="clear",
            speaker_overlap_present=False,
            long_silence_present=False,
            confidence=0.5,
        )
    except ValueError as exc:
        assert "emotional_tone" in str(exc)
    else:
        raise AssertionError("Invalid tone should have raised ValueError")


def test_acoustic_analyzer_reads_wave_and_emits_valid_prediction(tmp_path):
    audio_path = tmp_path / "baseline.wav"

    sample_rate = 16000
    duration_seconds = 0.25
    frames = int(sample_rate * duration_seconds)

    with wave.open(str(audio_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(frames):
            amplitude = 0.25 * (i % 16000) / sample_rate
            value = int(32767 * max(-1.0, min(1.0, amplitude)))
            wav.writeframes(struct.pack("<h", value))

    result = AcousticAnalyzer().analyze(audio_path)

    assert isinstance(result, PredictionResult)
    assert result.emotional_tone in {
        "neutral",
        "satisfied",
        "frustrated",
        "upset",
        "distressed",
    }
    assert result.emotional_intensity in {"low", "medium", "high"}
    assert result.audio_quality in {"clear", "noisy", "poor"}
    assert 0.0 <= result.confidence <= 1.0
