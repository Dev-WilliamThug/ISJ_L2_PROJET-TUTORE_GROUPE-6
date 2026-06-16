"""Service pour gérer les rappels et emails liés aux emprunts."""

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Emprunt, Rappel


class ReminderService:

    REMINDER_THRESHOLDS = {
        Rappel.TypeRappel.RETARD_1_JOUR:  1,
        Rappel.TypeRappel.RETARD_3_JOURS: 3,
        Rappel.TypeRappel.RETARD_7_JOURS: 7,
    }

    # ------------------------------------------------------------------ #
    #  Requêtes                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_overdue_emprunts():
        """Emprunts approuvés dont la date de retour est dépassée et non encore rendus."""
        today = timezone.now().date()
        return (
            Emprunt.objects
            .filter(
                date_retour_prevue__lt=today,
                date_retour_reelle__isnull=True,
                statut=Emprunt.Statut.APPROUVE,
            )
            .select_related("emprunteur")
            .prefetch_related("lignes__materiel")
        )

    @staticmethod
    def get_days_overdue(emprunt):
        """Nombre de jours de retard pour un emprunt."""
        today = timezone.now().date()
        if emprunt.date_retour_prevue:
            return (today - emprunt.date_retour_prevue).days
        return 0

    @staticmethod
    def _get_materiels_str(emprunt):
        noms = list(emprunt.lignes.values_list("materiel__nom", flat=True))
        return ", ".join(noms) if noms else "Matériel non précisé"

    @staticmethod
    def _rappel_already_sent(emprunt, reminder_type):
        return Rappel.objects.filter(emprunt=emprunt, type_rappel=reminder_type).exists()

    @staticmethod
    def _save_rappel(emprunt, reminder_type, success, error=""):
        """Enregistre le résultat d'un envoi dans la table Rappel."""
        try:
            Rappel.objects.get_or_create(
                emprunt=emprunt,
                type_rappel=reminder_type,
                defaults={
                    "email_destinataire": emprunt.emprunteur.email,
                    "statut_envoi": "envoye" if success else "echec",
                    "message_erreur": error,
                },
            )
        except Exception as e:
            print(f"[ReminderService] Impossible de sauvegarder le rappel : {e}")

    # ------------------------------------------------------------------ #
    #  OPTION B — déclenchement automatique au chargement de page         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def check_and_notify_new_overdue():
        """
        À appeler dans les vues dashboard et overdue_emprunts.

        Pour chaque emprunt qui vient de passer en retard et qui n'a pas
        encore reçu de notification NOUVEAU_RETARD, on envoie l'email
        immédiatement et on trace l'envoi en base pour ne plus le renvoyer.

        Retourne le nombre d'emails envoyés (utile pour les logs).
        """
        sent = 0
        for emprunt in ReminderService.get_overdue_emprunts():
            if not ReminderService._rappel_already_sent(
                emprunt, Rappel.TypeRappel.NOUVEAU_RETARD
            ):
                success = ReminderService._send_email(
                    destinataire=emprunt.emprunteur.email,
                    subject="⏰ Votre emprunt est en retard",
                    message=(
                        f"Bonjour {emprunt.emprunteur.prenom} {emprunt.emprunteur.nom},\n\n"
                        f"La date de retour de votre emprunt est dépassée.\n\n"
                        f"  Matériel    : {ReminderService._get_materiels_str(emprunt)}\n"
                        f"  Date prévue : {emprunt.date_retour_prevue}\n\n"
                        f"Veuillez retourner le matériel dès que possible.\n\n"
                        f"Cordialement,\nL'équipe de gestion des équipements"
                    ),
                )
                ReminderService._save_rappel(
                    emprunt, Rappel.TypeRappel.NOUVEAU_RETARD, success
                )
                if success:
                    sent += 1
        return sent

    # ------------------------------------------------------------------ #
    #  Rappels périodiques (bouton manuel ou cron)                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def should_send_reminder(emprunt, reminder_type):
        days_overdue = ReminderService.get_days_overdue(emprunt)
        threshold = ReminderService.REMINDER_THRESHOLDS.get(reminder_type, 0)
        return (days_overdue >= threshold) and (
            not ReminderService._rappel_already_sent(emprunt, reminder_type)
        )

    @staticmethod
    def send_reminder_email(emprunt, reminder_type):
        """Envoie un rappel périodique et trace le résultat."""
        days_overdue = ReminderService.get_days_overdue(emprunt)
        materiels_str = ReminderService._get_materiels_str(emprunt)
        emprunteur = emprunt.emprunteur

        success = ReminderService._send_email(
            destinataire=emprunteur.email,
            subject="⚠️ Rappel : Retour de matériel en retard",
            message=(
                f"Bonjour {emprunteur.prenom} {emprunteur.nom},\n\n"
                f"Rappel : vous avez du matériel en retard de retour.\n\n"
                f"  Matériel        : {materiels_str}\n"
                f"  Date prévue     : {emprunt.date_retour_prevue}\n"
                f"  Jours de retard : {days_overdue}\n\n"
                f"Merci de retourner le matériel dès que possible.\n\n"
                f"Cordialement,\nL'équipe de gestion des équipements"
            ),
        )
        ReminderService._save_rappel(emprunt, reminder_type, success)
        return success

    @staticmethod
    def send_all_reminders():
        """Envoie tous les rappels périodiques nécessaires (manuel / cron)."""
        stats = {
            "total_emprunts_en_retard": 0,
            "rappels_envoyes": 0,
            "rappels_echoues": 0,
        }

        overdue = ReminderService.get_overdue_emprunts()
        stats["total_emprunts_en_retard"] = overdue.count()

        for emprunt in overdue:
            for reminder_type in ReminderService.REMINDER_THRESHOLDS:
                if ReminderService.should_send_reminder(emprunt, reminder_type):
                    if ReminderService.send_reminder_email(emprunt, reminder_type):
                        stats["rappels_envoyes"] += 1
                    else:
                        stats["rappels_echoues"] += 1

        return stats

    # ------------------------------------------------------------------ #
    #  Email : confirmation de retour                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def send_return_confirmation(emprunt):
        """Email envoyé quand un emprunt est marqué comme rendu."""
        emprunteur = emprunt.emprunteur
        success = ReminderService._send_email(
            destinataire=emprunteur.email,
            subject="✅ Retour de matériel enregistré",
            message=(
                f"Bonjour {emprunteur.prenom} {emprunteur.nom},\n\n"
                f"Le retour de votre emprunt a bien été enregistré.\n\n"
                f"  Matériel       : {ReminderService._get_materiels_str(emprunt)}\n"
                f"  Date de retour : {emprunt.date_retour_reelle}\n\n"
                f"Merci pour votre coopération.\n\n"
                f"Cordialement,\nL'équipe de gestion des équipements"
            ),
        )

        # Enregistrer le rappel de confirmation de retour
        try:
            ReminderService._save_rappel(
                emprunt, Rappel.TypeRappel.CONFIRMATION_RETOUR, success
            )
        except Exception:
            # _save_rappel gère déjà les exceptions mais on protège l'appelant
            pass
        return success

    # ------------------------------------------------------------------ #
    #  Méthode interne d'envoi                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _send_email(destinataire, subject, message):
        """Envoie un email. Retourne True si succès, False sinon."""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinataire],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"[ReminderService] Erreur envoi email à {destinataire} : {e}")
            return False