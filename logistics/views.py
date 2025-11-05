# logistics/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Colis, SuiviStatut, RetraitColis, Facture, DeclarationDouaniere
from .serializers import ColisSerializer, SuiviStatutSerializer, RetraitColisSerializer, RetraitColisCreateSerializer, FactureSerializer, DeclarationDouaniereSerializer
from django.shortcuts import get_object_or_404
# logistics/views.py (Ajouter ou corriger ces imports au début du fichier)

from rest_framework import viewsets, permissions, status
# ... autres imports
from drf_yasg.utils import swagger_auto_schema 
from drf_yasg import openapi # On garde l'import de openapi
# --- CORRECTION ICI ---
# Parameter se trouve dans openapi.
from drf_yasg.openapi import Parameter # <--- C'EST CELLE-CI LA BONNE !

from rest_framework.permissions import IsAuthenticated

# ... (imports existants)
from .tasks import envoyer_notification_email 
from django.shortcuts import get_object_or_404 # Nécessaire si non importé
from django.core.files.storage import default_storage
from django.conf import settings
from .serializers import FileUploadSerializer # Importer le Serializer créé
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import random 
from django.utils import timezone # <--- ASSUREZ-VOUS QUE C'EST BIEN LÀ !
from datetime import timedelta
from drf_yasg import openapi # Assurez-vous d'avoir cet import
from rest_framework.parsers import MultiPartParser, FileUploadParser

# -----------------------------------------------------------------
# DÉFINITION GLOBALE DU SCHÉMA DU CORPS DE REQUÊTE POUR L'UPLOAD
# -----------------------------------------------------------------
file_upload_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['file'],
    properties={
        'file': openapi.Schema(
            type=openapi.TYPE_FILE,
            description="Le fichier de la preuve d'identité à uploader (image)."
        )
    }
)
# -----------------------------------------------------------------


class ColisViewSet(viewsets.ModelViewSet):
    """CRUD pour la gestion des colis (accès restreint aux Agents/Admins)."""
    queryset = Colis.objects.all()
    serializer_class = ColisSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            Parameter( # Utilisez la classe Parameter importée
                'id', 
                in_=openapi.IN_QUERY, # openapi doit aussi être importé de drf_yasg
                description="ID unique du colis (UUID).",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='track')
    def track_colis(self, request):
        """Endpoint pour le suivi public par ID Unique."""
        colis_id = request.query_params.get('id')
        if not colis_id:
            return Response({"detail": "Veuillez fournir l'ID unique du colis."}, status=status.HTTP_400_BAD_REQUEST)
            
        colis = get_object_or_404(Colis, id=colis_id)
        # On n'affiche que les infos publiques et l'historique de statut
        serializer = ColisSerializer(colis, fields=('id', 'description', 'statut_actuel', 'historique_statuts'))
        return Response(serializer.data)

class SuiviStatutViewSet(viewsets.ModelViewSet):
    """CRUD pour les mises à jour de statut (utilisé par les agents)."""
    queryset = SuiviStatut.objects.all()
    serializer_class = SuiviStatutSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Met à jour le statut_actuel du Colis parent après création du SuiviStatut."""
        statut_instance = serializer.save(agent_operationnel=self.request.user)
        colis = statut_instance.colis
        colis.statut_actuel = statut_instance.statut
        colis.save()
        
        # --- Déclenchement ASYNCHRONE ---
        client_email = colis.client.email
        
        sujet = f"PPPI : Mise à jour de votre colis #{colis.id}"
        message = f"Le statut de votre colis ({colis.numero_bl}) a été mis à jour.\nNouveau statut : {colis.get_statut_actuel_display()}\nLocalisation : {statut_instance.localisation}"
        
        # Lancement de la tâche Celery (appel non bloquant)
        envoyer_notification_email.delay(client_email, sujet, message) 
        
        # Ici, vous pourriez aussi ajouter envoyer_notification_sms.delay(...)
        # Ici, ajouter la logique de notification automatique (asynchrone)

# logistics/views.py

class RetraitColisViewSet(viewsets.ModelViewSet):
    """CRUD pour la validation des retraits (nécessite des permissions fortes)."""
    queryset = RetraitColis.objects.all()
    serializer_class = RetraitColisSerializer
    permission_classes = [IsAuthenticated]
    
    # --- AJOUT CRITIQUE POUR LA CRÉATION ---
    # Nouvelle méthode pour choisir le sérialiseur
    def get_serializer_class(self):
        if self.action == 'create':
            return RetraitColisCreateSerializer
        # Utiliser le sérialiseur détaillé pour toutes les autres actions (retrieve, list, update)
        return RetraitColisSerializer
    
    def perform_create(self, serializer):
        """Met à jour le statut_actuel du Colis parent après création du RetraitColis."""
        
        # 1. Sauvegarde l'instance. 
        # L'ID de l'agent est déjà dans serializer.validated_data, donc pas d'injection forcée.
        retrait_instance = serializer.save()
        
        # 2. Mise à jour du statut du Colis à 'LIVRE'
        colis = retrait_instance.colis
        colis.statut_actuel = 'LIVRE' 
        colis.save()
        
        # 3. (OPTIONNEL) Déclencher une notification
        # Vous pouvez appeler ici une tâche Celery pour confirmer la livraison.
        
    
    

# Création du schéma de corps de requête spécifique pour l'upload de fichier 
class FileUploadView(APIView):
    """
    Gère l'upload de la preuve d'identité et retourne l'URL du fichier stocké.
    """
    # Permission: Seuls les utilisateurs authentifiés peuvent uploader
    permission_classes = [IsAuthenticated] 
    
    # CECI DOIT ÊTRE PRÉSENT ET CORRECT
    parser_classes = (MultiPartParser, FileUploadParser)
    
    @swagger_auto_schema(
        tags=['Retraits'],
        operation_summary="Upload de la preuve d'identité du client.",
        operation_description="Reçoit un fichier image (multipart/form-data) et retourne l'URL publique.",
        manual_parameters=[
            # Ceci devient valide car la vue utilise maintenant les parsers de fichiers
            openapi.Parameter(
                'file', 
                in_=openapi.IN_FORM, 
                type=openapi.TYPE_FILE, 
                description="Le fichier de la preuve d'identité à uploader (image).",
                required=True
            )
        ],
        
        # Le reste des réponses
        responses={
            201: openapi.Response(
                'Upload réussi',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'url': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL du fichier uploadé")}
                )
            ),
            400: 'Données de fichier invalides'
        },
        # NOTE: On peut parfois forcer le Content-Type ici, mais IN_FORM devrait suffire.
        consumes=['multipart/form-data'], # Optionnel, mais peut aider
    )
    def post(self, request, format=None):
        serializer = FileUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            
            # 1. Définir un nom unique pour le fichier (important pour éviter les collisions)
            # Ex: 'uploads/identite/ID_agent-uuid_timestamp.jpg'
            extension = uploaded_file.name.split('.')[-1]
            file_name = f"preuve_identite/{request.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{extension}"
            
            # 2. Sauvegarder le fichier
            try:
                # Utilise le système de stockage configuré dans settings.py (ex: FileSystemStorage ou S3)
                path = default_storage.save(file_name, uploaded_file)
                
                # 3. Construire l'URL publique
                file_url = settings.MEDIA_URL + path
                
                # Renvoie l'URL au client Flutter
                return Response({'url': file_url}, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # Gérer les erreurs de stockage/permission
                return Response({'detail': f"Erreur de sauvegarde: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
    
    
# logistics/views.py (Ajouter ces imports nécessaires)
from .serializers import FactureSerializer, DeclarationDouaniereSerializer
# Assurez-vous d'avoir IsAuthenticated, Response, status, action, swagger_auto_schema importés

# --- 4. Vues pour les Factures ---
class FactureViewSet(viewsets.ModelViewSet):
    """CRUD pour la gestion des factures."""
    queryset = Facture.objects.all()
    serializer_class = FactureSerializer
    # Permission: Les agents et clients peuvent voir leurs propres factures, les admins toutes
    permission_classes = [IsAuthenticated]
    
    # Action pour marquer une facture comme payée (utilisé par l'agent ou un webhook de paiement)
    @swagger_auto_schema(
        tags=['Facturation'],
        operation_summary="Marquer la facture comme Payée",
        responses={200: 'Facture mise à jour', 404: 'Facture non trouvée'}
    )
    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        facture = get_object_or_404(Facture, pk=pk)
        if facture.statut == 'PENDING':
            facture.statut = 'PAID'
            facture.date_paiement = timezone.now()
            facture.save()
            return Response({'statut': 'PAID', 'date_paiement': facture.date_paiement}, status=status.HTTP_200_OK)
        return Response({'detail': 'La facture n\'est pas en statut PENDING.'}, status=status.HTTP_400_BAD_REQUEST)


# --- 5. Vues pour les Déclarations Douanières ---
class DeclarationDouaniereViewSet(viewsets.ModelViewSet):
    """CRUD pour la gestion des déclarations douanières (principalement par les Douaniers)."""
    queryset = DeclarationDouaniere.objects.all()
    serializer_class = DeclarationDouaniereSerializer
    # Permission: Seuls les utilisateurs ayant le rôle "Douanier" ou Admin devraient avoir un accès complet
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
        """Lors de la création, le statut par défaut est Brouillon."""
        instance = serializer.save()
        # Logique optionnelle ici : si le douanier envoie le colis, on pourrait mettre à jour le statut du colis
        
    @swagger_auto_schema(
        tags=['Douanes'],
        operation_summary="Approuver la déclaration (Dédouanement)",
        responses={200: 'Déclaration approuvée', 404: 'Déclaration non trouvée'}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve_declaration(self, request, pk=None):
        declaration = get_object_or_404(DeclarationDouaniere, pk=pk)
        if declaration.statut != 'CLEARED':
            declaration.statut = 'CLEARED'
            declaration.date_dedouanement = timezone.now()
            declaration.save()
            
            # Mettre à jour le statut du colis à "Prêt au Retrait" si nécessaire
            colis = declaration.colis
            colis.statut_actuel = 'PRET_RETRAIT'
            colis.save()
            
            return Response({'statut': 'CLEARED', 'message': 'Déclaration approuvée et Colis prêt au retrait.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'La déclaration est déjà dédouanée.'}, status=status.HTTP_400_BAD_REQUEST)