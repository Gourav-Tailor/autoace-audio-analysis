from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AudioFile, Batch, Prediction
from .prediction_contract import PredictionResult
from .serializers import (
    BatchSerializer,
    PredictionContractSerializer,
    PredictionSerializer,
)
from .upload_handlers import BatchUploadService


class BatchListView(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BatchUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        upload = request.FILES.get("file") or request.FILES.get("evaluation_batch")
        if not upload:
            return Response({"error": "No zip upload provided"}, status=400)

        if not upload.name.lower().endswith(".zip"):
            return Response({"error": "Only .zip uploads are accepted"}, status=400)

        service = BatchUploadService(upload)
        saved_path = service.save()

        batch = Batch.objects.create(
            name=upload.name,
            status=Batch.STATUS_VALIDATING,
            total_files=0,
            processed_files=0,
            failed_files=0,
        )

        manifest_rows = service.read_manifest()
        audio_filenames = service.audio_filenames_from_manifest()
        created_count = 0

        for filename in audio_filenames:
            file_path = service.extract_dir / filename
            if file_path.exists():
                AudioFile.objects.create(
                    batch=batch,
                    filename=filename,
                    file_path=str(file_path),
                    status=AudioFile.STATUS_PENDING,
                )
                created_count += 1

        batch.total_files = created_count
        batch.status = Batch.STATUS_UPLOADED if created_count else Batch.STATUS_FAILED
        batch.save(update_fields=["total_files", "status"])

        return Response(
            {
                "message": "Batch upload stored",
                "batch_id": batch.id,
                "stored_path": str(saved_path),
                "audio_files_created": created_count,
                "manifest_rows": len(manifest_rows),
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET"])
def prediction_json(request):
    prediction = Prediction.objects.select_related("audio_file").first()
    serializer = PredictionSerializer(prediction) if prediction else None
    return Response(serializer.data if serializer else {})


@api_view(["POST"])
def prediction_contract(request):
    serializer = PredictionContractSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = PredictionResult(**serializer.validated_data)
    return Response(result.to_dict())


def dashboard(request):
    batches = Batch.objects.prefetch_related("audio_files").all()
    audio_files = AudioFile.objects.select_related("batch").all()
    predictions = Prediction.objects.select_related("audio_file").all()
    context = {
        "batches": batches,
        "audio_files": audio_files,
        "predictions": predictions,
    }
    return render(request, "analysis/dashboard.html", context)
