from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("users/<int:user_id>/edit/",       views.edit_user,       name="edit_user"),
    path("user/<int:user_id>/deactivate/", views.deactivate_user, name="deactivate_user"),
    path("user/<int:user_id>/activate/", views.activate_user, name="activate_user"),
]

