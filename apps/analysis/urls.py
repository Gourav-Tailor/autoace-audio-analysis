from django.urls import path

from .views import BatchDetailView, BatchListView, dashboard, prediction_json

urlpatterns = [
    path("batches/", BatchListView.as_view(), name="batch-list"),
    path("batches/<int:pk>/", BatchDetailView.as_view(), name="batch-detail"),
    path("dashboard/", dashboard, name="dashboard"),
    path("prediction-json/", prediction_json, name="prediction-json"),
]
