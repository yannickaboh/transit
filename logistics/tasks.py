# logistics/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from users.models import Utilisateur
from django.conf import settings

@shared_task
def envoyer_notification_email(email_destinataire, sujet, message):
    """Tâche Celery pour envoyer un e-mail de manière non bloquante."""
    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.EMAIL_HOST_USER, 
            recipient_list=[email_destinataire],
            fail_silently=False,
        )
        return f"Email envoyé avec succès à {email_destinataire}"
    except Exception as e:
        # En cas d'échec, Celery peut être configuré pour réessayer
        print(f"Erreur d'envoi d'email: {e}")
        # Optionnel: raise self.retry(exc=e, countdown=60)
        return f"Échec de l'envoi d'email: {e}"

# --- Tâche plus complexe pour la sécurité ---

@shared_task
def envoyer_alerte_securite(user_id, action, ip_address):
    """Envoie une alerte critique aux administrateurs (e.g., tentative de connexion échouée répétée)."""
    try:
        user = Utilisateur.objects.get(id=user_id)
        # Trouver la liste des admins
        admin_emails = Utilisateur.objects.filter(role__nom_role='Admin').values_list('email', flat=True)
        
        sujet = f"ALERTE SÉCURITÉ CRITIQUE - {action}"
        message = f"L'utilisateur {user.email} (ID: {user_id}) a déclenché l'alerte: {action}. IP: {ip_address}"
        
        # Envoi aux administrateurs
        send_mail(sujet, message, settings.EMAIL_HOST_USER, list(admin_emails), fail_silently=False)
        return f"Alerte sécurité envoyée à {len(admin_emails)} admins."
    except Utilisateur.DoesNotExist:
        return "Utilisateur d'alerte non trouvé."