# users/views.py

from rest_framework import viewsets, mixins, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken # JWT pour l'authentification
from drf_yasg.utils import swagger_auto_schema
from .models import Utilisateur, Role, Permission
from .serializers import (
    UtilisateurSerializer, RoleSerializer, PermissionSerializer, 
    LoginSerializer, RegisterSerializer, ForgotPasswordSerializer, ResetPasswordConfirmSerializer, RefreshTokenSerializer
)
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt # Ajoutez cet import !
from django.utils.decorators import method_decorator # Ajoutez cet import !

from rest_framework.permissions import IsAuthenticated
from .permissions import HasPermission

# --- IMPORTATION MANQUANTE ---
from django.contrib.auth import authenticate

# --- 1. Authentification View ---

class AuthViewSet(viewsets.GenericViewSet):
    """Endpoints pour l'authentification (login, register, reset, etc.)."""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(request_body=LoginSerializer)
    @method_decorator(csrf_exempt, name='dispatch')
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(username=email, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UtilisateurSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({"detail": "Identifiants invalides."}, status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(request_body=RegisterSerializer)
    @method_decorator(csrf_exempt, name='dispatch')
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """Permet l'enregistrement initial des clients/utilisateurs externes."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UtilisateurSerializer(user).data, status=status.HTTP_201_CREATED)
        
    # --- TODO: forgot_password et reset_password à implémenter ---
    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    @method_decorator(csrf_exempt, name='dispatch')
    @action(detail=False, methods=['post'], url_path='forgot')
    def forgot_password(self, request):
        """Demande de réinitialisation: génère un code secret et l'envoie par email."""
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            # Sécurité : On répond 'OK' même si l'utilisateur n'existe pas pour éviter l'énumération
            return Response({"detail": "Si cet email est associé à un compte, un code secret y a été envoyé."}, status=status.HTTP_200_OK)

        # 1. Génération du code
        code = user.generer_code_secret()

        # 2. Envoi de l'email (Utilisation de send_mail de Django)
        sujet = "PPPI - Votre code secret de réinitialisation de mot de passe"
        message = f"Bonjour {user.prenoms},\n\nVotre code secret de réinitialisation est : {code}.\n\nCe code expire dans 15 minutes.\n\nL'équipe PPPI."
        
        send_mail(
            sujet,
            message,
            'noreply@pppi-lib.com', # Mettez votre EMAIL_HOST_USER ici
            [user.email],
            fail_silently=False,
        )

        return Response({"detail": "Un code secret a été envoyé à votre email."}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ResetPasswordConfirmSerializer)
    @method_decorator(csrf_exempt, name='dispatch')
    @action(detail=False, methods=['post'], url_path='reset')
    def reset_password(self, request):
        """Confirmation de réinitialisation: vérifie le code et met à jour le mot de passe."""
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code_secret = serializer.validated_data['code_secret']
        new_password = serializer.validated_data['password']

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response({"detail": "Email invalide."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Vérification du code et de l'expiration
        if user.code_secret_reset != code_secret:
            return Response({"detail": "Code secret invalide."}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.code_secret_reset_expiration is None or user.code_secret_reset_expiration < timezone.now():
            return Response({"detail": "Code secret expiré."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Mise à jour du mot de passe
        user.set_password(new_password)
        # 3. Invalidation du code secret après utilisation
        user.code_secret_reset = None
        user.code_secret_reset_expiration = None
        user.save()
        
        return Response({"detail": "Mot de passe réinitialisé avec succès. Veuillez vous reconnecter."}, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(request_body=RefreshTokenSerializer) # Utilisez votre Serializer simple pour Swagger
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_token(self, request):
        """Actualise le Access Token en utilisant le Refresh Token."""
        
        # 1. Utiliser votre Serializer pour valider l'entrée (champ 'refresh')
        simple_serializer = RefreshTokenSerializer(data=request.data)
        simple_serializer.is_valid(raise_exception=True)

        refresh_token = simple_serializer.validated_data['refresh']
        
        # 2. Utiliser le Serializer de Simple JWT pour l'actualisation réelle
        # Ceci gère la vérification d'expiration et la création des nouveaux tokens
        refresh_data = {'refresh': refresh_token}
        
        try:
            # TokenRefreshSerializer effectue la validation complète du Refresh Token
            refresh_serializer = TokenRefreshSerializer(data=refresh_data)
            refresh_serializer.is_valid(raise_exception=True)
            
            # Retourne le nouveau jeton d'accès (et potentiellement un nouveau jeton de rafraîchissement si configuré)
            return Response(refresh_serializer.validated_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Gère les erreurs spécifiques à JWT (jeton expiré ou invalide)
            return Response({"detail": "Token de rafraîchissement invalide ou expiré."}, 
                            status=status.HTTP_401_UNAUTHORIZED)

# --- 2. Gestion des Utilisateurs / Rôles (Admin CRUD) ---

class UtilisateurViewSet(viewsets.ModelViewSet):
    """CRUD complet pour les utilisateurs (nécessite la permission Admin)."""
    queryset = Utilisateur.objects.all().order_by('nom')
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated] # Exemple RBAC
    
    # --- Rôles : Récupération des IDs de Rôle (Méthode temporaire/simplifiée) ---
    def get_role_id(self, role_name):
        """Récupère l'ID du rôle à partir du nom."""
        try:
            # CORRECTION : Remplacer 'nom' par 'nom_role'
            return Role.objects.get(nom_role=role_name).id 
        except Role.DoesNotExist:
            return None

    # ------------------------------------------------------------------
    # 🎯 ENDPOINT 1 : Lister les Agents Portuaires
    @action(detail=False, methods=['get'], url_path='agents-portuaires')
    def list_agents_portuaires(self, request):
        role_id = self.get_role_id('AgentPort')
        if not role_id:
            return Response({"detail": "Le rôle 'AgentPort' n'existe pas."}, status=status.HTTP_404_NOT_FOUND)

        # Filtrer par l'ID du rôle
        agents = self.queryset.filter(role__id=role_id)
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # 🎯 ENDPOINT 2 : Lister les Douaniers
    @action(detail=False, methods=['get'], url_path='douaniers')
    def list_douaniers(self, request):
        role_id = self.get_role_id('Douanier')
        if not role_id:
            return Response({"detail": "Le rôle 'Douanier' n'existe pas."}, status=status.HTTP_404_NOT_FOUND)

        douaniers = self.queryset.filter(role__id=role_id)
        serializer = self.get_serializer(douaniers, many=True)
        return Response(serializer.data)
        
    # ------------------------------------------------------------------
    # 🎯 ENDPOINT 3 : Lister les Clients
    @action(detail=False, methods=['get'], url_path='clients')
    def list_clients(self, request):
        role_id = self.get_role_id('Client')
        if not role_id:
            return Response({"detail": "Le rôle 'Client' n'existe pas."}, status=status.HTTP_404_NOT_FOUND)

        clients = self.queryset.filter(role__id=role_id)
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

class RoleViewSet(viewsets.ModelViewSet):
    """CRUD pour les rôles."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule des permissions disponibles."""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]