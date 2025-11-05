# users/serializers.py

from rest_framework import serializers
from .models import Utilisateur, Role, Permission
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.core.mail import send_mail # Importez send_mail pour le mail de bienvenue
from rest_framework import serializers, status

# --- Serializers de Sécurité et d'Authentification ---

class ClientMinimalSerializer(serializers.ModelSerializer):
    # Ceci affiche le nom complet (grâce à la correction get_full_name)
    full_name = serializers.CharField(source='get_full_name', read_only=True) 

    class Meta:
        model = Utilisateur
        # N'inclure que les informations de vérification/contact :
        fields = ('id', 'full_name', 'email', 'telephone')

class LoginSerializer(serializers.Serializer):
    """Sérielizeur pour la connexion utilisateur."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    """Sérielizeur pour l'enregistrement (uniquement pour les clients externes ou initialisation)."""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Utilisateur
        fields = ('id', 'email', 'password', 'nom', 'prenoms', 'telephone')
        read_only_fields = ('role', 'is_staff', 'is_superuser') 

    def create(self, validated_data):
        
        # --- 1. Attribution du Rôle 'Client' ---
        try:
            # Assurez-vous que le rôle 'Client' existe (doit être créé par load_dummy_data/migrations)
            client_role = Role.objects.get(nom_role='Client') 
            validated_data['role'] = client_role
        except Role.DoesNotExist:
            # Gérer l'erreur si le rôle n'existe pas, ou laisser le champ à NULL
            # Pour la démo, on peut ignorer, mais en production, c'est critique
            pass 
            
        # Création de l'utilisateur via le CustomUserManager
        user = Utilisateur.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            nom=validated_data.get('nom', ''),
            prenoms=validated_data.get('prenoms', ''),
            telephone=validated_data.get('telephone'),
            role=validated_data.get('role', None) # Passez le rôle au create_user
        )
        
        # --- 2. Envoi du Mail de Bienvenue ---
        self.send_welcome_email(user)
        
        return user
        
    def send_welcome_email(self, user):
        """Fonction utilitaire pour envoyer l'email de bienvenue."""
        
        sujet = f"Bienvenue chez PPPI, {user.prenoms} !"
        message = (
            f"Bonjour {user.prenoms},\n\n"
            f"Votre compte Client a été créé avec succès sur la plateforme PPPI.\n"
            f"Votre identifiant de connexion est : {user.email}\n\n"
            f"Vous pouvez maintenant suivre vos colis en temps réel via notre application mobile.\n\n"
            f"L'équipe PPPI."
        )
        
        try:
            send_mail(
                sujet,
                message,
                'noreply@pppi-lib.com', # Utilisez votre DEFAULT_FROM_EMAIL
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Ceci est crucial. L'enregistrement doit réussir même si l'e-mail échoue.
            print(f"Erreur d'envoi du mail de bienvenue à {user.email}: {e}")
            # Vous pouvez logguer l'erreur ici.

# --- Serializers de Gestion Utilisateur / Rôles ---

class UtilisateurSerializer(serializers.ModelSerializer):
    """Sérielizeur complet pour la gestion des utilisateurs (CRUD par Admin)."""
    role_name = serializers.CharField(source='role.nom_role', read_only=True)
    
    class Meta:
        model = Utilisateur
        # Exclure le mot de passe dans la lecture
        exclude = ('password', 'groups', 'user_permissions', 'is_superuser', 'last_login')
        read_only_fields = ('id', 'date_joined')
        
# users/serializers.py (Ajouts)

class ForgotPasswordSerializer(serializers.Serializer):
    """Pour la demande de réinitialisation : envoie de l'email."""
    email = serializers.EmailField(required=True)

class ResetPasswordVerifySerializer(serializers.Serializer):
    """Pour la vérification du code secret."""
    email = serializers.EmailField(required=True)
    code_secret = serializers.CharField(max_length=6, required=True)

class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Pour la confirmation finale du mot de passe."""
    email = serializers.EmailField(required=True)
    code_secret = serializers.CharField(max_length=6, required=True)
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return data        
    
    
    
class RefreshTokenSerializer(serializers.Serializer):
    """Serializer pour l'actualisation du jeton (utilise le Refresh Token)."""
    refresh = serializers.CharField()
    
    # Vous pouvez dériver de TokenRefreshSerializer de simplejwt si vous souhaitez
    # utiliser la logique de validation intégrée, mais pour un wrapper simple :
    
    # def validate(self, attrs):
    #     # Validera que le champ refresh est présent et non vide
    #     return attrs
        


class RoleSerializer(serializers.ModelSerializer):
    """Sérielizeur pour les Rôles."""
    class Meta:
        model = Role
        fields = '__all__'
        
class PermissionSerializer(serializers.ModelSerializer):
    """Sérielizeur pour les Permissions."""
    class Meta:
        model = Permission
        fields = '__all__'