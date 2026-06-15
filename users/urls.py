from django.urls import path
from . import views
from inventaire import views as inventaire_views

app_name = "users"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("admin/dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("users/<int:user_id>/edit/",       views.edit_user,       name="edit_user"),
    path("user/<int:user_id>/deactivate/", views.deactivate_user, name="deactivate_user"),
    path("user/<int:user_id>/activate/", views.activate_user, name="activate_user"),
    path("inventaire/", inventaire_views.create_inventaire, name="create_inventaire"),
    path("inventaire/<int:inventaire_id>/detail/", inventaire_views.inventaire_detail, name="inventaire_detail"),
    path("emprunt/<int:emprunt_id>/valider/", views.validate_emprunt, name="validate_emprunt"),
    path("emprunt/<int:emprunt_id>/refuser/", views.refuser_emprunt, name="refuser_emprunt"),
    path("classes/<int:classe_id>/edit/",   views.edit_classe,   name="edit_classe"),
    path("classes/<int:classe_id>/delete/", views.delete_classe, name="delete_classe"),
]