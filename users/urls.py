from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("admin/dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("users/<int:user_id>/edit/",       views.edit_user,       name="edit_user"),
    path("user/<int:user_id>/deactivate/", views.deactivate_user, name="deactivate_user"),
    path("user/<int:user_id>/activate/", views.activate_user, name="activate_user"),
    path("inventaire/", views.inventaire_form, name="inventaire_form"),
    path("inventaire/<int:classe_id>/<str:date>/", views.inventaire_detail, name="inventaire_detail"),
    path("inventaire/list/", views.inventaire_list, name="inventaire_list"),
    path("inventaire/<int:inventaire_id>/view/", views.inventaire_detail_view, name="inventaire_view"),
    path("inventaire/<int:inventaire_id>/delete/", views.inventaire_delete, name="inventaire_delete"),

]

