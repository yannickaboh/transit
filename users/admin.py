# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Role, Permission
from django.utils.translation import gettext_lazy as _

# --- Custom Admin pour Utilisateur ---

class CustomUserAdmin(UserAdmin):
    # 1. RETIRER 'username' DE LA LISTE DE CHAMPS PAR DÉFAUT DE UserAdmin
    # Ces listes doivent remplacer celles de UserAdmin pour éviter les champs inutiles.
    
    # Affiche les champs de l'utilisateur dans la liste
    # On enlève 'username' (qui n'existe plus)
    list_display = ('email', 'nom', 'prenoms', 'telephone', 'role', 'is_staff', 'is_active', 'deux_facteurs_actif')
    
    # Permet de filtrer par ces champs
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role', 'deux_facteurs_actif')
    
    # Permet de rechercher par ces champs
    # On enlève 'username'
    search_fields = ('email', 'nom', 'prenoms', 'telephone')
    
    # Définition des sections dans le formulaire de modification/création
    fieldsets = (
        # Section d'identification, doit utiliser 'email' et non 'username'
        (None, {'fields': ('email', 'password')}), 
        
        (_('Informations Personnelles'), {'fields': ('nom', 'prenoms', 'telephone', 'role')}),
        
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        
        # Le champ 'code_secret_reset' devrait être en lecture seule
        (_('Sécurité'), {
            'fields': ('deux_facteurs_actif', 'code_secret_reset', 'code_secret_reset_expiration'),
            'classes': ('collapse',), # Optionnel : Masque cette section par défaut
        }),
        
        (_('Dates Importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # 2. Champs en LECTURE SEULE
    # Empêche la modification directe des champs de réinitialisation et des dates
    readonly_fields = ('last_login', 'date_joined', 'code_secret_reset', 'code_secret_reset_expiration')
    
    # Les champs qui ne sont pas inclus dans fieldsets mais sont nécessaires
    ordering = ('email',)
    
    filter_horizontal = ('groups', 'user_permissions',) # <--- À VÉRIFIER
    

# --- Autres Modèles (Aucune modification requise, ils sont déjà optimisés) ---

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_role', 'description')
    search_fields = ('nom_role',)
    filter_horizontal = ('permissions',) # Permet une interface agréable pour gérer les ManyToMany

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code_permission', 'libelle')
    search_fields = ('code_permission', 'libelle')

# Enregistrement de l'utilisateur personnalisé
admin.site.register(Utilisateur, CustomUserAdmin)