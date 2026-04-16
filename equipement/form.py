from django import forms

from .models import Materiel, Tierce


def _next_prefixed_id(last_value: str | None, prefix: str, fallback_count: int) -> str:
    """
    Construit un ID du type PREFIX-001 en évitant les erreurs
    si l'ancien format ne contient pas de '-'.
    """
    if not last_value:
        return f"{prefix}-001"

    try:
        parts = str(last_value).split("-")
        number = int(parts[-1]) + 1
    except (ValueError, TypeError):
        number = fallback_count + 1
    return f"{prefix}-{number:03d}"

class MaterielForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "field"
            field.widget.attrs["placeholder"] = f"Saisir {field.label.lower()}"
        
        # Calcul du prochain ID (EQ-00X), robuste meme si ancien format invalide.
        dernier_materiel = Materiel.objects.order_by('id_materiel').last()
        nouvel_id = _next_prefixed_id(
            dernier_materiel.id_materiel if dernier_materiel else None,
            "EQ",
            Materiel.objects.count(),
        )

        # Pre-remplissage et lecture seule de l'ID.
        self.fields['id_materiel'].initial = nouvel_id
        self.fields['id_materiel'].widget.attrs['readonly'] = True
        self.fields["id_materiel"].help_text = "ID genere automatiquement."
        self.fields['id_materiel'].widget.attrs['class'] = 'field bg-slate-100'
        self.fields["id_materiel"].widget.attrs["placeholder"] = nouvel_id

    class Meta:
        model = Materiel
        fields = ['id_materiel', 'nom', 'couleur', 'categorie', 'etat', 'marque']


class EditMaterielForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"
        self.fields["id_materiel"].widget.attrs["readonly"] = True
        self.fields["id_materiel"].widget.attrs["class"] = "field bg-slate-100"
        self.fields["id_materiel"].help_text = "ID non modifiable."

    class Meta:
        model = Materiel
        fields = ['id_materiel', 'nom', 'couleur', 'categorie', 'etat', 'marque']
class EnregistrerEmprunteurForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"
            field.widget.attrs["placeholder"] = f"Saisir {field.label.lower()}"
        dernier = Tierce.objects.order_by("id_Tierce").last()
        nouvel_id = _next_prefixed_id(
            dernier.id_Tierce if dernier else None,
            "EM",
            Tierce.objects.count(),
        )

        self.fields["id_Tierce"].initial = nouvel_id
        self.fields["id_Tierce"].widget.attrs["readonly"] = True
        self.fields["id_Tierce"].widget.attrs["class"] = "field bg-slate-100"
        self.fields["id_Tierce"].help_text = "ID genere automatiquement."
        self.fields["id_Tierce"].widget.attrs["placeholder"] = nouvel_id

    class Meta:
        model = Tierce
        fields = ["id_Tierce", "nom", "prenom", "email", "type_Tierce"]


class EditEmprunteurForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field"
            field.widget.attrs["placeholder"] = f"Saisir {field.label.lower()}"
        self.fields["id_Tierce"].widget.attrs["readonly"] = True
        self.fields["id_Tierce"].widget.attrs["class"] = "field bg-slate-100"
        self.fields["id_Tierce"].help_text = "ID non modifiable."

    class Meta:
        model = Tierce
        fields = ["id_Tierce", "nom", "prenom", "email", "type_Tierce"]