from rest_framework import serializers

from .models import AudioFile, Batch, Prediction
from .prediction_contract import PredictionResult


class PredictionContractSerializer(serializers.Serializer):
    emotional_tone = serializers.ChoiceField(
        choices=["neutral", "satisfied", "frustrated", "upset", "distressed"]
    )
    emotional_intensity = serializers.ChoiceField(choices=["low", "medium", "high"])
    background_noise_present = serializers.BooleanField()
    background_noise_type = serializers.CharField(allow_blank=True, required=False)
    background_noise_severity = serializers.ChoiceField(
        choices=[
            "low",
            "medium",
            "high",
        ]
    )
    audio_quality = serializers.ChoiceField(
        choices=["clear", "slightly_impaired", "severely_impaired"]
    )
    speaker_overlap_present = serializers.BooleanField()
    long_silence_present = serializers.BooleanField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)

    def create(self, validated_data):
        return PredictionResult(**validated_data)


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = [
            "id",
            "name",
            "status",
            "uploaded_at",
            "started_at",
            "completed_at",
            "total_files",
            "processed_files",
            "failed_files",
        ]


class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = [
            "id",
            "batch",
            "filename",
            "file_path",
            "status",
            "error_message",
            "duration",
            "processed_at",
        ]


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            "id",
            "audio_file",
            "emotional_tone",
            "emotional_intensity",
            "background_noise_present",
            "background_noise_type",
            "background_noise_severity",
            "audio_quality",
            "speaker_overlap_present",
            "long_silence_present",
            "confidence",
        ]
