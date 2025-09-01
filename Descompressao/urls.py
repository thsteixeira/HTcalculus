from django.urls import path
from .views import descompressao_view

urlpatterns = [
    path('', descompressao_view, name='descompressao'),
]