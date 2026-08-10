from rest_framework import serializers

from .models import AudioFile, Batch, Prediction


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
