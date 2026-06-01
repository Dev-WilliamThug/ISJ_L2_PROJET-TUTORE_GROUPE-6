from django import forms

from .models import Materiel, Operation, Tierce


def _next_prefixed_id(last_value: str | None, prefix: str, fallback_count: int) -> str: 

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
        
        
        self.fields['id_materiel'].widget.attrs['readonly'] = True
        self.fields['id_materiel'].widget.attrs['class'] = 'field bg-slate-100'
        self.fields['id_materiel'].help_text = (
            "ID généré automatiquement à partir du nom et du numéro de série."
        )
        self.fields['id_materiel'].required = False
        self.fields['id_materiel'].widget.attrs[
            'placeholder'
        ] = 'Généré à partir du nom + numéro de série'

    def clean(self):
        cleaned = super().clean()
        nom = cleaned.get("nom")
        numero_serie = cleaned.get("numero_serie")

        if nom and numero_serie:
            cleaned["id_materiel"] = Materiel.generate_identifiant(nom, numero_serie)
        else:
            self.add_error(
                "nom",
                "Le nom et le numéro de série sont nécessaires pour générer l'identifiant.",
            )
            self.add_error(
                "numero_serie",
                "Le nom et le numéro de série sont nécessaires pour générer l'identifiant.",
            )

        return cleaned

    class Meta:
        model = Materiel
        fields = ['id_materiel', 'nom', 'couleur','numero_serie','categorie', 'etat', 'marque']


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
        fields = ["id_Tierce", "nom", "prenom", "email", "type_Tierce","classe"]


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
        fields = ["id_Tierce", "nom", "prenom", "email", "type_Tierce","classe"]


class EmpruntForm(forms.Form):
    """Formulaire de création d'un emprunt multi-équipements."""

    emprunteur = forms.ModelChoiceField(
        queryset=Tierce.objects.all(),
        widget=forms.Select(attrs={"class": "field"}),
        label="Emprunteur",
        empty_label="— Choisir un emprunteur —",
    )

    date_operation = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"class": "field", "type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
        label="Date d'emprunt",
    )

    date_retour_prevue = forms.DateField(
        widget=forms.DateInput(attrs={"class": "field", "type": "date"}),
        label="Retour prévu",
        error_messages={"required": "Sélectionnez une date de retour."},
    )

    materiels = forms.ModelMultipleChoiceField(
        queryset=Materiel.objects.filter(etat="DISPONIBLE"),
        widget=forms.CheckboxSelectMultiple,
        label="Équipements",
        error_messages={"required": "Sélectionnez au moins un équipement."},
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "field resize-none", "rows": 3}),
        label="Notes",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        now = timezone.localtime(timezone.now())
        self.fields["date_operation"].initial = now.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned = super().clean()
        date_emprunt = cleaned.get("date_operation")
        date_retour = cleaned.get("date_retour_prevue")
        if date_emprunt and date_retour:
            if date_retour < date_emprunt.date():
                self.add_error(
                    "date_retour_prevue",
                    "La date de retour ne peut pas être antérieure à la date d'emprunt.",
                )
        return cleaned