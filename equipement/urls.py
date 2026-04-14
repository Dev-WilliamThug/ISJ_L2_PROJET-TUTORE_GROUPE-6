from django.urls import path

from . import views

app_name = "equipement"

urlpatterns = [
    path("", views.module_choice, name="module_choice"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("equipement/dashboard", views.dashboard, name="dashboard"),
]
