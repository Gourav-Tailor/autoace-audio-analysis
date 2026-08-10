from django.db import models


class Batch(models.Model):
    STATUS_UPLOADED = "UPLOADED"
    STATUS_VALIDATING = "VALIDATING"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_UPLOADED, "Uploaded"),
        (STATUS_VALIDATING, "Validating"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=24, choices=STATUS_CHOICES, default=STATUS_UPLOADED
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    total_files = models.PositiveIntegerField(default=0)
    processed_files = models.PositiveIntegerField(default=0)
    failed_files = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name


class AudioFile(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    batch = models.ForeignKey(
        Batch, related_name="audio_files", on_delete=models.CASCADE
    )
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    status = models.CharField(
        max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    error_message = models.TextField(blank=True, default="")
    duration = models.FloatField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["filename"]

    def __str__(self):
        return self.filename


class Prediction(models.Model):
    audio_file = models.OneToOneField(
        AudioFile, related_name="prediction", on_delete=models.CASCADE
    )
    emotional_tone = models.CharField(max_length=128, blank=True, default="")
    emotional_intensity = models.CharField(max_length=128, blank=True, default="")
    background_noise_present = models.BooleanField(default=False)
    background_noise_type = models.CharField(max_length=128, blank=True, default="")
    background_noise_severity = models.CharField(max_length=128, blank=True, default="")
    audio_quality = models.CharField(max_length=128, blank=True, default="")
    speaker_overlap_present = models.BooleanField(default=False)
    long_silence_present = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)

    def __str__(self):
        return f"Prediction for {self.audio_file.filename}"
