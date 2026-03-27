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
from .forms import LoginForm, RegisterUserForm, EditUserForm
from .models import CustomUser


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

        if getattr(request.user, "type_user", None) != CustomUser.TypeUser.ADMIN:
            messages.error(request, "Accès refusé : uniquement les administrateurs.")
            logout(request)
            return redirect("users:login")

        return view_func(request, *args, **kwargs)

    return _wrapped


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("users:dashboard")

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
            elif user.type_user != CustomUser.TypeUser.ADMIN:
                messages.error(request, "Seuls les administrateurs peuvent se connecter.")
            else:
                login(request, user)
                return redirect("users:dashboard")

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