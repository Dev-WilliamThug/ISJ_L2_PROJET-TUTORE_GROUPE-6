from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from equipement.models import Materiel, Tierce, Operation, Emprunt, Classe


class CustomUserManager(BaseUserManager):

    def create_user(self, email, nom, prenom, type_user=None, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire.")

        # On retire type_user de extra_fields s'il s'y trouve déjà (évite le doublon)
        extra_fields.pop("type_user", None)

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nom=nom,
            prenom=prenom,
            type_user=type_user or CustomUser.TypeUser.MANAGER,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, prenom, password=None, **extra_fields):
        extra_fields.pop("type_user", None)  # retire type_user s'il est déjà dans extra_fields
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True

        return self.create_user(
            email=email,
            nom=nom,
            prenom=prenom,
            type_user=CustomUser.TypeUser.ADMIN,
            password=password,
            **extra_fields,
        )


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class TypeUser(models.TextChoices):
        ADMIN = "administrateur", _("Administrateur")
        MANAGER = "gestionnaire", _("Gestionnaire")

    email = models.EmailField(_("email address"), unique=True)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    type_user = models.CharField(
        max_length=30,
        choices=TypeUser.choices,
        default=TypeUser.MANAGER
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom} <{self.email}>"

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)