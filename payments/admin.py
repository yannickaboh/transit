# payments/admin.py

from django.contrib import admin
from .models import TransactionPaiement

@admin.register(TransactionPaiement)
class TransactionPaiementAdmin(admin.ModelAdmin):
    list_display = ('id', 'colis', 'utilisateur_payeur', 'montant_total', 'type_frais', 'statut_paiement', 'date_heure_paiement')
    list_filter = ('statut_paiement', 'type_frais', 'date_heure_paiement')
    search_fields = ('colis__numero_bl', 'utilisateur_payeur__email', 'reference_externe')
    readonly_fields = ('date_heure_paiement', 'colis', 'utilisateur_payeur') # Rendre les FK non modifiables après création
    date_hierarchy = 'date_heure_paiement'