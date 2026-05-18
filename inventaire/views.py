from .models import Inventaire, LigneInventaire
from datetime import date
from django.utils import timezone
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from equipement.models import (
    Classe, 
    Emprunt, 
    Materiel
)
from users.models import CustomUser
from users.forms import LoginForm

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("inventaire:login")
        return view_func(request, *args, **kwargs)
    return _wrapped



def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.type_user == CustomUser.TypeUser.ADMIN:
            return redirect("inventaire:dashboard")
        elif request.user.type_user == CustomUser.TypeUser.MANAGER:
                return redirect("equipement:dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            password = form.cleaned_data["password"]

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                user = None

            if not user or (not user.is_active) or (not user.check_password(password)):
                messages.error(request, "Identifiants incorrects.")
            else:
                login(request, user)
            if request.user.type_user == CustomUser.TypeUser.ADMIN:
                return redirect("inventaire:dashboard")
            elif request.user.type_user == CustomUser.TypeUser.MANAGER:
                return redirect("equipement:dashboard")
    return render(request, "inventaire/login.html", {"form": form})



def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Déconnexion effectuée.")
    return redirect("inventaire:login")



@login_required
@admin_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tab = request.GET.get("tab", "home")


    context = {
        "tab": tab,
    }
    return render(request, "inventaire/dashboard.html", context)




@login_required
@admin_required
def inventaire_list(request):
    
    inventaires = Inventaire.objects.select_related('classe', 'created_by')
    
    context = {
        'inventaires': inventaires,
    }
    return render(request, 'inventaire/inventaire_list.html', context)
 
 
@login_required
@admin_required
def inventaire_form(request):
    """
    Formulaire pour sélectionner une classe et une date d'inventaire.
    """
    classes = Classe.objects.all()
    
    if request.method == "POST":
        classe_id = request.POST.get('classe')
        date_inventaire = request.POST.get('date_inventaire')
        
        if not classe_id or not date_inventaire:
            messages.error(request, "Veuillez sélectionner une classe et une date.")
            return render(request, 'inventaire/inventaire_form.html', {'classes': classes})
        
        try:
            classe = Classe.objects.get(pk=classe_id)
            # Rediriger vers la vue de détail d'inventaire
            return redirect(
                'inventaire:inventaire_detail',
                classe_id=classe_id,
                date=date_inventaire
            )
        except Classe.DoesNotExist:
            messages.error(request, "Classe non trouvée.")
    
    context = {
        'classes': classes,
        'today': date.today().isoformat(),
    }
    return render(request, 'inventaire/inventaire_form.html', context)
 
 
@login_required
@admin_required
def inventaire_detail(request, classe_id, date):
    """
    Affiche le détail de l'inventaire pour une classe et une date donnée.
    Permet de saisir les quantités empruntées et réelles.
    """
    classe = get_object_or_404(Classe, pk=classe_id)
    
    # Convertir la string date en objet date
    try:
        date_obj = timezone.datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format de date invalide.")
        return redirect('inventaire:inventaire_form')
    
    # Récupérer ou créer l'inventaire
    inventaire, created = Inventaire.objects.get_or_create(
        classe=classe,
        date_inventaire=date_obj,
        defaults={'created_by': request.user}
    )
    
    # Récupérer tous les équipements présents dans la classe
    # (groupés par catégorie au moment de la date)
    
    # Emprunts actifs pour cette classe à la date donnée
    emprunts_actifs = Emprunt.objects.filter(
        classe=classe,
        statut__in=['en_attente', 'approuve']
    ).select_related('materiel__categorie')
    
    # Compter les équipements par catégorie
    categories = Materiel.Categorie.objects.annotate(
        stock_initial=Count(
            'materiels',
            filter=Q(materiels__emprunt__classe=classe)
        )
    ).filter(materiels__emprunt__classe=classe).distinct()
    
    # Structure pour afficher les données
    inventaire_data = {}
    
    for categorie in Materiel.Categorie.objects.all():
        # Compter les équipements empruntés pour cette catégorie
        count_emprunts = emprunts_actifs.filter(
            materiel__categorie=categorie
        ).count()
        
        # Récupérer ou créer la ligne d'inventaire
        ligne, _ = LigneInventaire.objects.get_or_create(
            inventaire=inventaire,
            categorie=categorie,
            defaults={
                'stock_initial': count_emprunts,
                'stock_emprute': count_emprunts,
                'stock_reel': 0
            }
        )
        
        inventaire_data[categorie.id] = {
            'categorie': categorie,
            'stock_initial': ligne.stock_initial,
            'stock_emprute': ligne.stock_emprute,
            'stock_reel': ligne.stock_reel,
            'difference': ligne.difference,
            'ligne_id': ligne.id
        }
    
    if request.method == "POST":
        # Traiter la soumission du formulaire
        lignes = LigneInventaire.objects.filter(inventaire=inventaire)
        
        for ligne in lignes:
            stock_reel = request.POST.get(f'stock_reel_{ligne.id}')
            
            if stock_reel is not None and stock_reel != '':
                try:
                    ligne.stock_reel = int(stock_reel)
                    ligne.save()
                except ValueError:
                    messages.warning(
                        request, 
                        f"Valeur invalide pour {ligne.categorie.nom}"
                    )
        
        messages.success(
            request,
            f"Inventaire de {classe.nom} du {date_obj} enregistré avec succès."
        )
        return redirect('inventaire:inventaire_list')
    
    context = {
        'inventaire': inventaire,
        'classe': classe,
        'date': date_obj,
        'inventaire_data': inventaire_data,
    }
    return render(request, 'inventaire/inventaire_detail.html', context)
 
 
@login_required
@admin_required
def inventaire_detail_view(request, inventaire_id):
    """
    Affiche le détail d'un inventaire existant (lecture seule).
    """
    inventaire = get_object_or_404(Inventaire, pk=inventaire_id)
    lignes = inventaire.lignes.select_related('categorie')
    
    context = {
        'inventaire': inventaire,
        'lignes': lignes,
    }
    return render(request, 'inventaire/inventaire_view.html', context)
 
 
@login_required
@admin_required
@require_POST
def inventaire_delete(request, inventaire_id):
    """
    Supprime un inventaire.
    """
    inventaire = get_object_or_404(Inventaire, pk=inventaire_id)
    classe_nom = inventaire.classe.nom
    inventaire.delete()
    
    messages.success(
        request,
        f"Inventaire de {classe_nom} supprimé avec succès."
    )
    return redirect('inventaire:inventaire_list')
 
 
 