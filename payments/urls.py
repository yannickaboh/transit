# payments/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionPaiementViewSet

router = DefaultRouter()
router.register('transactions', TransactionPaiementViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]

# Les URLs générées seront de la forme :
# /api/v1/transactions/
# /api/v1/audit-logs/ (Lecture Seule)