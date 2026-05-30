"""Service pour gérer les rappels des emprunts en retard."""

from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Emprunt, Rappel


class ReminderService:
    """Service pour gérer les rappels des emprunts en retard."""
    
    # Configuration des jours de retard pour les rappels
    REMINDER_THRESHOLDS = {
        Rappel.TypeRappel.RETARD_1_JOUR: 1,
        Rappel.TypeRappel.RETARD_3_JOURS: 3,
        Rappel.TypeRappel.RETARD_7_JOURS: 7,
    }
    
    @staticmethod
    def get_overdue_emprunts():
        """
        Récupère tous les emprunts en retard non retournés.
        
        Returns:
            QuerySet: Les emprunts en retard
        """
        today = timezone.now().date()
        return Emprunt.objects.filter(
            date_retour_prevue__lt=today,
            date_retour_reelle__isnull=True,
            statut=Emprunt.Statut.APPROUVE
        )
    
    @staticmethod
    def get_days_overdue(emprunt):
        """
        Calcule le nombre de jours de retard pour un emprunt.
        
        Args:
            emprunt (Emprunt): L'emprunt à vérifier
            
        Returns:
            int: Nombre de jours de retard
        """
        today = timezone.now().date()
        if emprunt.date_retour_prevue:
            return (today - emprunt.date_retour_prevue).days
        return 0
    
    @staticmethod
    def should_send_reminder(emprunt, reminder_type):
        """
        Détermine si un rappel doit être envoyé pour un emprunt.
        
        Args:
            emprunt (Emprunt): L'emprunt à vérifier
            reminder_type (str): Type de rappel (RETARD_1_JOUR, RETARD_3_JOURS, etc.)
            
        Returns:
            bool: True si le rappel doit être envoyé
        """
        days_overdue = ReminderService.get_days_overdue(emprunt)
        threshold = ReminderService.REMINDER_THRESHOLDS.get(reminder_type, 0)
        
        # Vérifier si le rappel n'a pas déjà été envoyé
        reminder_exists = Rappel.objects.filter(
            emprunt=emprunt,
            type_rappel=reminder_type
        ).exists()
        
        return (days_overdue >= threshold) and (not reminder_exists)
    
    @staticmethod
    def send_reminder_email(emprunt, reminder_type):
        """
        Envoie un email de rappel pour un emprunt en retard.
        
        Args:
            emprunt (Emprunt): L'emprunt concerné
            reminder_type (str): Type de rappel
            
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        try:
            emprunteur = emprunt.emprunteur
            days_overdue = ReminderService.get_days_overdue(emprunt)
            
            # Récupérer le matériel (utiliser la première ligne d'emprunt si possible)
            materiels_list = list(emprunt.lignes.values_list('materiel__nom', flat=True))
            materiels_str = ", ".join(materiels_list) if materiels_list else "Matériel"
            
            # Construire le sujet et le message selon le type de rappel
            subject = f"Rappel : Retour de matériel en retard"
            
            message = f"""Bonjour {emprunteur.prenom} {emprunteur.nom},

Nous vous rappelons que vous avez actuellement du matériel en retard :

Matériel: {materiels_str}
Date de retour prévue: {emprunt.date_retour_prevue}
Nombre de jours de retard: {days_overdue}

Veuillez retourner le matériel au plus vite possible.

Cordialement,
{settings.DEFAULT_FROM_EMAIL}
"""
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[emprunteur.email],
                fail_silently=False,
            )
            
            # Enregistrer le rappel
            Rappel.objects.create(
                emprunt=emprunt,
                type_rappel=reminder_type,
                email_destinataire=emprunteur.email,
                statut_envoi='envoye'
            )
            
            return True
            
        except Exception as e:
            # Enregistrer l'erreur
            Rappel.objects.create(
                emprunt=emprunt,
                type_rappel=reminder_type,
                email_destinataire=emprunt.emprunteur.email,
                statut_envoi='echec',
                message_erreur=str(e)
            )
            print(f"Erreur lors de l'envoi du rappel pour {emprunt.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_all_reminders():
        """
        Envoie tous les rappels nécessaires pour les emprunts en retard.
        
        Returns:
            dict: Statistiques sur les rappels envoyés
        """
        stats = {
            'total_emprunts_en_retard': 0,
            'rappels_envoyes': 0,
            'rappels_echoues': 0,
        }
        
        overdue_emprunts = ReminderService.get_overdue_emprunts()
        stats['total_emprunts_en_retard'] = overdue_emprunts.count()
        
        for emprunt in overdue_emprunts:
            # Envoyer les rappels appropriés selon le nombre de jours de retard
            for reminder_type in ReminderService.REMINDER_THRESHOLDS.keys():
                if ReminderService.should_send_reminder(emprunt, reminder_type):
                    success = ReminderService.send_reminder_email(emprunt, reminder_type)
                    if success:
                        stats['rappels_envoyes'] += 1
                    else:
                        stats['rappels_echoues'] += 1
        
        return stats
