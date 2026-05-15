from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from equipement.models import Materiel,Tierce,Emprunt,Classe 
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, nom, prenom, type_user, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire.")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nom=nom,
            prenom=prenom,
            type_user=type_user,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            # Un mot de passe vide ne doit pas arriver en prod.
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, prenom, password=None, **extra_fields):
        extra_fields.setdefault("type_user", "administrateur")
        extra_fields["is_staff"] = True      # ← ajouter
        return self.create_user(email, nom, prenom, type_user="administrateur", password=password, **extra_fields)
    
    


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class TypeUser(models.TextChoices):
        ADMIN = "administrateur", _("Administrateur")
        MANAGER = "gestionnaire", _("Gestionnaire")

    email = models.EmailField(_("email address"), unique=True)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    type_user = models.CharField(max_length=30, choices=TypeUser.choices, default=TypeUser.MANAGER)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom} <{self.email}>"

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)


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