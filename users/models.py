from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from equipement.models import Materiel,Tierce


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
