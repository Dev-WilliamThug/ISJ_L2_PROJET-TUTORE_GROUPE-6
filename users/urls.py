from django.urls import path

from .views import *


app_name = "users"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("users/<int:user_id>/edit/",       edit_user,       name="edit_user"),
    path("user/<int:user_id>/deactivate/", deactivate_user, name="deactivate_user"),
    path("user/<int:user_id>/activate/", activate_user, name="activate_user"),
    path("createmateriel/",creatematerial)
]

