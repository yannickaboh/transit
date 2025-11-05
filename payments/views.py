# payment/views.py
from rest_framework import viewsets
from .models import TransactionPaiement
from .serializers import TransactionPaiementSerializer

from rest_framework.permissions import IsAuthenticated

class TransactionPaiementViewSet(viewsets.ModelViewSet):
    queryset = TransactionPaiement.objects.all()
    serializer_class = TransactionPaiementSerializer
    permission_classes = [IsAuthenticated]
    # Nécessite des permissions pour initier/confirmer