from django import forms

from .models import CustomUser, Materiel


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
class formmateriel(forms.ModelForm):
    class Meta:
        model = Materiel
        fields = ["couleur", "Marque"]