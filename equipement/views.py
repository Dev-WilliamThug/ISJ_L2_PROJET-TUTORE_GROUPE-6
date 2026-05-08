import openpyxl
from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from openpyxl.styles import Font, PatternFill

from users.forms import LoginForm
from users.models import CustomUser
from .form import EditEmprunteurForm, EditMaterielForm, EnregistrerEmprunteurForm, MaterielForm, EmpruntForm
from .models import Materiel, Tierce, Emprunt, LigneEmprunt


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
        if request.user.type_user == CustomUser.TypeUser.MANAGER:
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


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Déconnexion effectuée.")
    return redirect("users:module_choice")


def register_materiel(request: HttpRequest, form: MaterielForm) -> HttpResponse:
    if request.method != "POST":
        messages.error(request, "Action non autorisee.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=add")
    if form.is_valid():
        form.save()
        messages.success(request, "Equipement enregistre avec succes.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=list")
    messages.error(request, "Veuillez corriger les erreurs du formulaire equipement.")
    return redirect(f"{reverse('equipement:dashboard')}?tab=add")


@login_required
def edit_equipement(request: HttpRequest, materiel_id: str) -> HttpResponse:
    materiel = get_object_or_404(Materiel, pk=materiel_id)

    if request.method == "POST":
        form = EditMaterielForm(request.POST, instance=materiel)
        if form.is_valid():
            form.save()
            messages.success(request, f"Equipement {materiel.nom} modifié avec succès.")
            return redirect(
                f"{reverse('equipement:dashboard')}?tab=detail&materiel_id={materiel_id}"
            )
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = EditMaterielForm(instance=materiel)

    return render(request, "equipement/edit_equipement.html", {
        "form": form,
        "materiel": materiel,
    })


def register_emprunteur(request: HttpRequest, form: EnregistrerEmprunteurForm) -> HttpResponse:
    if request.method != "POST":
        messages.error(request, "Action non autorisee.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=register")
    if form.is_valid():
        form.save()
        messages.success(request, "Emprunteur enregistre avec succes.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")
    messages.error(request, "Veuillez corriger les erreurs du formulaire emprunteur.")
    return redirect(f"{reverse('equipement:dashboard')}?tab=register")


@login_required
def edit_emprunteur(request: HttpRequest, emprunteur_id: str) -> HttpResponse:
    emprunteur = get_object_or_404(Tierce, pk=emprunteur_id)

    if request.method == "POST":
        form = EditEmprunteurForm(request.POST, instance=emprunteur)
        if form.is_valid():
            form.save()
            messages.success(request, f"Emprunteur {emprunteur.prenom} {emprunteur.nom} modifié avec succès.")
            return redirect(
                f"{reverse('equipement:dashboard')}?tab=detail_emprunteur&emprunteur_id={emprunteur_id}"
            )
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = EditEmprunteurForm(instance=emprunteur)

    return render(request, "equipement/edit_emprunteur.html", {
        "form": form,
        "emprunteur": emprunteur,
    })


def dashboard(request: HttpRequest) -> HttpResponse:
    tab = request.GET.get("tab", "home")

    editFormMateriel = EditMaterielForm()
    editFormEmprunteur = EditEmprunteurForm()
    formMateriel = MaterielForm()
    formEmprunteur = EnregistrerEmprunteurForm()
    formEmprunt = EmpruntForm()

    action = request.POST.get("action")
    target = None

    materiel_detail = None
    emprunteur_detail = None

    emprunteurs = Tierce.objects.all()
    materiels = Materiel.objects.all()
    emprunts = Emprunt.objects.select_related(
        "materiel",
        "emprunteur",
    ).prefetch_related("lignes__materiel").order_by("-date_emprunt")

    # ✅ AJOUT : filtrage par catégorie
    categorie_filtre = request.GET.get("categorie", "")
    if categorie_filtre:
        materiels = materiels.filter(categorie=categorie_filtre)

    # ✅ AJOUT : liste des catégories pour le template
    categories = Materiel.Categorie.choices

    materiels_recents = Materiel.objects.order_by("-id_materiel")[:5]
    materiels_disponibles = Materiel.objects.filter(etat="DISPONIBLE")

    if request.method == "POST":

        if action == "register_materiel":
            formMateriel = MaterielForm(request.POST)
            return register_materiel(request, formMateriel)

        if action == "register_emprunteur":
            formEmprunteur = EnregistrerEmprunteurForm(request.POST)
            return register_emprunteur(request, formEmprunteur)

    if tab == "detail" and request.GET.get("materiel_id"):
        materiel_detail = get_object_or_404(Materiel, pk=request.GET.get("materiel_id"))
    if tab == "detail_emprunteur" and request.GET.get("emprunteur_id"):
        emprunteur_detail = get_object_or_404(Tierce, pk=request.GET.get("emprunteur_id"))

    context = {
        "tab": tab,
        "target": target,
        "formMateriel": formMateriel,
        "formEmprunteur": formEmprunteur,
        "formEmprunt": formEmprunt,
        "materiels": materiels,
        "materiels_recents": materiels_recents,
        "materiels_disponibles": materiels_disponibles,
        "materiel_detail": materiel_detail,
        "editMaterielForm": editFormMateriel,
        "editEmprunteurForm": editFormEmprunteur,
        "emprunteur_detail": emprunteur_detail,
        "emprunteurs": emprunteurs,
        "emprunts": emprunts,
        "statuts_emprunt": Emprunt.Statut.choices,
        # ✅ AJOUT
        "categories": categories,
        "categorie_filtre": categorie_filtre,
    }
    return render(request, "equipement/dashboard.html", context)


def detail_materiel(request, materiel_id):
    get_object_or_404(Materiel, id_materiel=materiel_id)
    return redirect(f"{reverse('equipement:dashboard')}?tab=detail&materiel_id={materiel_id}")


def retirer_materiel(request, materiel_id):
    if request.method != "POST":
        messages.error(request, "Action non autorisee.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=list")
    materiel = get_object_or_404(Materiel, id_materiel=materiel_id)
    nom = materiel.nom
    materiel.delete()
    messages.success(request, f"Equipement {nom} retire avec succes.")
    return redirect(f"{reverse('equipement:dashboard')}?tab=list")


@require_POST
def modifier_statut_emprunt(request: HttpRequest, emprunt_id: int) -> HttpResponse:
    emprunt = get_object_or_404(Emprunt, pk=emprunt_id)
    nouveau_statut = request.POST.get("statut")
    source = request.POST.get("source", "equipement")
    statuts_valides = [statut for statut, _ in Emprunt.Statut.choices]

    if nouveau_statut not in statuts_valides:
        messages.error(request, "Statut invalide.")
    else:
        emprunt.statut = nouveau_statut
        if nouveau_statut == Emprunt.Statut.RETOURNE:
            emprunt.date_retour_effective = timezone.localdate()
        elif nouveau_statut == Emprunt.Statut.EN_COURS:
            emprunt.date_retour_effective = None
        emprunt.save(update_fields=["statut", "date_retour_effective"])

        materiels = [ligne.materiel for ligne in emprunt.lignes.all()]
        if not materiels and emprunt.materiel_id:
            materiels = [emprunt.materiel]

        if nouveau_statut == Emprunt.Statut.RETOURNE:
            for materiel in materiels:
                materiel.retourner()
        elif nouveau_statut == Emprunt.Statut.EN_COURS:
            for materiel in materiels:
                materiel.etat = "EN PRET"
                materiel.save(update_fields=["etat"])

        messages.success(request, "Statut de l'emprunt modifie avec succes.")

    if source == "admin":
        return redirect(f"{reverse('users:dashboard')}?tab=listeemprunts")
    return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunts")


@login_required
def enregistrer_emprunt_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EmpruntForm(request.POST)
        if form.is_valid():
            materiels_choisis = form.cleaned_data["materiels"]
            date_emprunt = form.cleaned_data["date_emprunt"]
            now = timezone.now()

            if timezone.is_naive(date_emprunt):
                date_emprunt = timezone.make_aware(date_emprunt)

            statut = Emprunt.Statut.EN_COURS if date_emprunt <= now else Emprunt.Statut.EN_ATTENTE

            if statut == Emprunt.Statut.EN_COURS:
                indisponibles = [m for m in materiels_choisis if not m.est_disponible()]
                if indisponibles:
                    noms = ", ".join(m.nom for m in indisponibles)
                    messages.error(request, f"Matériel(s) non disponible(s) : {noms}")
                    return redirect(f"{reverse('equipement:dashboard')}?tab=creer_emprunt")

            emprunt = Emprunt.objects.create(
                materiel=materiels_choisis[0],
                emprunteur=form.cleaned_data["emprunteur"],
                date_emprunt=date_emprunt,
                date_retour_prevue=form.cleaned_data["date_retour_prevue"],
                statut=statut,
                notes=form.cleaned_data["notes"],
            )

            for materiel in materiels_choisis:
                LigneEmprunt.objects.create(emprunt=emprunt, materiel=materiel)
                if statut == Emprunt.Statut.EN_COURS:
                    materiel.mettre_en_pret()

            messages.success(
                request,
                f"Emprunt enregistré avec succès ({len(materiels_choisis)} équipement(s), statut : {emprunt.get_statut_display()})."
            )
            return redirect(f"{reverse('equipement:dashboard')}?tab=home")

        messages.error(request, "Erreur dans le formulaire.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=creer_emprunt")
    return redirect(f"{reverse('equipement:dashboard')}?tab=creer_emprunt")


def exporter_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Materiels"

    headers = ['id_materiel', 'nom', 'couleur', 'categorie', 'etat', 'marque']
    ws.append(headers)

    for m in Materiel.objects.all():
        ws.append([
            str(m.id_materiel),
            m.nom or "",
            m.couleur or "",
            m.categorie or "",
            m.etat or "",
            m.marque or "",
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=materiels.xlsx'
    wb.save(response)
    return response


def import_materiels(request):
    if request.method != "POST":
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    fichier = request.FILES.get("file")

    if not fichier:
        messages.error(request, "Veuillez sélectionner un fichier.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    if not fichier.name.endswith(".xlsx"):
        messages.error(request, "Fichier invalide (.xlsx requis).")
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    try:
        wb = openpyxl.load_workbook(fichier)
        ws = wb.active
    except Exception as e:
        messages.error(request, f"Erreur lecture fichier : {e}")
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    importes = 0
    ignores = 0

    valeurs_valides = [c[0] for c in Materiel.ETAT_CHOICES]

    for row in ws.iter_rows(min_row=2, values_only=True):

        if not row:
            ignores += 1
            continue

        row = [str(cell).strip() if cell else "" for cell in row]

        if len(row) < 6:
            ignores += 1
            continue

        id_materiel, nom, couleur, categorie, etat, marque = row[:6]

        if not id_materiel or not nom:
            ignores += 1
            continue

        etat = etat.upper()
        if etat not in valeurs_valides:
            etat = "DISPONIBLE"

        Materiel.objects.update_or_create(
            id_materiel=id_materiel,
            defaults={
                "nom": nom,
                "couleur": couleur,
                "categorie": categorie,
                "etat": etat,
                "marque": marque,
            }
        )
        importes += 1

    messages.success(
        request,
        f"Import terminé : {importes} lignes traitées, {ignores} ignorées."
    )
    return redirect(f"{reverse('equipement:dashboard')}?tab=list")


def detail_materiel(request, materiel_id):
    get_object_or_404(Materiel, id_materiel=materiel_id)
    return redirect(f"{reverse('equipement:dashboard')}?tab=detail&materiel_id={materiel_id}")


def detail_emprunteur(request, emprunteur_id):
    get_object_or_404(Tierce, id_Tierce=emprunteur_id)
    return redirect(f"{reverse('equipement:dashboard')}?tab=detail_emprunteur&emprunteur_id={emprunteur_id}")


def retirer_emprunteur(request: HttpRequest, emprunteur_id: str) -> HttpResponse:
    if request.method != "POST":
        messages.error(request, "Action non autorisee.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")

    emprunteur = get_object_or_404(Tierce, id_Tierce=emprunteur_id)
    nom_complet = f"{emprunteur.prenom} {emprunteur.nom}".strip()
    emprunteur.delete()
    messages.success(request, f"Emprunteur {nom_complet} supprime avec succes.")
    return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")
