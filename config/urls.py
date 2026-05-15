from django.contrib import admin
from django.urls import include, path
from users import views


urlpatterns = [
    path("",views.login_view, name="login"),
    path("utilisateurs/", include("users.urls")),
    path("equipements/", include("equipement.urls")),
]
 