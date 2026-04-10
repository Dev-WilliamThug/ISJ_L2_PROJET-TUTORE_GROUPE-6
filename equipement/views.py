from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from users.forms import LoginForm
from users.models import CustomUser


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("equipement:login")
        if request.user.type_user != "gestionnaire":
            return redirect("users:dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped



def module_choice(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.type_user == CustomUser.TypeUser.ADMIN:
            return redirect("users:dashboard")
        return redirect("equipement:dashboard")
    return render(request, "equipement/module_choice.html")



def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.type_user == CustomUser.TypeUser:
            return redirect("equipement:dashboard")
        return redirect("users:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
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
            return redirect("equipement:dashboard")

    return render(request, "equipement/login.html", {"form": form})



@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tab = request.GET.get("tab", "home")
    context = {
        "tab": tab,
        "stats": {
            "equipements_total": 128,
            "equipements_disponibles": 97,
            "emprunts_en_cours": 31,
            "retours_prevus": 12,
        },
        "recent_equipements": [
            {"code": "EQ-001", "nom": "Ordinateur Dell Latitude 7440", "etat": "Disponible"},
            {"code": "EQ-002", "nom": "Projecteur Epson EB-X49", "etat": "Emprunte"},
            {"code": "EQ-003", "nom": "Tablette Samsung Tab S9", "etat": "Maintenance"},
            {"code": "EQ-004", "nom": "Camera Sony ZV-E10", "etat": "Disponible"},
        ],
    }
    return render(request, "equipement/dashboard.html", context)
