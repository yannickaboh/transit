# payment/serializers.py
from rest_framework import serializers
from .models import JournalAudit

class JournalAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalAudit
        fields = '__all__'
        read_only_fields = ('date_heure',)