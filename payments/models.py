from django.db import models
from users.models import Utilisateur 
from logistics.models import Colis 
import uuid

# --- 1. Transaction de Paiement ---

class TransactionPaiement(models.Model):
    """Enregistrement de tous les frais et paiements associés à un colis."""
    STATUT_PAIEMENT_CHOICES = [
        ('EN_ATTENTE', 'En Attente'),
        ('REUSSI', 'Réussi'),
        ('ECHOUE', 'Échoué'),
        ('REMBOURSE', 'Remboursé')
    ]
    
    TYPE_FRAIS_CHOICES = [
        ('MANUTENTION', 'Manutention Portuaire'),
        ('DOUANE', 'Frais de Douane'),
        ('STOCKAGE', 'Frais de Stockage/Magasinage'),
        ('AUTRES', 'Autres Frais')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    colis = models.ForeignKey(Colis, on_delete=models.PROTECT, related_name='transactions')
    utilisateur_payeur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='paiements_effectues')
    
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2) # Taux inclus
    type_frais = models.CharField(max_length=50, choices=TYPE_FRAIS_CHOICES)
    
    statut_paiement = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='EN_ATTENTE')
    mode_paiement = models.CharField(max_length=50, blank=True)
    reference_externe = models.CharField(max_length=255, blank=True, help_text="ID de transaction de la passerelle de paiement")
    date_heure_paiement = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transaction de Paiement"
        verbose_name_plural = "Transactions de Paiement"

