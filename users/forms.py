from django import forms

from .models import CustomUser
from equipement.models import Classe


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class RegisterUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["nom", "prenom", "email", "type_user"]
        widgets = {
            "type_user": forms.Select(choices=CustomUser.TypeUser.choices),
        }


class EditUserForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = ["nom", "prenom", "email", "type_user"]
        widgets = {
            "type_user": forms.Select(choices=CustomUser.TypeUser.choices),
        }


class ClasseForm(forms.ModelForm):
    """Formulaire de création / modification d'une salle de classe."""

    class Meta:
        model = Classe
        fields = ["nom", "description", "nombre_places"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nom"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "ex : Salle A101",
        })
        self.fields["description"].widget = forms.Textarea(attrs={
            "class": "form-input resize-none",
            "rows": 3,
            "placeholder": "Description optionnelle...",
        })
        self.fields["description"].required = False
        self.fields["nombre_places"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "ex : 30",
            "min": "1",
        })
        self.fields["nombre_places"].required = False

    def clean_nom(self):
        nom = self.cleaned_data.get("nom", "").strip()
        if len(nom) < 2:
            raise forms.ValidationError("Le nom doit contenir au moins 2 caractères.")
        # Vérifier unicité en excluant l'instance courante (utile à l'édition)
        qs = Classe.objects.filter(nom__iexact=nom)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"Une classe nommée « {nom} » existe déjà.")
        return nom

    def clean_nombre_places(self):
        places = self.cleaned_data.get("nombre_places")
        if places is not None and places < 1:
            raise forms.ValidationError("Le nombre de places doit être supérieur à 0.")
        return places