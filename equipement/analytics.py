import json

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

from .models import Emprunt, LigneEmprunt, Materiel


def _chart_payload(labels, values):
    return {
        "labels": list(labels),
        "values": list(values),
    }


def get_admin_chart_data():
    top_materiels = (
        LigneEmprunt.objects.values("materiel__nom")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )

    renouvellement = (
        Materiel.objects.annotate(total_emprunts=Count("lignes_emprunt"))
        .filter(
            Q(total_emprunts__gte=3)
            | Q(etat__in=["DEFECTUEUX", "EN MAINTENANCE", "HORS SERVICE"])
        )
        .order_by("-total_emprunts", "nom")[:8]
    )

    utilisation = (
        Emprunt.objects.annotate(month=TruncMonth("date_operation"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    top_emprunteurs = (
        LigneEmprunt.objects.values(
            "emprunt__emprunteur__prenom",
            "emprunt__emprunteur__nom",
        )
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )

    utilisation_labels = [
        row["month"].strftime("%m/%Y") if row["month"] else "Non renseigne"
        for row in utilisation
    ]
    utilisation_values = [row["total"] for row in utilisation]

    data = {
        "top_materiels": _chart_payload(
            [row["materiel__nom"] or "Non renseigne" for row in top_materiels],
            [row["total"] for row in top_materiels],
        ),
        "renouvellement": _chart_payload(
            [materiel.nom for materiel in renouvellement],
            [materiel.total_emprunts for materiel in renouvellement],
        ),
        "utilisation": _chart_payload(utilisation_labels, utilisation_values),
        "top_emprunteurs": _chart_payload(
            [
                f"{row['emprunt__emprunteur__prenom'] or ''} {row['emprunt__emprunteur__nom'] or ''}".strip()
                or "Non renseigne"
                for row in top_emprunteurs
            ],
            [row["total"] for row in top_emprunteurs],
        ),
    }

    return {
        "admin_chart_data": data,
        "admin_chart_data_json": json.dumps(data).replace("</", "<\\/"),
    }
