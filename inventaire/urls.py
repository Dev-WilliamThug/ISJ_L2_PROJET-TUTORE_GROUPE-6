from django.urls import path,include

from . import views

app_name='inventaire'


urlpatterns=[
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create_inventaire/", views.create_inventaire, name="create_inventaire"),
    path("inventaire_detail/<int:inventaire_id>/", views.inventaire_detail, name="inventaire_detail"),
]

