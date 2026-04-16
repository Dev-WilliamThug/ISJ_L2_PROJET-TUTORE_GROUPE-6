from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("equipement", "0002_categorie"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tierce",
            fields=[
                (
                    "id_tierce",
                    models.CharField(
                        max_length=50,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Identifiant",
                    ),
                ),
                ("nom", models.CharField(max_length=200)),
                ("prenom", models.CharField(max_length=200)),
                (
                    "email",
                    models.EmailField(max_length=254, unique=True, verbose_name="email address"),
                ),
                (
                    "type_Tierce",
                    models.CharField(
                        choices=[("etudiant", "etudiant"), ("professeur", "professeur")],
                        default="etudiant",
                        max_length=30,
                        verbose_name="Type",
                    ),
                ),
            ],
        ),
    ]
