from django import forms
from django.utils import timezone
from .models import Classe
from django.core.exceptions import ValidationError

class InventaireForm(forms.Form):

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(), 
        empty_label="Choisir une classe",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    date_inventaire = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean_date_inventaire(self):
        date_selectionnee = self.cleaned_data.get('date_inventaire')
        if date_selectionnee > timezone.now().date():
            raise ValidationError("Impossible de faire un inventaire à une date future !")
        return date_selectionnee
