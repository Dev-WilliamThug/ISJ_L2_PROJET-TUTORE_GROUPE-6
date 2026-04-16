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

    def __str__(self):
        return f"{self.nom} ({self.id_materiel})"


class Tierce(models.Model):
    class TypeTierce(models.TextChoices):
        ETUDIANT = "etudiant", _("etudiant")
        PROFESSEUR = "professeur", _("professeur")

    # Le champ Python reste "id_Tierce" pour compatibilite avec le code existant,
    # mais la colonne SQL est "id_tierce" (cree par la migration 0003).
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

    def __str__(self):
        return self.nom

