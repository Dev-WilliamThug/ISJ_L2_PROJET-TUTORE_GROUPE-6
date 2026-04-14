from django.db import models

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
