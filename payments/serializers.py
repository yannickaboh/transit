# payment/serializers.py
from rest_framework import serializers
from .models import TransactionPaiement

class TransactionPaiementSerializer(serializers.ModelSerializer):
    colis_id = serializers.CharField(source='colis.id', read_only=True)
    
    class Meta:
        model = TransactionPaiement
        fields = '__all__'
        read_only_fields = ('date_heure_paiement',)


