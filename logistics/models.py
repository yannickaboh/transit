from django.db import models
from users.models import Utilisateur # Importation de l'utilisateur personnalisé
import uuid

# --- 1. Colis (Le cœur de l'application) ---

class Colis(models.Model):
    """Représente la marchandise physique à gérer au port."""
    STATUT_CHOICES = [
        ('EN_ATTENTE_DECHARGE', 'En Attente de Déchargement'),
        ('EN_TRANSIT', 'En Transit'),
        ('DEDOUANEMENT', 'En Dédouanement'),
        ('PRET_RETRAIT', 'Prêt au Retrait'),
        ('LIVRE', 'Livré/Retiré'),
        ('LITIGE', 'Litige/Problème')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID Unique Colis")
    numero_bl = models.CharField(max_length=150, unique=True, verbose_name="Numéro de B/L (Bill of Lading)")
    description = models.TextField(verbose_name="Description de la Marchandise")
    poids_kg = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="Poids (kg)")
    dimensions = models.CharField(max_length=200, blank=True, verbose_name="Dimensions (L x l x H)")
    
    date_arrivee = models.DateTimeField(auto_now_add=True, verbose_name="Date d'Arrivée au Port")
    client = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='colis_client', verbose_name="Client Propriétaire")
    
    lieu_stockage = models.CharField(max_length=100, blank=True, verbose_name="Localisation Physique Actuelle")
    statut_actuel = models.CharField(max_length=30, choices=STATUT_CHOICES, default='EN_ATTENTE_DECHARGE', verbose_name="Statut Actuel")

    class Meta:
        verbose_name = "Colis"
        verbose_name_plural = "Colis"

    def __str__(self):
        return str(self.id)

# --- 2. Suivi de Statut (Historique) ---

class SuiviStatut(models.Model):
    """Historique des mouvements et des changements de statut d'un colis."""
    colis = models.ForeignKey(Colis, on_delete=models.CASCADE, related_name='historique_statuts')
    statut = models.CharField(max_length=30, choices=Colis.STATUT_CHOICES, verbose_name="Statut Enregistré")
    localisation = models.CharField(max_length=255, blank=True, verbose_name="Localisation (GPS/Zone)")
    date_heure = models.DateTimeField(auto_now_add=True)
    agent_operationnel = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='operations_effectuees')
    notes = models.TextField(blank=True, verbose_name="Notes Opérationnelles")

    class Meta:
        verbose_name = "Suivi de Statut"
        verbose_name_plural = "Suivis de Statut"
        ordering = ['-date_heure']

# --- 3. Retrait Sécurisé ---

class RetraitColis(models.Model):
    """Enregistrement final et sécurisé de la livraison au client."""
    colis = models.OneToOneField(Colis, on_delete=models.CASCADE, related_name='retrait_final')
    date_heure_retrait = models.DateTimeField(auto_now_add=True)
    agent_validation = models.ForeignKey(Utilisateur, on_delete=models.PROTECT, related_name='validation_retraits')
    
    # Sécurité/Preuve
    preuve_identite_url = models.URLField(max_length=500, verbose_name="Lien vers Preuve d'Identité Chiffrée")
    signature_client = models.TextField(verbose_name="Signature Électronique (Base64)", help_text="Signature enregistrée du client ou de son mandataire.")
    
    class Meta:
        verbose_name = "Retrait de Colis"
        verbose_name_plural = "Retraits de Colis"