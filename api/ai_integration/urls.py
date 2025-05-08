from django.urls import path
from . import  views as ai_views

urlpatterns = [
    path('upload-dataset/', ai_views.upload_fine_tuned_dataset, name='upload_fine_tuned_dataset'),
]
