from django.urls import path

from . import views

app_name='inventaire'


urlpatterns=[
    path("", views.login_view, name="login"),
    path("inventaire/", views.inventaire_form, name="inventaire_form"),
    path("inventaire/<int:classe_id>/<str:date>/", views.inventaire_detail, name="inventaire_detail"),
    path("inventaire/list/", views.inventaire_list, name="inventaire_list"),
    path("inventaire/<int:inventaire_id>/view/", views.inventaire_detail_view, name="inventaire_view"),
    path("inventaire/<int:inventaire_id>/delete/", views.inventaire_delete, name="inventaire_delete"),
]

