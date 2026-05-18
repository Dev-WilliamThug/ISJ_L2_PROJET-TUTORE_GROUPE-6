import secrets
import string
from .models import Inventaire, LigneInventaire
from datetime import date
from django.utils import timezone
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import LoginForm, RegisterUserForm, EditUserForm
from .models import CustomUser
from equipement.models import (
    Classe, 
    Emprunt, 
    Materiel
)



def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits 
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
        
        ):
            return pwd





def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        return view_func(request, *args, **kwargs)
    return _wrapped



def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.type_user == CustomUser.TypeUser.ADMIN:
            return redirect("users:dashboard")
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
                return redirect("users:dashboard")
            elif request.user.type_user == CustomUser.TypeUser.MANAGER:
                return redirect("equipement:dashboard")
    return render(request, "users/login.html", {"form": form})



def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Déconnexion effectuée.")
    return redirect("users:login")



@login_required
@admin_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tab = request.GET.get("tab", "home")

    active_users = CustomUser.objects.filter(is_active=True).order_by("id")
    disabled_users = CustomUser.objects.filter(is_active=False).order_by("id")
    emprunts_en_attente = Emprunt.objects.select_related(
        "materiel",
        "emprunteur",
    ).prefetch_related("lignes__materiel").filter(
        statut=Emprunt.Statut.EN_ATTENTE
    ).order_by("-date_emprunt")

    form = RegisterUserForm()

    if request.method == "POST":
        if request.POST.get("action") == "register":
            form = RegisterUserForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        user = form.save(commit=False)
                        plain_password = _generate_password()
                        user.set_password(plain_password)
                        user.save()

                        
                        email_dest = user.email
                        prenom = user.prenom
                        nom = user.nom

                       
                        pwd_copy = plain_password

                        def send_email_after_commit():
                            send_mail(
                                "Bienvenue – vos identifiants de connexion",
                                (
                                    f"Bonjour {prenom} {nom},\n\n"
                                    f"Un compte a été créé pour vous.\n\n"
                                    f"Email    : {email_dest}\n"
                                    f"Mot de passe : {pwd_copy}\n\n"
                                    f"avec nos futures améliorations vous pourrez bientot pouvoir le personnaliser"
                                    f"dès votre première connexion.\n\n"
                                    f"Cordialement,\nL'équipe d'administration"
                                ),
                                settings.DEFAULT_FROM_EMAIL,
                                [email_dest],
                                fail_silently=True,
                            )

                        transaction.on_commit(send_email_after_commit)

                        # 6. Effacer la variable pour qu'elle ne persiste pas en mémoire
                        del plain_password

                    messages.success(
                        request,
                        f"Utilisateur {user.prenom} {user.nom} enregistré avec succès. "
                        f"Un email contenant ses identifiants a été envoyé à {user.email}.",
                    )
                    return redirect(f"{reverse('users:dashboard')}?tab=active")

                except Exception as exc:
                    messages.error(
                        request,
                        f"Erreur lors de l'enregistrement ou de l'envoi de l'email : {exc}",
                    )
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    context = {
        "tab": tab,
        "form": form,
        "active_users": active_users,
        "disabled_users": disabled_users,
        "emprunts_en_attente": emprunts_en_attente,
        "statuts_emprunt": Emprunt.Statut.choices,
    }
    return render(request, "users/dashboard.html", context)



@login_required
@admin_required
def edit_user(request: HttpRequest, user_id: int) -> HttpResponse:
    """
    Permet de modifier les informations d'un utilisateur (nom, prénom, email, type).
    Le mot de passe n'est PAS modifié ici.
    """
    target = get_object_or_404(CustomUser, pk=user_id)

    if request.method == "POST":
        form = EditUserForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Les informations de {target.prenom} {target.nom} ont été mises à jour.",
            )
            return redirect(f"{reverse('users:dashboard')}?tab=active")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = EditUserForm(instance=target)

    return render(request, "users/edit_user.html", {"form": form, "target": target})



@require_POST
@login_required
@admin_required
def deactivate_user(request: HttpRequest, user_id: int) -> HttpResponse:
    target = get_object_or_404(CustomUser, pk=user_id)

    if target == request.user:
        messages.error(request, "Vous ne pouvez pas vous désactiver vous-même.")
        return redirect(f"{reverse('users:dashboard')}?tab=active")

    if target.is_active:
        target.is_active = False
        target.save(update_fields=["is_active"])

    messages.success(request, "Utilisateur désactivé.")
    return redirect(f"{reverse('users:dashboard')}?tab=disabled")



@require_POST
@login_required
@admin_required
def activate_user(request: HttpRequest, user_id: int) -> HttpResponse:
    target = get_object_or_404(CustomUser, pk=user_id)

    if not target.is_active:
        target.is_active = True
        target.save(update_fields=["is_active"])

    messages.success(request, "Utilisateur activé.")
    return redirect(f"{reverse('users:dashboard')}?tab=active")

@login_required
@admin_required
def inventaire_list(request):
    
    inventaires = Inventaire.objects.select_related('classe', 'created_by')
    
    context = {
        'inventaires': inventaires,
    }
    return render(request, 'users/inventaire_list.html', context)
 
 
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
            return render(request, 'users/inventaire_form.html', {'classes': classes})
        
        try:
            classe = Classe.objects.get(pk=classe_id)
            # Rediriger vers la vue de détail d'inventaire
            return redirect(
                'users:inventaire_detail',
                classe_id=classe_id,
                date=date_inventaire
            )
        except Classe.DoesNotExist:
            messages.error(request, "Classe non trouvée.")
    
    context = {
        'classes': classes,
        'today': date.today().isoformat(),
    }
    return render(request, 'users/inventaire_form.html', context)
 
 
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
        return redirect('users:inventaire_form')
    
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
    categories = Categorie.objects.annotate(
        stock_initial=Count(
            'materiels',
            filter=Q(materiels__emprunt__classe=classe)
        )
    ).filter(materiels__emprunt__classe=classe).distinct()
    
    # Structure pour afficher les données
    inventaire_data = {}
    
    for categorie in Categorie.objects.all():
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
        return redirect('users:inventaire_list')
    
    context = {
        'inventaire': inventaire,
        'classe': classe,
        'date': date_obj,
        'inventaire_data': inventaire_data,
    }
    return render(request, 'users/inventaire_detail.html', context)
 
 
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
    return render(request, 'users/inventaire_view.html', context)
 
 
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
    return redirect('users:inventaire_list')
 
 
 