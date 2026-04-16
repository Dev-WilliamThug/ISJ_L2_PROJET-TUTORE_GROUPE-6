import openpyxl
from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from openpyxl.styles import Font, PatternFill

from users.forms import LoginForm
from users.models import CustomUser
from .form import EditEmprunteurForm, EditMaterielForm, EnregistrerEmprunteurForm, MaterielForm
from .models import Materiel, Tierce


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




def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Déconnexion effectuée.")
    return redirect("users:module_choice")


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



@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tab = request.GET.get("tab", "home")
    form = MaterielForm()
    f = EnregistrerEmprunteurForm()
    editMaterielForm = None
    editEmprunteurForm = None
    target = None
    materiel_detail = None
    emprunteur_detail = None
    emprunteurs = Tierce.objects.all()

    materiels = Materiel.objects.all()
    materiels_recents = materiels.order_by("-id_materiel")[:5]
    materiels_disponibles = materiels.filter(etat="DISPONIBLE")

   
    if tab == "detail" and request.GET.get("materiel_id"):
        materiel_detail = get_object_or_404(Materiel, pk=request.GET.get("materiel_id"))
    if tab == "detail_emprunteur" and request.GET.get("emprunteur_id"):
        emprunteur_detail = get_object_or_404(Tierce, pk=request.GET.get("emprunteur_id"))

    if tab == "editMateriel" and request.GET.get("materiel_id"):
        target = get_object_or_404(Materiel, id_materiel=request.GET.get("materiel_id"))

        if request.method == "POST":
            action = request.POST.get("action")

            if action == "edit_materiel":
                editMaterielForm = EditMaterielForm(request.POST, instance=target)

                if editMaterielForm.is_valid():
                    editMaterielForm.save()
                    messages.success(request, "Modification effectuée avec succès.")
                    return redirect(f"{reverse('equipement:dashboard')}?tab=list")

                messages.error(request, "Veuillez corriger les erreurs.")
        
        else:
            editMaterielForm = EditMaterielForm(instance=target)

    if tab == "editEmprunteur" and request.GET.get("emprunteur_id"):
        target = get_object_or_404(Tierce, id_Tierce=request.GET.get("emprunteur_id"))

        if request.method == "POST":
            action = request.POST.get("action")

            if action == "edit_emprunteur":
                editEmprunteurForm = EditEmprunteurForm(request.POST, instance=target)

                if editEmprunteurForm.is_valid():
                    editEmprunteurForm.save()
                    messages.success(request, "Modification effectuée avec succès.")
                    return redirect(f"{reverse('equipement:dashboard')}?tab=list")

                messages.error(request, "Veuillez corriger les erreurs.")
        
        else:
            editEmprunteurForm = EditEmprunteurForm(instance=target)      


    if request.method == "POST":
        action = request.POST.get("action")
        if action == "register_materiel":
            form = MaterielForm(request.POST or None)
            if form.is_valid():
                form.save()
                messages.success(request, "Equipement enregistre avec succes.")
                return redirect(f"{reverse('equipement:dashboard')}?tab=list")
            messages.error(request, "Veuillez corriger les erreurs du formulaire equipement.")
            tab = "add"

        if action == "register_emprunteur":
            f = EnregistrerEmprunteurForm(request.POST)
            if f.is_valid():
                f.save()
                messages.success(request, "Emprunteur enregistre avec succes.")
                return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")
            messages.error(request, "Veuillez corriger les erreurs du formulaire emprunteur.")
            tab = "register"

    context = {
        "tab": tab,
        "target": target,
        "form": form,
        "materiels": materiels,
        "materiels_recents": materiels_recents,
        "materiels_disponibles": materiels_disponibles,
        "materiel_detail": materiel_detail,
        "editMaterielForm": editMaterielForm,
        "editEmprunteurForm": editEmprunteurForm,
        "emprunteur_detail": emprunteur_detail,
        "f": f,
        "emprunteurs": emprunteurs,
    }
    return render(request, "equipement/dashboard.html", context)





def exporter_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Materiel"

  
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")


    ws.append([])
    ws.append(["Exporté le :", datetime.now().strftime("%d/%m/%Y %H:%M")])

  
    headers = ['nom', 'id_materiel', 'etat', 'couleur', 'marque']
    ws.append(headers)

    for cell in ws[3]:
        cell.font = header_font
        cell.fill = header_fill

    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 20

    for materiel in Materiel.objects.all():
        ws.append([
            materiel.nom,
            materiel.id_materiel,
            materiel.get_etat_display(),
            materiel.couleur,
            materiel.marque
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=logiciel.xlsx'

    wb.save(response)

    return response


def retirer_materiel(request, materiel_id):
    if request.method != "POST":
        messages.error(request, "Action non autorisee.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=list")
    materiel = get_object_or_404(Materiel, id_materiel=materiel_id)
    nom = materiel.nom
    materiel.delete()
    messages.success(request, f"Equipement {nom} retire avec succes.")
    return redirect(f"{reverse('equipement:dashboard')}?tab=list")


def import_materiels(request):
    if request.method != "POST":
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    fichier = request.FILES.get("file")
    if not fichier:
        messages.error(request, "Veuillez selectionner un fichier.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")
    if not fichier.name.endswith(".xlsx"):
        messages.error(request, "Le fichier doit etre au format .xlsx.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    try:
        wb = openpyxl.load_workbook(fichier)
        ws = wb.active
    except Exception:
        messages.error(request, "Impossible de lire le fichier Excel.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=import")

    importes = 0
    ignores = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 6:
            ignores += 1
            continue

        id_materiel, nom, couleur, categorie, etat, marque = row[:6]
        if not id_materiel or not nom:
            ignores += 1
            continue

        valeurs_valides = [choix[0] for choix in Materiel.ETAT_CHOICES]
        etat_valeur = etat if etat in valeurs_valides else "DISPONIBLE"

        obj, created = Materiel.objects.update_or_create(
            id_materiel=id_materiel,
            defaults={
                "nom": nom,
                "couleur": couleur or "",
                "categorie": categorie or "",
                "etat": etat_valeur,
                "marque": marque or "",
            },
        )
        if obj:
            importes += 1
        else:
            ignores += 1

    messages.success(request, f"Import termine : {importes} ligne(s) traitee(s), {ignores} ignoree(s).")
    return redirect(f"{reverse('equipement:dashboard')}?tab=list")


def detail_materiel(request, materiel_id):
    get_object_or_404(Materiel, id_materiel=materiel_id)
    return redirect(f"{reverse('equipement:dashboard')}?tab=detail&materiel_id={materiel_id}")


def detail_emprunteur(request, emprunteur_id):
    get_object_or_404(Tierce, id_Tierce=emprunteur_id)
    return redirect(f"{reverse('equipement:dashboard')}?tab=detail_emprunteur&emprunteur_id={emprunteur_id}")


def edit_emprunteur(request: HttpRequest, emprunteur_id: str) -> HttpResponse:
    target = get_object_or_404(Tierce, id_Tierce=emprunteur_id)

    if request.method == "POST":
        form = EditEmprunteurForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, "Emprunteur modifie avec succes.")
            return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")
        messages.error(request, "Veuillez corriger les erreurs du formulaire emprunteur.")
    else:
        form = EditEmprunteurForm(instance=target)

    return render(request, "equipement/edit_emprunteur.html", {"form": form, "target": target})


def retirer_emprunteur(request: HttpRequest, emprunteur_id: str) -> HttpResponse:
    if request.method != "POST":
        messages.error(request, "Action non autorisee.")
        return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")

    emprunteur = get_object_or_404(Tierce, id_Tierce=emprunteur_id)
    nom_complet = f"{emprunteur.prenom} {emprunteur.nom}".strip()
    emprunteur.delete()
    messages.success(request, f"Emprunteur {nom_complet} supprime avec succes.")
    return redirect(f"{reverse('equipement:dashboard')}?tab=lister_emprunteurs")
