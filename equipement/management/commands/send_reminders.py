"""Commande Django pour envoyer les rappels des emprunts en retard."""

from django.core.management.base import BaseCommand
from equipement.reminder_service import ReminderService


class Command(BaseCommand):
    help = 'Envoie les rappels pour les emprunts dont la date de retour est dépassée'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche des informations détaillées sur l\'exécution'
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS('Début de l\'envoi des rappels...'))
        
        try:
            stats = ReminderService.send_all_reminders()
            
            self.stdout.write(
                self.style.SUCCESS(f'\nRésumé:')
            )
            self.stdout.write(f'  Emprunts en retard: {stats["total_emprunts_en_retard"]}')
            self.stdout.write(f'  Rappels envoyés: {stats["rappels_envoyes"]}')
            
            if stats['rappels_echoues'] > 0:
                self.stdout.write(
                    self.style.WARNING(f'  Rappels échoués: {stats["rappels_echoues"]}')
                )
            
            self.stdout.write(self.style.SUCCESS('\nEnvoi des rappels terminé avec succès!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de l\'envoi des rappels: {str(e)}')
            )
