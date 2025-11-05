# audit/admin.py

from django.contrib import admin
from .models import JournalAudit

@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ('date_heure', 'utilisateur', 'action_type', 'ressource_affectee', 'ressource_id', 'adresse_ip')
    list_filter = ('action_type', 'ressource_affectee')
    search_fields = ('utilisateur__email', 'details', 'ressource_id', 'adresse_ip')
    # Rendre TOUS les champs en lecture seule pour assurer la conformité de l'audit
    readonly_fields = ('utilisateur', 'action_type', 'ressource_affectee', 'ressource_id', 
                       'date_heure', 'adresse_ip', 'details')
    
    # Interdire l'ajout et la suppression via l'interface Admin
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

    date_hierarchy = 'date_heure'