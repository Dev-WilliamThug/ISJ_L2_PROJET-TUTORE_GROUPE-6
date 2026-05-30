"""Context processor pour les notifications d'emprunts en retard."""

from django.utils import timezone
from equipement.models import Emprunt


def overdue_count(request):
    """
    Context processor qui compte les emprunts en retard.
    Disponible dans tous les templates via {{ overdue_count }}
    """
    if not request.user.is_authenticated:
        return {'overdue_count': 0}
    
    # Compter les emprunts en retard
    today = timezone.now().date()
    count = Emprunt.objects.filter(
        date_retour_prevue__lt=today,
        date_retour_reelle__isnull=True,
        statut=Emprunt.Statut.APPROUVE
    ).count()
    
    return {
        'overdue_count': count,
        'has_overdue': count > 0
    }
