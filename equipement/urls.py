from django.urls import path

from . import views

app_name = "equipement"

urlpatterns = [
    path("", views.module_choice, name="module_choice"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("equipement/dashboard", views.dashboard, name="dashboard"),
    path("equipement/exporter", views.exporter_excel, name="exporter_excel"),  
    path("equipement/importer", views.import_materiels, name="import_materiels"),  
    path("equipement/<str:materiel_id>/retirer/", views.retirer_materiel, name="retirer_materiel"),
    path("equipement/<str:materiel_id>/detail/", views.detail_materiel, name="detail_materiel"),
    path("emprunteur/<str:emprunteur_id>/detail/", views.detail_emprunteur, name="detail_emprunteur"),
    path("emprunteur/<str:emprunteur_id>/edit/", views.edit_emprunteur, name="edit_emprunteur"),
    path("equipement/<str:materiel_id>/edit/", views.edit_equipement, name="edit_equipement"),
    path("emprunteur/<str:emprunteur_id>/retirer/", views.retirer_emprunteur, name="retirer_emprunteur"),
    path("emprunt/enregistrer/", views.enregistrer_emprunt_view, name="enregistrer_emprunt"),
]
