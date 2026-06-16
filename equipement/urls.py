from django.urls import path
from . import views

app_name = "equipement"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("equipement/dashboard/", views.dashboard, name="dashboard"),
    path("equipement/exporter/", views.exporter_excel, name="exporter_excel"),
    path("equipement/importer/", views.import_materiels, name="import_materiels"),
    path("equipement/rapport/pdf/", views.rapport_pdf, name="rapport_pdf"),
    path("emprunts/importer/", views.import_emprunts, name="import_emprunts"),
    path("equipement/<str:materiel_id>/retirer/", views.retirer_materiel, name="retirer_materiel"),
    path("equipement/<str:materiel_id>/detail/", views.detail_materiel, name="detail_materiel"),
    path("emprunteur/<str:emprunteur_id>/detail/", views.detail_emprunteur, name="detail_emprunteur"),
    path("emprunteur/<str:emprunteur_id>/edit/", views.edit_emprunteur, name="edit_emprunteur"),
    path("equipement/<str:materiel_id>/edit/", views.edit_equipement, name="edit_equipement"),
    path("emprunteur/<str:emprunteur_id>/retirer/", views.retirer_emprunteur, name="retirer_emprunteur"),
    path("emprunt/enregistrer/", views.enregistrer_emprunt_view, name="enregistrer_emprunt"),
    path("emprunts/template/", views.exporter_template_emprunts, name="exporter_template_emprunts"),
    path("emprunts/en-retard/", views.overdue_emprunts, name="overdue_emprunts"),
    path("emprunts/<int:emprunt_id>/rendu/", views.marquer_rendu, name="marquer_rendu"),
    path("rappels/", views.rappels_list, name="rappels_list"),
    path("rappels/envoyer/", views.send_reminders_manual, name="send_reminders_manual"),
    path("notifications/api/", views.notifications_api, name="notifications_api"),
]