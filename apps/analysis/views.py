from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AudioFile, Batch, Prediction
from .serializers import BatchSerializer, PredictionSerializer


class BatchListView(generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


@api_view(["GET"])
def prediction_json(request):
    prediction = Prediction.objects.select_related("audio_file").first()
    serializer = PredictionSerializer(prediction) if prediction else None
    return Response(serializer.data if serializer else {})


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
