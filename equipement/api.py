"""
API REST pour le système de rappels (Optionnel).
Nécessite: pip install djangorestframework

Pour utiliser:
1. Ajouter 'rest_framework' à INSTALLED_APPS dans settings.py
2. Inclure les URLs dans config/urls.py
3. Importer cette classe depuis equipement/serializers.py
"""

try:
    from rest_framework import serializers, viewsets, status
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from rest_framework.permissions import IsAuthenticated
    from .models import Rappel, Emprunt
    from .reminder_service import ReminderService
    
    REST_FRAMEWORK_AVAILABLE = True
except ImportError:
    REST_FRAMEWORK_AVAILABLE = False
    print("Warning: Django REST Framework not installed. API endpoints will not work.")


if REST_FRAMEWORK_AVAILABLE:
    
    class RappelSerializer(serializers.ModelSerializer):
        """Sérialiseur pour le modèle Rappel."""
        emprunteur_name = serializers.CharField(
            source='emprunt.emprunteur.get_full_name',
            read_only=True
        )
        emprunt_id = serializers.IntegerField(source='emprunt.id', read_only=True)
        
        class Meta:
            model = Rappel
            fields = [
                'id', 'emprunt_id', 'emprunteur_name', 'type_rappel',
                'email_destinataire', 'date_envoi', 'statut_envoi',
                'message_erreur'
            ]
            read_only_fields = ['date_envoi']
    
    
    class OverdueEmpruntSerializer(serializers.ModelSerializer):
        """Sérialiseur pour les emprunts en retard."""
        emprunteur_name = serializers.CharField(
            source='emprunteur.get_full_name',
            read_only=True
        )
        days_overdue = serializers.SerializerMethodField()
        materiels = serializers.SerializerMethodField()
        
        class Meta:
            model = Emprunt
            fields = [
                'id', 'emprunteur_name', 'date_retour_prevue',
                'days_overdue', 'materiels', 'statut'
            ]
        
        def get_days_overdue(self, obj):
            return ReminderService.get_days_overdue(obj)
        
        def get_materiels(self, obj):
            return [ligne.materiel.nom for ligne in obj.lignes.all()]
    
    
    class RappelViewSet(viewsets.ModelViewSet):
        """
        API ViewSet pour gérer les rappels.
        
        Endpoints disponibles:
        - GET /api/rappels/ - Lister les rappels
        - GET /api/rappels/{id}/ - Détails d'un rappel
        - GET /api/rappels/overdue/ - Lister les emprunts en retard
        - POST /api/rappels/send/ - Envoyer les rappels
        """
        queryset = Rappel.objects.all().select_related(
            'emprunt', 'emprunt__emprunteur'
        ).order_by('-date_envoi')
        serializer_class = RappelSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            """Filtrer les rappels selon l'utilisateur."""
            queryset = super().get_queryset()
            
            # Filtrer par type de rappel
            type_rappel = self.request.query_params.get('type_rappel')
            if type_rappel:
                queryset = queryset.filter(type_rappel=type_rappel)
            
            # Filtrer par statut
            statut = self.request.query_params.get('statut')
            if statut:
                queryset = queryset.filter(statut_envoi=statut)
            
            return queryset
        
        @action(detail=False, methods=['get'])
        def overdue(self, request):
            """Retourner les emprunts en retard."""
            overdue_emprunts = ReminderService.get_overdue_emprunts()
            serializer = OverdueEmpruntSerializer(
                overdue_emprunts,
                many=True
            )
            return Response({
                'count': len(overdue_emprunts),
                'emprunts': serializer.data
            })
        
        @action(detail=False, methods=['post'])
        def send(self, request):
            """Envoyer les rappels."""
            try:
                stats = ReminderService.send_all_reminders()
                return Response({
                    'success': True,
                    'message': 'Rappels envoyés avec succès',
                    'stats': stats
                })
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        @action(detail=False, methods=['get'])
        def stats(self, request):
            """Retourner les statistiques des rappels."""
            overdue = ReminderService.get_overdue_emprunts()
            total_sent = Rappel.objects.filter(
                statut_envoi='envoye'
            ).count()
            total_failed = Rappel.objects.filter(
                statut_envoi='echec'
            ).count()
            
            return Response({
                'total_overdue': overdue.count(),
                'total_reminders_sent': total_sent,
                'total_reminders_failed': total_failed,
                'success_rate': (total_sent / (total_sent + total_failed) * 100
                               if (total_sent + total_failed) > 0 else 0)
            })


# Si DRF est installé, enregistrer le ViewSet
if REST_FRAMEWORK_AVAILABLE:
    from rest_framework.routers import DefaultRouter
    
    router = DefaultRouter()
    router.register(r'rappels', RappelViewSet)
    
    urlpatterns = router.urls
else:
    urlpatterns = []
