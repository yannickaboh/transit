# payment/views.py
from rest_framework import viewsets
from .models import JournalAudit
from .serializers import JournalAuditSerializer

from rest_framework.permissions import IsAuthenticated


class JournalAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """Consultation des logs d'audit (Lecture Seule, Admin seul)."""
    queryset = JournalAudit.objects.all().order_by('-date_heure')
    serializer_class = JournalAuditSerializer
    permission_classes = [IsAuthenticated]