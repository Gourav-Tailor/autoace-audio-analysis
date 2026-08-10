from apps.analysis.prediction_contract import PredictionResult


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
