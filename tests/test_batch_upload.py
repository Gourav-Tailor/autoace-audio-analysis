import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.analysis.models import Batch

pytestmark = pytest.mark.django_db


def test_batch_upload_accepts_zip_file():
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("call_001.wav", b"audio")
        archive.writestr("labels.csv", "filename,label\ncall_001.wav,neutral\n")

    archive_buffer.seek(0)
    response = APIClient().post(
        "/batches/upload/",
        {
            "file": SimpleUploadedFile(
                "evaluation_batch.zip",
                archive_buffer.getvalue(),
                content_type="application/zip",
            )
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert Batch.objects.filter(name="evaluation_batch.zip").exists()


def test_batch_upload_parses_manifest_and_creates_audio_rows():
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("call_001.wav", b"audio")
        archive.writestr("call_002.wav", b"audio")
        archive.writestr(
            "labels.csv",
            "filename,label\ncall_001.wav,neutral\ncall_002.wav,satisfied\n",
        )

    archive_buffer.seek(0)
    response = APIClient().post(
        "/batches/upload/",
        {
            "file": SimpleUploadedFile(
                "evaluation_batch.zip",
                archive_buffer.getvalue(),
                content_type="application/zip",
            )
        },
        format="multipart",
    )

    assert response.status_code == 201
    batch = Batch.objects.get(name="evaluation_batch.zip")
    assert batch.audio_files.count() == 2
    assert batch.audio_files.filter(filename="call_001.wav").exists()
    assert batch.audio_files.filter(filename="call_002.wav").exists()
