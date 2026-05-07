from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here

from django.db import models

class Materiel(models.Model):
    id_materiel = models.CharField(max_length=50, primary_key=True, verbose_name="Identifiant")
    nom = models.CharField(max_length=100)
    couleur = models.CharField(max_length=30)
    categorie = models.CharField(max_length=50)
    
    ETAT_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('EN PRET', 'En prêt'),
        ('DEFECTUEUX', 'Defectueux'),
        ('EN MAINTENANCE', 'En maintenance'),
        ('HORS SERVICE', 'Hors service'),
    ]
    etat = models.CharField(
        max_length=14,
        choices=ETAT_CHOICES,
        default='DISPONIBLE',
        verbose_name="État"
    )
    marque = models.CharField(max_length=50)

    def est_disponible(self) -> bool:
        return self.etat == "DISPONIBLE"

    def mettre_en_pret(self) -> None:
        if not self.est_disponible():
            raise ValueError(f"Le matériel {self.nom} n'est pas disponible.")
        self.etat = "EN PRET"
        self.save()

    def retourner(self) -> None:
        self.etat = "DISPONIBLE"
        self.save()

    def __str__(self):
        return f"{self.nom} ({self.id_materiel})"


class Tierce(models.Model):
    
    class TypeTierce(models.TextChoices):
        ETUDIANT = "etudiant", _("etudiant")
        PROFESSEUR = "professeur", _("professeur")

    id_Tierce = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Identifiant",
        db_column="id_tierce",
    )
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200)
    email = models.EmailField(_("email address"), unique=True)
    type_Tierce = models.CharField(
        max_length=30,
        choices=TypeTierce.choices,
        default=TypeTierce.ETUDIANT,
        verbose_name="Type",
    )
    def get_full_name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    def est_etudiant(self) -> bool:
        return self.type_Tierce == self.TypeTierce.ETUDIANT

    @property
    def nb_emprunts_en_cours(self) -> int:
        return self.emprunts.filter(statut="EN_COURS").count()

    def __str__(self):
        return self.get_full_name()

class Emprunt(models.Model):

    class Statut(models.TextChoices):
        EN_COURS = "EN_COURS", _("En cours")
        RETOURNE = "RETOURNE", _("Retourné")
        EN_RETARD = "EN_RETARD", _("En retard")
        EN_ATTENTE ="EN_ATTENTE", _("En attente")

    materiel = models.ForeignKey(
        Materiel,
        on_delete=models.PROTECT,  # on ne supprime pas un matériel en cours de prêt
        related_name="emprunts",
        verbose_name="Matériel",
    )
    emprunteur = models.ForeignKey(
        Tierce,
        on_delete=models.PROTECT,
        related_name="emprunts",
        verbose_name="Emprunteur",
    )
    date_emprunt = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField(verbose_name="Retour prévu")
    date_retour_effective = models.DateField(null=True, blank=True, verbose_name="Retour effectif")
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_COURS,
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    def __str__(self):
        return f"{self.materiel} → {self.emprunteur} ({self.statut})"