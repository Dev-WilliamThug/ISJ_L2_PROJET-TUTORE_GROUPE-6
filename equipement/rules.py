from django.db.models import Q

from .models import Emprunt


def materiel_a_un_emprunt_en_cours(materiel) -> bool:
    return Emprunt.objects.filter(
        Q(lignes__materiel=materiel) | Q(materiels=materiel),
        statut__in=[Emprunt.Statut.EN_ATTENTE, Emprunt.Statut.APPROUVE],
        date_retour_reelle__isnull=True,
    ).exists()
