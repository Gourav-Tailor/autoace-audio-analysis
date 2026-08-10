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
