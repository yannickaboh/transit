from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
# users/models.py (Début du fichier)

from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import random # <--- AJOUTER CET IMPORT
from django.utils import timezone # <--- AJOUTER CET IMPORT
# Note: timezone.timedelta fait partie de la bibliothèque standard datetime, mais s'assure que timezone est là
# users/models.py (Ajouter ces imports et la classe CustomUserManager)

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager # Importer BaseUserManager
import uuid
import random
from django.utils import timezone
from datetime import timedelta # Ajouter timedelta si ce n'est pas déjà fait

# --- CUSTOM MANAGER ---
class CustomUserManager(BaseUserManager):
    """
    Manager qui utilise l'email comme identifiant au lieu du username.
    Ceci remplace le comportement par défaut de AbstractUser.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'email doit être défini')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')
        
        # Le manager personnalisé gère la création sans nécessiter 'username'
        return self.create_user(email, password, **extra_fields)

# --- Utilisateur Personnalisé ---

# --- 1. Roles et Permissions (Pour le RBAC) ---

class Permission(models.Model):
    """Permissions granulaires, liées aux Roles."""
    code_permission = models.CharField(max_length=50, unique=True, verbose_name="Code de Permission")
    libelle = models.CharField(max_length=255, verbose_name="Libellé")

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.code_permission

class Role(models.Model):
    """Définition des rôles utilisateurs (Admin, AgentPort, Client, Douanier...)."""
    nom_role = models.CharField(max_length=50, unique=True, verbose_name="Nom du Rôle")
    description = models.TextField(blank=True, verbose_name="Description")
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name="Permissions Associées")

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"

    def __str__(self):
        return self.nom_role

# --- 2. Utilisateur Personnalisé ---

class Utilisateur(AbstractUser):
    """Modèle Utilisateur étendu pour intégrer le rôle et le 2FA."""
    # Utilisation de l'email comme champ unique d'identification
    # --- CONFIGURATION CRITIQUE POUR L'EMAIL COMME IDENTIFIANT ---
    # 1. Le manager personnalisé prend le relais
    objects = CustomUserManager() 

    # 2. Supprime l'héritage du champ 'username' et son utilisation
    username = None 
    USERNAME_FIELD = 'email'

    # 3. Ceci est la clé: REDÉFINIR le champ email hérité 
    # (même s'il existe dans AbstractUser, il doit être explicitement unique ici)
    email = models.EmailField(unique=True, verbose_name="Adresse E-mail")
    
    # 4. Champs requis lors de la création d'un super-utilisateur
    REQUIRED_FIELDS = ['nom', 'prenoms', 'telephone']
    # -----------------------------------------------------------------
    # Suppression du champ 'username' par défaut si l'email est utilisé comme login
    # username = None 
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['nom', 'prenoms', 'telephone'] 

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # --- Champs de Réinitialisation ---
    code_secret_reset = models.CharField(max_length=6, blank=True, null=True, verbose_name="Code Secret de Réinitialisation")
    code_secret_reset_expiration = models.DateTimeField(null=True, blank=True, verbose_name="Expiration du Code Secret")

    # ... (autres méthodes et classes Meta)
    
    # Relation N:1 vers Role
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="utilisateur_groups", # CHANGEMENT CLÉ ICI
        related_query_name="utilisateur",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="utilisateur_permissions", # CHANGEMENT CLÉ ICI
        related_query_name="utilisateur",
    )
    
    # Sécurité
    deux_facteurs_actif = models.BooleanField(default=False, verbose_name="2FA Actif")

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.prenoms} {self.nom} ({self.role})"
    
    # Note: AbstractUser fournit déjà get_full_name(),
    # mais il utilise first_name et last_name (que vous avez renommé/remplacé par prenoms/nom)
    # Pour garantir qu'il utilise VOS champs:
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        return f"{self.prenoms} {self.nom}".strip()

    def get_short_name(self):
        """Retourne uniquement le prénom de l'utilisateur."""
        return self.prenoms
    
    def generer_code_secret(self):
        """Génère un code secret à 6 chiffres et définit son expiration (ex: 15 minutes)."""
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.code_secret_reset = code
        self.code_secret_reset_expiration = timezone.now() + timezone.timedelta(minutes=15)
        self.save()
        return code