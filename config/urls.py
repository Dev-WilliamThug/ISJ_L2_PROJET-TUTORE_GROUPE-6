from django.contrib import admin
from django.urls import include, path
from users import views


urlpatterns = [
    path("",views.module_choice, name="choix du module"),
    path("utilisateurs/", include("users.urls")),
    path("equipements/", include("equipement.urls")),
]
 