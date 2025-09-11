from django.urls import path
from .views import vencimento_view

urlpatterns = [
    path('', vencimento_view, name='vencimento'),
]