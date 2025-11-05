# users/management/commands/load_dummy_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import random
import uuid

# Importation de tous les modèles nécessaires
from users.models import Utilisateur, Role, Permission
from logistics.models import Colis, SuiviStatut, RetraitColis
from payments.models import TransactionPaiement
from audit.models import JournalAudit 

# --- CONFIGURATION GLOBALE ---
DEFAULT_PASSWORD = "QWzx1234"
DEFAULT_EMAIL_SUFFIX = "@transit241.com"
ROLES_DATA = {
    "Admin": ["logistics.manage_colis", "users.manage_users", "payments.manage_transactions", "audit.view_logs"],
    "AgentPort": ["logistics.create_colis", "logistics.update_statut", "logistics.validate_retrait"],
    "Douanier": ["logistics.view_colis", "logistics.update_statut", "payments.view_transactions"],
    "Client": ["logistics.track_colis", "payments.make_payment", "payments.view_transactions"],
    "Transporteur": ["logistics.track_colis"],
}
STATUTS_POSSIBLES = [s[0] for s in Colis.STATUT_CHOICES]

class Command(BaseCommand):
    help = 'Charge des données factices (Roles, Users, Colis, Transactions, etc.) dans la base de données.'

    def handle(self, *args, **options):
        # Utilisation d'une transaction pour garantir l'atomicité
        with transaction.atomic():
            self.stdout.write(self.style.WARNING("Démarrage du chargement des données factices..."))

            # 1. Création des Permissions
            self.stdout.write("1. Création des Permissions et des Rôles...")
            permissions_crees = self._create_permissions_and_roles()
            self.stdout.write(self.style.SUCCESS(f"-> {len(permissions_crees)} permissions et {len(ROLES_DATA)} rôles créés."))

            # 2. Création des Utilisateurs
            self.stdout.write("\n2. Création des Utilisateurs (Superusers)...")
            users_crees = self._create_users()
            self.stdout.write(self.style.SUCCESS(f"-> {len(users_crees)} utilisateurs factices créés."))

            # 3. Création des Données Logistiques (Colis, Suivi, Retrait)
            self.stdout.write("\n3. Création des Données Logistiques (Colis, Suivi)...")
            clients = [u for u in Utilisateur.objects.filter(role__nom_role='Client')]
            agents = [u for u in Utilisateur.objects.filter(role__nom_role='AgentPort')]
            if clients and agents:
                colis_crees = self._create_logistics_data(clients, agents)
                self.stdout.write(self.style.SUCCESS(f"-> {len(colis_crees)} colis générés."))
            else:
                self.stdout.write(self.style.ERROR("!! Pas assez de clients ou d'agents pour créer des colis."))

            # 4. Création des Données Paiements et Audit
            self.stdout.write("\n4. Création des Transactions et Logs d'Audit...")
            if 'colis_crees' in locals():
                 self._create_payment_and_audit_data(colis_crees, clients, agents)
            self.stdout.write(self.style.SUCCESS("-> Transactions et Logs d'Audit générés."))

            self.stdout.write(self.style.SUCCESS("\n✅ Chargement des données factices terminé avec succès."))
            self.stdout.write(self.style.SUCCESS(f"Les mots de passe par défaut pour tous les Superusers sont: {DEFAULT_PASSWORD}"))

    def _create_permissions_and_roles(self):
        """Crée toutes les permissions nécessaires et les rôles."""
        permissions_list = set()
        for perms in ROLES_DATA.values():
            permissions_list.update(perms)
        
        # Création des permissions
        Permission.objects.all().delete()
        permissions_instances = {}
        for code in permissions_list:
            # Exemple de libellé basique
            libelle = code.replace('.', ' ').replace('_', ' ').title()
            perm_obj = Permission.objects.create(code_permission=code, libelle=libelle)
            permissions_instances[code] = perm_obj
            
        # Création des rôles et attribution des permissions
        Role.objects.all().delete()
        for role_name, required_perms in ROLES_DATA.items():
            role_obj = Role.objects.create(nom_role=role_name, description=f"Rôle pour les {role_name}")
            for code in required_perms:
                role_obj.permissions.add(permissions_instances[code])
        
        return permissions_instances

    def _create_users(self):
        """Crée un Superuser pour chaque rôle principal."""
        Utilisateur.objects.all().delete()
        roles_instances = Role.objects.all()
        users_crees = []

        for role in roles_instances:
            email_prefix = role.nom_role.lower()
            user_email = f"{email_prefix}{DEFAULT_EMAIL_SUFFIX}"
            
            user = Utilisateur.objects.create_user(
                # ANCIEN CODE (ERREUR) : username=user_email, 
                email=user_email, # NE PAS CHANGER
                password=DEFAULT_PASSWORD,
                nom=role.nom_role,
                prenoms=f"User",
                role=role,
                is_staff=True,
                is_superuser=True if role.nom_role == 'Admin' else False,
                deux_facteurs_actif=True if role.nom_role == 'Admin' else False
            )
            users_crees.append(user)
        
        # Créer quelques clients supplémentaires
        for i in range(5):
             client_role = Role.objects.get(nom_role='Client')
             client_email = f"client{i+1}{DEFAULT_EMAIL_SUFFIX}"
             user = Utilisateur.objects.create_user(
                # ANCIEN CODE (ERREUR) : username=client_email,
                email=client_email, # NE PAS CHANGER
                password=DEFAULT_PASSWORD,
                nom=f"Client{i+1}",
                prenoms="Extern",
                role=client_role,
             )
             users_crees.append(user)
             
        return users_crees

    def _create_logistics_data(self, clients, agents, num_colis=20):
        """Crée des colis avec historique de suivi et un retrait simulé."""
        Colis.objects.all().delete()
        SuiviStatut.objects.all().delete()
        RetraitColis.objects.all().delete()
        
        colis_list = []
        for i in range(num_colis):
            client = random.choice(clients)
            agent_port = random.choice(agents)
            
            # 1. Création du Colis
            colis = Colis.objects.create(
                numero_bl=f"BL{random.randint(100000, 999999)}GAB",
                description=f"Marchandise générale n°{i+1}",
                poids_kg=random.uniform(500, 5000),
                client=client,
                statut_actuel='EN_ATTENTE_DECHARGE'
            )
            colis_list.append(colis)

            # 2. Création de l'Historique de Suivi
            statut_courant = 'EN_ATTENTE_DECHARGE'
            for statut in STATUTS_POSSIBLES:
                if random.random() < 0.7 or statut == statut_courant: # Chance de passer au statut suivant
                    SuiviStatut.objects.create(
                        colis=colis,
                        statut=statut,
                        localisation=f"Zone {random.choice(['A', 'B', 'C'])}",
                        agent_operationnel=agent_port,
                        date_heure=timezone.now() - timezone.timedelta(days=random.randint(0, 10))
                    )
                    statut_courant = statut
                    colis.statut_actuel = statut # Mise à jour du statut final
                    if statut == 'LIVRE':
                        break

            colis.save()
            
            # 3. Création du Retrait si livré
            if colis.statut_actuel == 'LIVRE':
                RetraitColis.objects.create(
                    colis=colis,
                    agent_validation=agent_port,
                    preuve_identite_url="https://dummyurl.com/id",
                    signature_client="SignatureB64"
                )
        return colis_list

    def _create_payment_and_audit_data(self, colis_list, clients, agents):
        """Crée des transactions et des logs d'audit simulés."""
        TransactionPaiement.objects.all().delete()
        JournalAudit.objects.all().delete()
        
        admin_user = Utilisateur.objects.get(role__nom_role='Admin')

        for colis in colis_list:
            client = colis.client
            
            # Création de Transactions (2 à 3 par colis)
            for _ in range(random.randint(1, 3)):
                statut_paiment = random.choice(['REUSSI', 'EN_ATTENTE'])
                TransactionPaiement.objects.create(
                    colis=colis,
                    utilisateur_payeur=client,
                    montant_ht=random.uniform(10000, 500000),
                    montant_total=random.uniform(10500, 525000),
                    type_frais=random.choice(['MANUTENTION', 'DOUANE', 'STOCKAGE']),
                    statut_paiement=statut_paiment
                )

            # Création de Logs d'Audit (Simulation d'activité)
            JournalAudit.objects.create(
                utilisateur=admin_user,
                action_type='LOGIN_SUCCESS',
                ressource_affectee='Utilisateur',
                ressource_id=str(admin_user.id),
                adresse_ip="192.168.1.1",
                details="Connexion de l'administrateur réussie."
            )
            JournalAudit.objects.create(
                utilisateur=random.choice(agents),
                action_type='MODIF_STATUT',
                ressource_affectee='Colis',
                ressource_id=str(colis.id),
                adresse_ip="10.0.0.5",
                details=f"Statut mis à jour vers {colis.statut_actuel}"
            )