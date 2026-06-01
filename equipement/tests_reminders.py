"""Tests pour le système de rappels des emprunts en retard."""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.mail import outbox
from equipement.models import Materiel, Classe, Tierce, Emprunt, LigneEmprunt, Rappel
from equipement.reminder_service import ReminderService


class ReminderServiceTestCase(TestCase):
    """Tests pour le ReminderService."""
    
    def setUp(self):
        """Préparer les données de test."""
        # Créer une classe
        self.classe = Classe.objects.create(
            nom="Test Classe",
            nombre_places=30
        )
        
        # Créer un matériel
        self.materiel = Materiel.objects.create(
            id_materiel="TEST001",
            nom="Laptop Test",
            couleur="Noir",
            numero_serie="SN123",
            categorie="INFORMATIQUE",
            marque="Dell"
        )
        
        # Créer un emprunteur
        self.emprunteur = Tierce.objects.create(
            id_Tierce="EMP001",
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@test.com",
            type_Tierce="etudiant",
            classe=self.classe
        )
    
    def test_get_overdue_emprunts(self):
        """Test la récupération des emprunts en retard."""
        # Créer un emprunt avec une date passée
        past_date = timezone.now().date() - timedelta(days=5)
        emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=past_date,
            statut=Emprunt.Statut.APPROUVE
        )
        LigneEmprunt.objects.create(emprunt=emprunt, materiel=self.materiel)
        
        # Vérifier que l'emprunt est détecté
        overdue = ReminderService.get_overdue_emprunts()
        self.assertIn(emprunt, overdue)
    
    def test_get_days_overdue(self):
        """Test le calcul des jours de retard."""
        # Créer un emprunt en retard de 3 jours
        past_date = timezone.now().date() - timedelta(days=3)
        emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=past_date,
            statut=Emprunt.Statut.APPROUVE
        )
        
        days = ReminderService.get_days_overdue(emprunt)
        self.assertEqual(days, 3)
    
    def test_should_send_reminder_1_day(self):
        """Test l'envoi du rappel 1 jour."""
        # Emprunt en retard de 1 jour
        past_date = timezone.now().date() - timedelta(days=1)
        emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=past_date,
            statut=Emprunt.Statut.APPROUVE
        )
        
        should_send = ReminderService.should_send_reminder(
            emprunt, 
            Rappel.TypeRappel.RETARD_1_JOUR
        )
        self.assertTrue(should_send)
    
    def test_should_not_send_duplicate_reminder(self):
        """Test qu'un rappel n'est pas envoyé deux fois."""
        # Créer un emprunt en retard
        past_date = timezone.now().date() - timedelta(days=1)
        emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=past_date,
            statut=Emprunt.Statut.APPROUVE
        )
        
        # Créer un rappel existant
        Rappel.objects.create(
            emprunt=emprunt,
            type_rappel=Rappel.TypeRappel.RETARD_1_JOUR,
            email_destinataire=self.emprunteur.email
        )
        
        # Vérifier qu'on ne veut pas envoyer un autre rappel
        should_send = ReminderService.should_send_reminder(
            emprunt,
            Rappel.TypeRappel.RETARD_1_JOUR
        )
        self.assertFalse(should_send)
    
    def test_send_reminder_email(self):
        """Test l'envoi d'un email de rappel."""
        # Créer un emprunt en retard
        past_date = timezone.now().date() - timedelta(days=3)
        emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=past_date,
            statut=Emprunt.Statut.APPROUVE
        )
        LigneEmprunt.objects.create(emprunt=emprunt, materiel=self.materiel)
        
        # Envoyer le rappel
        success = ReminderService.send_reminder_email(
            emprunt,
            Rappel.TypeRappel.RETARD_3_JOURS
        )
        
        # Vérifier que l'envoi a réussi
        self.assertTrue(success)
        
        # Vérifier qu'un rappel a été créé
        rappel = Rappel.objects.get(
            emprunt=emprunt,
            type_rappel=Rappel.TypeRappel.RETARD_3_JOURS
        )
        self.assertIsNotNone(rappel)
        self.assertEqual(rappel.statut_envoi, 'envoye')
    
    def test_send_all_reminders(self):
        """Test l'envoi de tous les rappels nécessaires."""
        # Créer plusieurs emprunts en retard
        past_date_1 = timezone.now().date() - timedelta(days=1)
        past_date_3 = timezone.now().date() - timedelta(days=3)
        past_date_7 = timezone.now().date() - timedelta(days=7)
        
        for past_date in [past_date_1, past_date_3, past_date_7]:
            emprunt = Emprunt.objects.create(
                emprunteur=self.emprunteur,
                classe=self.classe,
                date_retour_prevue=past_date,
                statut=Emprunt.Statut.APPROUVE
            )
            LigneEmprunt.objects.create(emprunt=emprunt, materiel=self.materiel)
        
        # Envoyer tous les rappels
        stats = ReminderService.send_all_reminders()
        
        # Vérifier les statistiques
        self.assertEqual(stats['total_emprunts_en_retard'], 3)
        self.assertGreater(stats['rappels_envoyes'], 0)
    
    def test_emprunt_returned_not_included(self):
        """Test que les emprunts retournés ne sont pas inclus."""
        # Créer un emprunt retourné
        past_date = timezone.now().date() - timedelta(days=5)
        emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=past_date,
            date_retour_reelle=timezone.now().date(),
            statut=Emprunt.Statut.RETOURNE
        )
        
        # Vérifier que l'emprunt n'est pas en retard
        overdue = ReminderService.get_overdue_emprunts()
        self.assertNotIn(emprunt, overdue)


class RappelModelTestCase(TestCase):
    """Tests pour le modèle Rappel."""
    
    def setUp(self):
        """Préparer les données de test."""
        self.classe = Classe.objects.create(
            nom="Test Classe",
            nombre_places=30
        )
        
        self.materiel = Materiel.objects.create(
            id_materiel="TEST001",
            nom="Laptop Test",
            couleur="Noir",
            numero_serie="SN123",
            categorie="INFORMATIQUE",
            marque="Dell"
        )
        
        self.emprunteur = Tierce.objects.create(
            id_Tierce="EMP001",
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@test.com",
            type_Tierce="etudiant",
            classe=self.classe
        )
        
        self.emprunt = Emprunt.objects.create(
            emprunteur=self.emprunteur,
            classe=self.classe,
            date_retour_prevue=timezone.now().date() - timedelta(days=1),
            statut=Emprunt.Statut.APPROUVE
        )
    
    def test_rappel_creation(self):
        """Test la création d'un rappel."""
        rappel = Rappel.objects.create(
            emprunt=self.emprunt,
            type_rappel=Rappel.TypeRappel.RETARD_1_JOUR,
            email_destinataire=self.emprunteur.email,
            statut_envoi='envoye'
        )
        
        self.assertIsNotNone(rappel.id)
        self.assertEqual(rappel.emprunt, self.emprunt)
        self.assertEqual(rappel.email_destinataire, self.emprunteur.email)
    
    def test_unique_reminder_per_emprunt(self):
        """Test que seul un rappel du même type peut exister par emprunt."""
        # Créer un premier rappel
        Rappel.objects.create(
            emprunt=self.emprunt,
            type_rappel=Rappel.TypeRappel.RETARD_1_JOUR,
            email_destinataire=self.emprunteur.email,
            statut_envoi='envoye'
        )
        
        # Essayer de créer un duplicata devrait échouer
        with self.assertRaises(Exception):
            Rappel.objects.create(
                emprunt=self.emprunt,
                type_rappel=Rappel.TypeRappel.RETARD_1_JOUR,
                email_destinataire=self.emprunteur.email,
                statut_envoi='envoye'
            )
