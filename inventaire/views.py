from .models import Inventaire
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
from django.db.models import Q, Count
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
            return redirect(f"{reverse('users:dashboard')}?tab=dashboard")
        elif request.user.type_user == CustomUser.TypeUser.MANAGER:
                return redirect(f"{reverse("equipement:dashboard")}?tab=dashboard")
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
                return redirect(f"{reverse('users:dashboard')}?tab=dashboard")
            elif request.user.type_user == CustomUser.TypeUser.MANAGER:
                return redirect(f"{reverse('equipement:dashboard')}?tab=dashboard")
    return render(request, "inventaire/login.html", {"form": form})



def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Déconnexion effectuée.")
    return redirect("inventaire:login")



@login_required
@admin_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tab = request.GET.get("tab", "home")
    inventaires = Inventaire.objects.select_related("classe").all()

    context = {
        "tab": tab,
        "inventaires": inventaires,
    }
    return render(request, "inventaire/dashboard.html", context)

def create_inventaire (request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        classe=request.POST.get("classe")
        date_inventaire = request.POST.get("date_inventaire")
        if not date_inventaire or not classe:
            messages.error(request, "La date et la classe de l'inventaire sont requises.")
            return redirect(reverse("inventaire:dashboard") + "?tab=inventaires")

        try:
            date_inventaire = timezone.datetime.strptime(date_inventaire, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Format de date invalide. Utilisez AAAA-MM-JJ.")
            return redirect(reverse("inventaire:dashboard") + "?tab=inventaires")

        if Inventaire.objects.filter(date_inventaire=date_inventaire, classe_id=int(classe)).exists():
            messages.error(request, "Un inventaire pour cette date existe déjà.")
            return redirect(reverse("inventaire:dashboard") + "?tab=inventaires")
        
        emprunts_classe=Emprunt.objects.filter(classe_id=int(classe), date_operation__date=date_inventaire) 
        if emprunts_classe.exists():
            try:
                nouvel_inventaire = Inventaire.objects.create(
                    classe_id=int(classe),
                    date_inventaire=date_inventaire,
                    created_by=request.user,
                    date_creation=timezone.now(),
                )
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de l'inventaire : {str(e)}")
                return redirect(reverse("inventaire:dashboard") + "?tab=inventaires")
            messages.success(request, "Inventaire créé avec succès.")
            return redirect("inventaire:inventaire_detail", inventaire_id=nouvel_inventaire.id)
        else:
            messages.error(request, "Aucun emprunt pour cette classe à cette date. Inventaire non créé.")

    context={
        "classes": Classe.objects.all()
             }
    return render(request,"inventaire/inventaire_form.html",context)


def inventaire_detail(request: HttpRequest, inventaire_id: int) -> HttpResponse:
    inventaire = get_object_or_404(Inventaire, id=inventaire_id)
    emprunts = Emprunt.objects.filter(classe=inventaire.classe, date_operation__date=inventaire.date_inventaire)
    classe=inventaire.classe
    context = {
        "inventaire": inventaire,
        "emprunts": emprunts,
        "classe": classe,
    }
    return render(request, "inventaire/inventaire_detail.html", context)
