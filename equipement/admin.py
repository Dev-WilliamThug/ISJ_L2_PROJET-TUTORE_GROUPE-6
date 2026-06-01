from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Materiel, Classe, Tierce, Operation, Emprunt, LigneEmprunt, Rappel


@admin.register(Materiel)
class MaterielAdmin(admin.ModelAdmin):
    list_display = ('id_materiel', 'nom', 'categorie', 'etat', 'marque')
    list_filter = ('categorie', 'etat')
    search_fields = ('id_materiel', 'nom', 'numero_serie')
    ordering = ('id_materiel',)


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nombre_places', 'created_at')
    search_fields = ('nom',)
    ordering = ('nom',)


@admin.register(Tierce)
class TierceAdmin(admin.ModelAdmin):
    list_display = ('id_Tierce', 'get_full_name', 'type_Tierce', 'email', 'classe')
    list_filter = ('type_Tierce', 'classe')
    search_fields = ('id_Tierce', 'nom', 'prenom', 'email')
    ordering = ('id_Tierce',)


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('id', 'materiel', 'type_operation', 'date_operation')
    list_filter = ('type_operation', 'date_operation')
    ordering = ('-date_operation',)


class LigneEmpruntInline(admin.TabularInline):
    model = LigneEmprunt
    extra = 1
    fields = ('materiel',)


@admin.register(Emprunt)
class EmpruntAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'emprunteur',
        'date_retour_prevue',
        'statut_couleur',
        'jours_retard_display',
        'materiels_count'
    )
    list_filter = ('statut', 'date_retour_prevue', 'created_at')
    search_fields = ('emprunteur__prenom', 'emprunteur__nom', 'emprunteur__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LigneEmpruntInline]
    fieldsets = (
        ('Informations générales', {
            'fields': ('emprunteur', 'classe', 'statut')
        }),
        ('Dates', {
            'fields': ('date_retour_prevue', 'date_retour_reelle', 'created_at', 'updated_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def statut_couleur(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'en_attente': '#FFC107',  # Jaune
            'approuve': '#28A745',    # Vert
            'refuse': '#DC3545',      # Rouge
            'retourne': '#6C757D',    # Gris
        }
        color = colors.get(obj.statut, '#000000')
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_couleur.short_description = 'Statut'
    
    def jours_retard_display(self, obj):
        """Affiche le nombre de jours de retard si applicable."""
        from django.utils import timezone
        
        if obj.date_retour_reelle or obj.statut == 'retourne':
            return '-'
        
        today = timezone.now().date()
        if obj.date_retour_prevue and obj.date_retour_prevue < today:
            days = (today - obj.date_retour_prevue).days
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">{}j</span>',
                days
            )
        return '-'
    jours_retard_display.short_description = 'Retard'
    
    def materiels_count(self, obj):
        """Affiche le nombre de matériels empruntés."""
        count = obj.lignes.count()
        return count
    materiels_count.short_description = 'Matériels'


@admin.register(Rappel)
class RappelAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'emprunt',
        'type_rappel',
        'email_destinataire',
        'statut_couleur',
        'date_envoi'
    )
    list_filter = ('type_rappel', 'statut_envoi', 'date_envoi')
    search_fields = ('email_destinataire', 'emprunt__emprunteur__email')
    readonly_fields = ('date_envoi', 'emprunt_link', 'message_erreur')
    ordering = ('-date_envoi',)
    
    def statut_couleur(self, obj):
        """Affiche le statut avec une couleur."""
        if obj.statut_envoi == 'envoye':
            color = '#28A745'  # Vert
            text = '✓ Envoyé'
        else:
            color = '#DC3545'  # Rouge
            text = '✗ Échec'
        
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            color,
            text
        )
    statut_couleur.short_description = 'Statut'
    
    def emprunt_link(self, obj):
        """Affiche un lien vers l'emprunt."""
        url = reverse('admin:equipement_emprunt_change', args=[obj.emprunt.id])
        return format_html('<a href="{}">{}</a>', url, obj.emprunt)
    emprunt_link.short_description = 'Emprunt'
