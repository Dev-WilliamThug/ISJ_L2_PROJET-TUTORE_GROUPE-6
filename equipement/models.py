from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

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
    numero_serie = models.CharField(max_length=30)
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

    def est_en_pret(self) -> bool:
        return self.etat == "EN PRET"

    def est_deffectueux(self) -> bool:
        return self.etat == "DEFECTUEUX"

    def est_en_maintenance(self) -> bool:
        return self.etat == "EN MAINTENANCE"

    def est_hors_service(self) -> bool:
        return self.etat == "HORS SERVICE"

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

    @staticmethod
    def _normalize_identifiant(nom: str, numero_serie: str) -> str:
        raw_value = f"{nom.strip()} {numero_serie.strip()}"
        if not raw_value.strip():
            return ""
        normalized = slugify(raw_value, allow_unicode=False).upper()
        return normalized[:50].rstrip("-")

    @classmethod
    def generate_identifiant(cls, nom: str, numero_serie: str) -> str:
        base_id = cls._normalize_identifiant(nom, numero_serie)
        if not base_id:
            base_id = "EQ"

        candidate = base_id
        counter = 1
        while cls.objects.filter(id_materiel=candidate).exists():
            suffix = f"-{counter}"
            candidate = f"{base_id[:50-len(suffix)]}{suffix}"
            counter += 1

        return candidate

    def save(self, *args, **kwargs):
        if not self.id_materiel and self.nom and self.numero_serie:
            self.id_materiel = self.generate_identifiant(self.nom, self.numero_serie)
        super().save(*args, **kwargs)

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
        ETUDIANT   = "etudiant",   _("etudiant")
        PROFESSEUR = "professeur", _("professeur")

    id_Tierce = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Identifiant",
        db_column="id_tierce",
    )
    nom    = models.CharField(max_length=200)
    prenom = models.CharField(max_length=200)
    email  = models.EmailField(_("email address"), unique=True)
    type_Tierce = models.CharField(
        max_length=30,
        choices=TypeTierce.choices,
        default=TypeTierce.ETUDIANT,
        verbose_name="Type",
    )
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT, null=True, blank=True)

    def get_classe(self) -> str:
        return self.classe if self.classe else "Aucune classe associée"

    def get_full_name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    def est_etudiant(self) -> bool:
        return self.type_Tierce == self.TypeTierce.ETUDIANT

    def __str__(self):
        return self.get_full_name()


class Operation(models.Model):

    class TypeOperation(models.TextChoices):
        ENTREE  = "entree",  _("Entrée (enregistrement)")
        SORTIE  = "sortie",  _("Sortie (planifiée)")
        EMPRUNT = "emprunt", _("Emprunt")

    materiel = models.ForeignKey("Materiel", on_delete=models.CASCADE, related_name="operations")
    date_operation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    type_operation = models.CharField(
        max_length=30,
        choices=TypeOperation.choices,
        default=TypeOperation.EMPRUNT,
        verbose_name="Type d'opération",
    )

    class Meta:
        verbose_name = "Opération"
        verbose_name_plural = "Opérations"
        ordering = ['-date_operation']

    def __str__(self):
        return f"{self.type_operation} - {self.materiel}"


class Emprunt(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente")
        APPROUVE   = "approuve",   _("Approuvé")
        REFUSE     = "refuse",     _("Refusé")
        RETOURNE   = "retourne",   _("Retourné")

    emprunteur        = models.ForeignKey("equipement.Tierce", on_delete=models.CASCADE, related_name="emprunts")
    classe            = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    date_retour_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"

    def __str__(self):
        return f"Emprunt #{self.id} - {self.emprunteur.get_full_name()}"


class LigneEmprunt(models.Model):

    emprunt  = models.ForeignKey(Emprunt,  on_delete=models.CASCADE,  related_name="lignes",        verbose_name="Emprunt")
    materiel = models.ForeignKey(Materiel, on_delete=models.PROTECT,   related_name="lignes_emprunt", verbose_name="Matériel")

    class Meta:
        unique_together = ("emprunt", "materiel")

    def __str__(self):
        return f"{self.materiel} dans Emprunt #{self.emprunt_id}"


class Rappel(models.Model):
    """Trace tous les emails envoyés liés aux emprunts."""

    class TypeRappel(models.TextChoices):
        # Email immédiat dès le premier jour de retard (envoi automatique)
        NOUVEAU_RETARD = "nouveau_retard", _("Nouveau retard détecté")
        # Confirmation envoyé quand un emprunt est rendu
        CONFIRMATION_RETOUR = "confirmation_retour", _("Confirmation de retour")
        # Rappels périodiques
        RETARD_1_JOUR  = "retard_1",       _("1 jour de retard")
        RETARD_3_JOURS = "retard_3",       _("3 jours de retard")
        RETARD_7_JOURS = "retard_7",       _("7 jours de retard")

    emprunt = models.ForeignKey(
        Emprunt,
        on_delete=models.CASCADE,
        related_name="rappels",
        verbose_name="Emprunt",
    )
    type_rappel = models.CharField(
        max_length=20,
        choices=TypeRappel.choices,
        verbose_name="Type de rappel",
    )
    date_envoi = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    email_destinataire = models.EmailField(verbose_name="Email destinataire")
    statut_envoi = models.CharField(
        max_length=20,
        choices=[('envoye', 'Envoyé'), ('echec', 'Échec')],
        default='envoye',
        verbose_name="Statut d'envoi",
    )
    message_erreur = models.TextField(blank=True, verbose_name="Message d'erreur")

    class Meta:
        ordering = ['-date_envoi']
        verbose_name = "Rappel"
        verbose_name_plural = "Rappels"
        # Un seul rappel de chaque type par emprunt
        unique_together = ('emprunt', 'type_rappel')

    def __str__(self):
        return f"Rappel {self.get_type_rappel_display()} - {self.emprunt.emprunteur} ({self.date_envoi.date()})"