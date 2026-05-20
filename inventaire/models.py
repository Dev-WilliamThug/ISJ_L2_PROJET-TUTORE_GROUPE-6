from django.db import models
from django.utils import timezone

from equipement.models import Classe

# Create your models here.
class Inventaire(models.Model):

    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name="inventaires")
    date_inventaire = models.DateField(default=timezone.now)
    created_by = models.ForeignKey("users.CustomUser", on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
 
    class Meta:
        ordering = ['-date_inventaire']
        unique_together = ('classe', 'date_inventaire')
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaires"
 
    def __str__(self):
        return f"Inventaire {self.classe.nom} - {self.date_inventaire}"

class LigneInventaire(models.Model):
   
    inventaire = models.ForeignKey(Inventaire, on_delete=models.CASCADE, related_name="lignes")
    stock_initial = models.IntegerField(help_text="Stock initial dans la classe")
    stock_emprute = models.IntegerField(default=0, help_text="Nombre d'équipements empruntés")
    stock_reel = models.IntegerField(help_text="Nombre d'équipements réellement présents")
    difference = models.IntegerField(
        editable=False,
        help_text="Différence entre stock initial et stock réel"
    )
    
    class Meta:
        #ordering = ['categorie']
        #unique_together = ('inventaire', 'categorie')
        verbose_name = "Ligne d'inventaire"
        verbose_name_plural = "Lignes d'inventaire"
 
    def save(self, *args, **kwargs):
        # Calculer la différence automatiquement
        self.difference = self.stock_initial - self.stock_reel
        super().save(*args, **kwargs)
 
    def __str__(self):
        return f"{self.inventaire} - {self.categorie.nom}"   