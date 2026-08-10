import csv
import zipfile
from pathlib import Path

from django.conf import settings


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

        extract_dir = upload_dir / Path(target_name).stem
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
            filename = row.get("filename") or row.get("file_name") or row.get("audio")
            if filename:
                filenames.append(str(Path(filename).name))
        return filenames
