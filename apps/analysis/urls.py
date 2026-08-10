from django.urls import path

from .views import (
    BatchDetailView,
    BatchListView,
    BatchUploadView,
    dashboard,
    prediction_contract,
    prediction_json,
)

urlpatterns = [
    path("batches/", BatchListView.as_view(), name="batch-list"),
    path("batches/<int:pk>/", BatchDetailView.as_view(), name="batch-detail"),
    path("batches/upload/", BatchUploadView.as_view(), name="batch-upload"),
    path("dashboard/", dashboard, name="dashboard"),
    path("prediction-json/", prediction_json, name="prediction-json"),
    path("prediction-contract/", prediction_contract, name="prediction-contract"),
]
