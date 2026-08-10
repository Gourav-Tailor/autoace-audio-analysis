import csv
import json
import zipfile
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.utils import timezone

from .analyzers import BaselineAnalyzer
from .models import AudioFile, Batch, Prediction
from .prediction_contract import PredictionResult

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


class BatchValidationError(ValueError):
    pass


class BatchUploadService:
    def __init__(self, upload_file):
        self.upload_file = upload_file
        self.extract_dir = None
        self.zip_path = None

    def save(self):
        upload_dir = Path(settings.BASE_DIR) / "storage" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        target_name = Path(self.upload_file.name).name
        target = upload_dir / target_name

        with target.open("wb") as destination:
            for chunk in self.upload_file.chunks():
                destination.write(chunk)

        if not zipfile.is_zipfile(target):
            raise ValueError("Uploaded batch must be a valid ZIP archive")

        extract_dir = upload_dir / f"{Path(target_name).stem}_{uuid4().hex}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(target, "r") as archive:
            archive.extractall(extract_dir)

        self.extract_dir = extract_dir
        self.zip_path = target
        return target

    def read_manifest(self):
        if self.extract_dir is None:
            return []

        manifest_path = self.extract_dir / "labels.csv"
        if not manifest_path.exists():
            return []

        with manifest_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader)

    def audio_filenames_from_manifest(self):
        rows = self.read_manifest()
        filenames = []
        for row in rows:
            filename = row.get("name") or row.get("filename") or row.get("file_name")
            if filename:
                filenames.append(str(Path(filename).name))
        return filenames


class BatchProcessor:
    def __init__(self, batch, upload_service=None, analyzer=None):
        self.batch = batch
        self.service = upload_service
        self.analyzer = analyzer or BaselineAnalyzer()
        self.manifest = []
        self.audio_files = []
        self.extract_dir = None if self.service is None else self.service.extract_dir

    def process(self):
        validation = self.validate_batch()
        created_count = self.extract_files()
        self.save_predictions(validation["manifest"])
        self.update_progress(created_count)
        return {
            "manifest_rows": len(validation["manifest"]),
            "audio_files_created": created_count,
        }

    def validate_batch(self):
        if self.service.extract_dir is None:
            raise BatchValidationError("Batch archive was not extracted")

        extract_dir = self.service.extract_dir
        labels_path = extract_dir / "labels.csv"
        if not labels_path.exists():
            raise BatchValidationError("labels.csv is required in the ZIP")

        with labels_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise BatchValidationError("labels.csv is empty or malformed")

            normalized_headers = {
                header.strip().lower() for header in reader.fieldnames
            }
            if (
                "name" not in normalized_headers
                and "filename" not in normalized_headers
            ):
                raise BatchValidationError("labels.csv must include a name column")

            manifest = list(reader)

        if "result_json" in {header.strip().lower() for header in reader.fieldnames}:
            for row in manifest:
                result_value = row.get("result_json") or row.get("result-json")
                if result_value:
                    try:
                        json.loads(result_value)
                    except json.JSONDecodeError as exc:
                        raise BatchValidationError(
                            "result_json is not valid JSON in labels.csv"
                        ) from exc

        if not manifest:
            raise BatchValidationError("labels.csv has no rows to validate")

        archive_files = []
        unsupported_files = []
        for path in extract_dir.rglob("*"):
            if path.is_file():
                relative_name = path.relative_to(extract_dir).as_posix()
                if relative_name == "labels.csv":
                    continue
                suffix = path.suffix.lower()
                if suffix in SUPPORTED_AUDIO_EXTENSIONS:
                    archive_files.append(path.name)
                else:
                    unsupported_files.append(relative_name)

        if unsupported_files:
            raise BatchValidationError(
                "Unsupported files found in ZIP: " + ", ".join(unsupported_files)
            )

        csv_names = []
        duplicates = []
        seen = set()
        for row in manifest:
            name = row.get("name") or row.get("filename")
            if not name:
                raise BatchValidationError("labels.csv row is missing a name value")
            normalized_name = str(Path(name).name).strip()
            if not normalized_name:
                raise BatchValidationError("labels.csv row name cannot be blank")
            if normalized_name in seen:
                duplicates.append(normalized_name)
            seen.add(normalized_name)
            csv_names.append(normalized_name)

        if duplicates:
            raise BatchValidationError(
                "Duplicate filenames found in labels.csv: " + ", ".join(duplicates)
            )

        missing_from_archive = [name for name in csv_names if name not in archive_files]
        if missing_from_archive:
            raise BatchValidationError(
                "CSV references missing audio files: " + ", ".join(missing_from_archive)
            )

        missing_from_csv = [name for name in archive_files if name not in csv_names]
        if missing_from_csv:
            raise BatchValidationError(
                "Audio files are not represented in labels.csv: "
                + ", ".join(missing_from_csv)
            )

        self.manifest = manifest
        self.audio_files = archive_files
        return {"manifest": manifest, "audio_files": archive_files}

    def extract_files(self):
        created_count = 0
        for filename in self.audio_files:
            file_path = self.service.extract_dir / filename
            if file_path.exists():
                AudioFile.objects.create(
                    batch=self.batch,
                    filename=filename,
                    file_path=str(file_path),
                    status=AudioFile.STATUS_PENDING,
                )
                created_count += 1
        return created_count

    def save_predictions(self, manifest):
        for row in manifest:
            filename = row.get("name") or row.get("filename")
            if not filename:
                continue
            normalized_name = str(Path(filename).name)
            audio_file = AudioFile.objects.filter(
                batch=self.batch, filename=normalized_name
            ).first()
            if audio_file is None:
                continue
            if "result_json" in row and str(row.get("result_json") or "").strip():
                payload = json.loads(row.get("result_json"))
                if not payload:
                    continue
                result = PredictionResult(**payload)
                Prediction.objects.update_or_create(
                    audio_file=audio_file,
                    defaults={
                        "emotional_tone": result.emotional_tone,
                        "emotional_intensity": result.emotional_intensity,
                        "background_noise_present": result.background_noise_present,
                        "background_noise_type": result.background_noise_type,
                        "background_noise_severity": result.background_noise_severity,
                        "audio_quality": result.audio_quality,
                        "speaker_overlap_present": result.speaker_overlap_present,
                        "long_silence_present": result.long_silence_present,
                        "confidence": result.confidence,
                    },
                )

    def process_audio(self):
        self.batch.status = Batch.STATUS_PROCESSING
        self.batch.started_at = timezone.now()
        self.batch.save(update_fields=["status", "started_at"])

        failed_count = 0
        for audio_file in AudioFile.objects.filter(batch=self.batch):
            audio_file.status = AudioFile.STATUS_PROCESSING
            audio_file.save(update_fields=["status"])

            try:
                result = self.analyzer.analyze(audio_file.file_path)
                Prediction.objects.update_or_create(
                    audio_file=audio_file,
                    defaults={
                        "emotional_tone": result.emotional_tone,
                        "emotional_intensity": result.emotional_intensity,
                        "background_noise_present": result.background_noise_present,
                        "background_noise_type": result.background_noise_type,
                        "background_noise_severity": result.background_noise_severity,
                        "audio_quality": result.audio_quality,
                        "speaker_overlap_present": result.speaker_overlap_present,
                        "long_silence_present": result.long_silence_present,
                        "confidence": result.confidence,
                    },
                )
                audio_file.status = AudioFile.STATUS_COMPLETED
                audio_file.processed_at = timezone.now()
                audio_file.error_message = ""
                audio_file.save(
                    update_fields=["status", "processed_at", "error_message"]
                )
            except Exception as exc:
                failed_count += 1
                audio_file.status = AudioFile.STATUS_FAILED
                audio_file.error_message = str(exc)[:500]
                audio_file.save(update_fields=["status", "error_message"])

        processed = AudioFile.objects.filter(
            batch=self.batch, status=AudioFile.STATUS_COMPLETED
        ).count()
        if failed_count:
            self.batch.status = Batch.STATUS_FAILED
        else:
            self.batch.status = Batch.STATUS_COMPLETED
        self.batch.processed_files = processed
        self.batch.failed_files = failed_count
        self.batch.completed_at = timezone.now()
        self.batch.save(
            update_fields=[
                "status",
                "processed_files",
                "failed_files",
                "completed_at",
            ]
        )
        return {
            "batch_id": self.batch.id,
            "processed_files": processed,
            "failed_files": failed_count,
        }

    def update_progress(self, created_count):
        self.batch.total_files = created_count
        self.batch.processed_files = created_count
        self.batch.failed_files = 0
        self.batch.status = Batch.STATUS_UPLOADED
        self.batch.save(
            update_fields=[
                "total_files",
                "processed_files",
                "failed_files",
                "status",
            ]
        )
