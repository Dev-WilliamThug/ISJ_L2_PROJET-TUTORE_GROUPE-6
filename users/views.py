import secrets
import string
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

from inventaire.models import Inventaire
from .forms import LoginForm, RegisterUserForm, EditUserForm, ClasseForm
from .models import CustomUser
from equipement.models import (
    Classe,
    Emprunt,
    Materiel,
)
from equipement.analytics import get_admin_chart_data



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
            return redirect(f"{reverse('users:dashboard')}?tab=dashboard")
        elif request.user.type_user == CustomUser.TypeUser.MANAGER:
            return redirect(f"{reverse('equipement:dashboard')}?tab=dashboard")

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
                if user.type_user == CustomUser.TypeUser.ADMIN:
                    return redirect(f"{reverse('users:dashboard')}?tab=dashboard")
                elif user.type_user == CustomUser.TypeUser.MANAGER:
                    return redirect(f"{reverse('equipement:dashboard')}?tab=dashboard")

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
    inventaires = Inventaire.objects.select_related("classe").all()
    classes = Classe.objects.all()
    emprunts_en_attente = Emprunt.objects.select_related(
        "materiels",
        "emprunteur",
    ).prefetch_related("lignes__materiel").filter(
        statut=Emprunt.Statut.EN_ATTENTE
    ).order_by("-date_operation")

    form = RegisterUserForm()
    classe_form = ClasseForm()

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
                    prenom     = user.prenom
                    nom        = user.nom

                    send_mail(
                        subject="Bienvenue – vos identifiants de connexion",
                        message=(
                            f"Bonjour {prenom} {nom},\n\n"
                            f"Un compte a été créé pour vous sur la plateforme de gestion.\n\n"
                            f"Vos identifiants de connexion :\n"
                            f"  Email        : {email_dest}\n"
                            f"  Mot de passe : {plain_password}\n\n"
                            f"Nous vous conseillons de conserver ces informations en lieu sûr.\n\n"
                            f"Cordialement,\n"
                            f"L'équipe d'administration"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email_dest],
                        fail_silently=False,
                    )

                    messages.success(
                        request,
                        f"Utilisateur {prenom} {nom} enregistré avec succès. "
                        f"Un email contenant ses identifiants a été envoyé à {email_dest}.",
                    )
                    return redirect(f"{reverse('users:dashboard')}?tab=utilisateur/actifs")

                except Exception as exc:
                    messages.error(
                        request,
                        f"Erreur lors de l'envoi de l'email : {exc}. "
                        f"Le compte a bien été créé mais le gestionnaire n'a pas reçu ses identifiants — "
                        f"transmettez-les lui manuellement.",
                    )
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")

        elif request.POST.get("action") == "register_classe":
            classe_form = ClasseForm(request.POST)
            if classe_form.is_valid():
                classe = classe_form.save()
                messages.success(request, f"Classe « {classe.nom} » créée avec succès.")
                return redirect(f"{reverse('users:dashboard')}?tab=classes/liste")
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")
                return redirect(f"{reverse('users:dashboard')}?tab=classes/creer")

    context = {
        "tab": tab,
        "form": form,
        "classe_form": classe_form,
        "active_users": active_users,
        "disabled_users": disabled_users,
        "emprunts_en_attente": emprunts_en_attente,
        "statuts_emprunt": Emprunt.Statut.choices,
        "inventaires": inventaires,
        "classes": classes,
    }
    context.update(get_admin_chart_data())
    return render(request, "users/dashboard.html", context)


@login_required
@admin_required
def edit_user(request: HttpRequest, user_id: int) -> HttpResponse:
    target = get_object_or_404(CustomUser, pk=user_id)

    if request.method == "POST":
        form = EditUserForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Les informations de {target.prenom} {target.nom} ont été mises à jour.",
            )
            return redirect(f"{reverse('users:dashboard')}?tab=utilisateur/actifs")
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
        return redirect(f"{reverse('users:dashboard')}?tab=utilisateurs/actifs")

    if target.is_active:
        target.is_active = False
        target.save(update_fields=["is_active"])

    messages.success(request, "Utilisateur désactivé.")
    return redirect(f"{reverse('users:dashboard')}?tab=utilisateur/desactives")


@require_POST
@login_required
@admin_required
def activate_user(request: HttpRequest, user_id: int) -> HttpResponse:
    target = get_object_or_404(CustomUser, pk=user_id)

    if not target.is_active:
        target.is_active = True
        target.save(update_fields=["is_active"])

    messages.success(request, "Utilisateur activé.")
    return redirect(f"{reverse('users:dashboard')}?tab=utilisateur/actifs")


def validate_emprunt(request: HttpRequest, emprunt_id: int) -> HttpResponse:
    emprunt = get_object_or_404(Emprunt, pk=emprunt_id)
    emprunt.statut = Emprunt.Statut.APPROUVE
    emprunt.save(update_fields=["statut"])
    messages.success(request, "Emprunt validé.")
    return redirect(f"{reverse('users:dashboard')}?tab=emprunts")


def refuser_emprunt(request: HttpRequest, emprunt_id: int) -> HttpResponse:
    emprunt = get_object_or_404(Emprunt, pk=emprunt_id)
    emprunt.statut = Emprunt.Statut.REFUSE
    emprunt.save(update_fields=["statut"])
    messages.success(request, "Emprunt refusé.")
    return redirect(f"{reverse('users:dashboard')}?tab=emprunts")


@login_required
@admin_required
def edit_classe(request: HttpRequest, classe_id: int) -> HttpResponse:
    classe = get_object_or_404(Classe, pk=classe_id)

    if request.method == "POST":
        form = ClasseForm(request.POST, instance=classe)
        if form.is_valid():
            form.save()
            messages.success(request, f"Classe « {classe.nom} » mise à jour avec succès.")
            return redirect(f"{reverse('users:dashboard')}?tab=classes/liste")
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ClasseForm(instance=classe)

    return render(request, "users/edit_classe.html", {
        "form": form,
        "classe": classe,
    })


@require_POST
@login_required
@admin_required
def delete_classe(request: HttpRequest, classe_id: int) -> HttpResponse:
    classe = get_object_or_404(Classe, pk=classe_id)

    nb_emprunteurs = classe.tierce_set.count() if hasattr(classe, "tierce_set") else 0
    nb_inventaires = classe.inventaire_set.count() if hasattr(classe, "inventaire_set") else 0

    if nb_emprunteurs > 0:
        messages.error(
            request,
            f"Impossible de supprimer « {classe.nom} » : "
            f"{nb_emprunteurs} emprunteur(s) y sont rattaché(s). "
            "Réaffectez-les d'abord."
        )
        return redirect(f"{reverse('users:dashboard')}?tab=classes/liste")

    if nb_inventaires > 0:
        messages.error(
            request,
            f"Impossible de supprimer « {classe.nom} » : "
            f"{nb_inventaires} inventaire(s) y sont liés."
        )
        return redirect(f"{reverse('users:dashboard')}?tab=classes/liste")

    nom = classe.nom
    classe.delete()
    messages.success(request, f"Classe « {nom} » supprimée avec succès.")
    return redirect(f"{reverse('users:dashboard')}?tab=classes/liste")