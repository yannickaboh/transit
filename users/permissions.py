# users/permissions.py

from rest_framework import permissions

# ⚠️ NOUVELLE FONCTION FACTORY ⚠️
def HasPermission(required_permission_code):
    
    class HasRequiredPermission(permissions.BasePermission):
        """
        Permission personnalisée générée pour vérifier un code spécifique.
        """
        
        def has_permission(self, request, view):
            # 1. Bypass pour l'Admin/Superuser
            if request.user.is_superuser or request.user.is_staff:
                return True
                
            # 2. Utilisateur non authentifié (devrait être géré par IsAuthenticated)
            if not request.user or not request.user.is_authenticated:
                return False

            # 3. Vérification de la permission RBAC
            # Supposons que votre modèle Utilisateur a un Role et que le Role a des Permissions
            
            # Exemple : Vérifie si la permission est associée au rôle de l'utilisateur
            # (Cette ligne doit correspondre à la structure de vos modèles !)
            if request.user.role:
                return request.user.role.permissions.filter(code=required_permission_code).exists()

            return False

    # La fonction retourne la CLASSE (non instanciée)
    return HasRequiredPermission