from django.contrib import admin

from .models import AudioFile, Batch, Prediction


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "uploaded_at",
        "total_files",
        "processed_files",
        "failed_files",
    )
    list_filter = ("status", "uploaded_at")
    search_fields = ("name",)


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ("filename", "batch", "status", "duration", "processed_at")
    list_filter = ("status", "batch")
    search_fields = ("filename",)


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "audio_file",
        "emotional_tone",
        "emotional_intensity",
        "confidence",
    )
    search_fields = ("audio_file__filename",)
