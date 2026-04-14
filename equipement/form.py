from django import forms
from .models import Materiel

class MaterielForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Calcul du prochain ID (EQ-00X)
        dernier_materiel = Materiel.objects.order_by('id_materiel').last()
        if not dernier_materiel:
            nouvel_id = "EQ-001"
        else:
            # On extrait le chiffre, on l'incrémente et on reformate
            numero = int(dernier_materiel.id_materiel.split('-')[1]) + 1
            nouvel_id = f"EQ-{numero:03d}" # :03d ajoute les zéros (002, 010...)
            
        # 2. On pré-remplit le champ et on le met en lecture seule
        self.fields['id_materiel'].initial = nouvel_id
        self.fields['id_materiel'].widget.attrs['readonly'] = True
        # Optionnel : ajouter une classe CSS pour montrer que c'est bloqué
        self.fields['id_materiel'].widget.attrs['class'] = 'form-control bg-light'

    class Meta:
        model = Materiel
        fields = ['id_materiel', 'nom', 'couleur', 'categorie', 'etat', 'marque']
