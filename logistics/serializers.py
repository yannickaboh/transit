# logistics/serializers.py

from rest_framework import serializers
from .models import Colis, SuiviStatut, RetraitColis
from users.models import Utilisateur, Role, Permission
from users.serializers import ClientMinimalSerializer

class SuiviStatutSerializer(serializers.ModelSerializer):
    """Sérielizeur pour l'historique de statut."""
    agent_operationnel_name = serializers.CharField(source='agent_operationnel.get_full_name', read_only=True)
    
    class Meta:
        model = SuiviStatut
        fields = '__all__'
        read_only_fields = ('date_heure',)

class ColisSerializer(serializers.ModelSerializer):
    """Sérielizeur pour l'entité Colis."""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    # Pour afficher l'historique lors de la consultation d'un Colis
    historique_statuts = SuiviStatutSerializer(many=True, read_only=True) 
    
    # Ajoutez ou modifiez le constructeur pour accepter 'fields'
    def __init__(self, *args, **kwargs):
        # Ne pas appeler la méthode __init__ de la classe de base (serializers.Field) 
        # car c'est là que l'erreur 'fields' se produit
        
        # Récupérer l'argument 'fields' si passé
        fields = kwargs.pop('fields', None)

        # Appeler la méthode __init__ de la classe parent (ModelSerializer)
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the 'fields' argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = Colis
        fields = '__all__'
        read_only_fields = ('id', 'date_arrivee', 'statut_actuel', 'historique_statuts')
        
class ColisMinimalSerializer(serializers.ModelSerializer):
    client = ClientMinimalSerializer(read_only=True)
    # On ajoute d'autres champs utiles (description, statut_actuel, etc.)
    class Meta:
        model = Colis
        fields = ('id', 'numero_bl', 'description', 'statut_actuel', 'client')
        



class AgentValidationMinimalSerializer(serializers.ModelSerializer):
    # On utilise la correction que nous avons faite !
    agent_name = serializers.CharField(source='get_full_name', read_only=True)
    class Meta:
        model = Utilisateur
        fields = ('id', 'agent_name', 'email', 'telephone')


# ... (Vos imports existants : ModelSerializer, Colis, SuiviStatut, RetraitColis, Utilisateur, etc.)

# ... (Vos classes SuiviStatutSerializer, ColisSerializer, ColisMinimalSerializer, AgentValidationMinimalSerializer)

# --- NOUVEAU SÉRIALISEUR POUR LA CRÉATION (POST) ---
class RetraitColisCreateSerializer(serializers.ModelSerializer):
    """
    Sérielizeur minimal pour la création (POST) d'un RetraitColis.
    N'accepte que les ID (UUID) et les champs simples requis.
    """
    
    # DRF s'attend à recevoir les UUID des objets liés (colis et agent)
    # car ce sont des ForeignKey dans le modèle RetraitColis.
    
    class Meta:
        model = RetraitColis
        # Seulement les champs qui doivent être fournis par le client Flutter
        fields = ('colis', 'agent_validation', 'preuve_identite_url', 'signature_client')
        # Pas de read_only_fields : tous ces champs sont requis en écriture.

# --- SÉRIALISEUR POUR L'AFFICHAGE DÉTAILLÉ (GET) ---
# Ceci est votre ancien RetraitColisSerializer, mais renommé ou modifié pour la clarté.
class RetraitColisSerializer(serializers.ModelSerializer):
    """Sérielizeur pour l'affichage détaillé (GET) d'un RetraitColis."""
    colis_details = ColisMinimalSerializer(source='colis', read_only=True)
    agent_details = AgentValidationMinimalSerializer(source='agent_validation', read_only=True)
    
    class Meta:
        model = RetraitColis
        # Inclut tous les champs du modèle (y compris les ID 'colis' et 'agent_validation')
        # ainsi que les champs imbriqués ('colis_details', 'agent_details') pour la lecture.
        fields = '__all__'
        read_only_fields = ('date_heure_retrait',) 
        # Note : 'agent_validation' est retiré des read_only_fields pour la Meta 
        # car nous gérons les champs imbriqués en lecture seule manuellement.

# ... (Votre classe FileUploadSerializer)
        
        

class FileUploadSerializer(serializers.Serializer):
    """
    Serializer pour gérer l'upload d'un seul fichier (la pièce d'identité).
    """
    file = serializers.FileField()
    
    # Vous pouvez ajouter ici la logique de validation de type de fichier
    # (ex: seulement JPG/PNG) si nécessaire.