from django.urls import path
from .views import (
    vencimento_view,
    validate_professor_ajax,
    vencimento_preview_ajax,
)

urlpatterns = [
    path('', vencimento_view, name='vencimento'),
    path('ajax/validate-professor/', validate_professor_ajax, name='validate_professor'),
    path('ajax/vencimento-preview/', vencimento_preview_ajax, name='vencimento_preview'),
]