from django.db import models
from django.utils.translation import gettext_lazy as _
# Create your models here

from django.db import models

class Materiel(models.Model):

 
    class Categorie(models.TextChoices):
        INFORMATIQUE = "INFORMATIQUE", "Informatique"
        AUDIOVISUEL  = "AUDIOVISUEL",  "Audiovisuel"
        MOBILIER     = "MOBILIER",     "Mobilier"
        RESEAU       = "RESEAU",       "Réseau & Télécommunications"
        LABORATOIRE  = "LABORATOIRE",  "Laboratoire"
        SPORT        = "SPORT",        "Sport"
        BUREAUTIQUE  = "BUREAUTIQUE",  "Bureautique"
        SECURITE     = "SECURITE",     "Sécurité"
        AUTRE        = "AUTRE",        "Autre"

    ETAT_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('EN PRET', 'En prêt'),
        ('DEFECTUEUX', 'Defectueux'),
        ('EN MAINTENANCE', 'En maintenance'),
        ('HORS SERVICE', 'Hors service'),
    ]

    id_materiel = models.CharField(max_length=50, primary_key=True, verbose_name="Identifiant")
    nom = models.CharField(max_length=100)
    couleur = models.CharField(max_length=30)
    
    categorie = models.CharField(
        max_length=50,
        choices=Categorie.choices,
        default=Categorie.AUTRE,
        verbose_name="Catégorie",
    )
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

class Classe(models.Model):
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    nombre_places = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['nom']
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
 
    def __str__(self):
        return self.nom
    
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
    classe=models.ForeignKey(Classe, on_delete=models.PROTECT, null=True, blank=True)
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
 
    
    class TypeOperation(models.TextChoices):
        ENTREE = "entree", _("Entrée (enregistrement)")
        SORTIE = "sortie", _("Sortie (planifiée)")
        EMPRUNT = "emprunt", _("Emprunt")
 
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente")
        APPROUVE = "approuve", _("Approuvé")
        REFUSE = "refuse", _("Refusé")
        RETOURNE = "retourne", _("Retourné")
 
    # Champs existants (à conserver)
    materiel = models.ForeignKey("Materiel", on_delete=models.CASCADE, related_name="emprunts")
    emprunteur = models.ForeignKey("equipement.Tierce", on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True)
    date_emprunt = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    date_retour_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE
    )
    
   
    type_operation = models.CharField(
        max_length=20,
        choices=TypeOperation.choices,
        default=TypeOperation.EMPRUNT
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-date_emprunt']
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"
 
    def __str__(self):
        return f"{self.materiel} - {self.emprunteur}"


class LigneEmprunt(models.Model):
    
    emprunt = models.ForeignKey(
        Emprunt,
        on_delete=models.CASCADE,
        related_name="lignes",
        verbose_name="Emprunt",
    )
    materiel = models.ForeignKey(
        Materiel,
        on_delete=models.PROTECT,
        related_name="lignes_emprunt",
        verbose_name="Matériel",
    )

    class Meta:
        unique_together = ("emprunt", "materiel")

    def __str__(self):
         return f"{self.materiel} dans Emprunt #{self.emprunt_id}"


