from django.contrib import admin
from django.urls import path, include
from users import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("utilisateurs/", include("users.urls")),
    path("equipements/", include("equipement.urls")),
    path("inventaire/", include("inventaire.urls")),
]