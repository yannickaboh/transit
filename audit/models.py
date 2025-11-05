from django.db import models
from users.models import Utilisateur 
from logistics.models import Colis 
import uuid

# Create your models here.


# --- 2. Journal d'Audit (Sécurité/Conformité ISO 27001) ---

class JournalAudit(models.Model):
    """Log de toutes les actions critiques pour la traçabilité et l'audit."""
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50, verbose_name="Type d'Action (LOGIN_SUCCESS, MODIF_STATUT, etc.)")
    ressource_affectee = models.CharField(max_length=100, verbose_name="Nom de l'Entité Modifiée/Consultée")
    ressource_id = models.CharField(max_length=36, blank=True, verbose_name="UUID ou PK de la Ressource")
    date_heure = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField(verbose_name="Adresse IP")
    details = models.TextField(blank=True, verbose_name="Détails (Anciennes/Nouvelles Valeurs, Erreurs)")

    class Meta:
        verbose_name = "Journal d'Audit"
        verbose_name_plural = "Journaux d'Audit"
        ordering = ['-date_heure']
