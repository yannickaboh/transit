# logistics/admin.py

from django.contrib import admin
from .models import Colis, SuiviStatut, RetraitColis

# --- Inlines (Pour afficher les relations dans le parent) ---

class SuiviStatutInline(admin.StackedInline):
    # Affiche le suivi statut sur la page du Colis
    model = SuiviStatut
    extra = 1 # Affiche un formulaire vide pour en ajouter un
    readonly_fields = ('date_heure', 'agent_operationnel')
    
    def get_formset(self, request, obj=None, **kwargs):
        # Permet de pré-remplir l'agent opérationnel
        formset = super().get_formset(request, obj, **kwargs)
        # Surcharge le queryset si nécessaire (ex: ne montrer que les agents)
        return formset

class RetraitColisInline(admin.StackedInline):
    # Affiche le retrait sur la page du Colis (OneToOne, donc max_num=1)
    model = RetraitColis
    max_num = 1
    can_delete = False
    readonly_fields = ('date_heure_retrait', 'agent_validation', 'preuve_identite_url', 'signature_client')

# --- Custom Admin pour Colis ---

@admin.register(Colis)
class ColisAdmin(admin.ModelAdmin):
    list_display = ('numero_bl', 'client', 'statut_actuel', 'poids_kg', 'date_arrivee')
    list_filter = ('statut_actuel', 'date_arrivee', 'client__role')
    search_fields = ('numero_bl', 'description', 'client__email', 'client__nom')
    readonly_fields = ('date_arrivee',)
    inlines = [SuiviStatutInline, RetraitColisInline]
    
    # Action pour mettre à jour le statut en masse
    @admin.action(description='Marquer comme Prêt au Retrait')
    def make_ready_for_pickup(self, request, queryset):
        queryset.update(statut_actuel='PRET_RETRAIT')
        self.message_user(request, f"{queryset.count()} colis marqués Prêt au Retrait.")

    actions = [make_ready_for_pickup]

@admin.register(SuiviStatut)
class SuiviStatutAdmin(admin.ModelAdmin):
    list_display = ('colis', 'statut', 'localisation', 'agent_operationnel', 'date_heure')
    list_filter = ('statut', 'agent_operationnel')
    search_fields = ('colis__numero_bl', 'notes')
    date_hierarchy = 'date_heure'

# RetraitColis peut être géré via l'Inline, mais si vous voulez une vue liste :
@admin.register(RetraitColis)
class RetraitColisAdmin(admin.ModelAdmin):
    list_display = ('colis', 'agent_validation', 'date_heure_retrait')
    search_fields = ('colis__numero_bl',)
    readonly_fields = ('colis', 'date_heure_retrait', 'agent_validation', 'preuve_identite_url', 'signature_client')