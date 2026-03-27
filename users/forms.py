from django import forms

from .models import CustomUser


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