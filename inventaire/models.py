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

