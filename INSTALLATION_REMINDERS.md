# Installation du Système de Rappels

## ✅ Étapes d'Installation

### 1. Fichiers Déjà Créés
Les fichiers suivants ont été créés/modifiés pour vous:
- ✓ `equipement/models.py` - Modèle Rappel ajouté
- ✓ `equipement/reminder_service.py` - Service de rappels
- ✓ `equipement/admin.py` - Interface administration enrichie
- ✓ `equipement/views.py` - Vues pour les rappels et emprunts en retard
- ✓ `equipement/urls.py` - Routes pour accéder aux rappels
- ✓ `equipement/management/commands/send_reminders.py` - Commande Django
- ✓ `equipement/templates/equipement/overdue_emprunts.html` - Template emprunts en retard
- ✓ `equipement/templates/equipement/rappels_list.html` - Template historique rappels
- ✓ `equipement/migrations/0002_rappel.py` - Migration pour le modèle Rappel
- ✓ `equipement/tests_reminders.py` - Tests unitaires
- ✓ `REMINDER_SYSTEM_README.md` - Documentation complète

### 2. Appliquer les Migrations

```bash
# Naviguer vers le dossier du projet
cd e:\FinTuto\ISJ_L2_PROJET-TUTORE_GROUPE-6

# Créer les tables en base de données
python manage.py migrate equipement 0002_rappel
```

### 3. Tester le Système

```bash
# Lancer les tests
python manage.py test equipement.tests_reminders

# Envoyer les rappels (commande test)
python manage.py send_reminders --verbose
```

### 4. Accéder aux Interfaces Web

Après avoir démarré le serveur Django:
```bash
python manage.py runserver
```

Naviguez vers:
- **Emprunts en retard**: http://localhost:8000/equipement/emprunts/en-retard/
- **Historique des rappels**: http://localhost:8000/equipement/rappels/

### 5. Administration Django

Allez à: http://localhost:8000/admin/

Et consulter:
- Modèle "Rappels" pour voir l'historique complet
- Modèle "Emprunts" pour voir les détails

## 🔍 Configuration Vérifiée

✅ Configuration email dans `config/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jeanemmanuelmahop@gmail.com'
EMAIL_HOST_PASSWORD = 'flnabgmkmtcvrrbr'
DEFAULT_FROM_EMAIL = 'jeanemmanuelmahop@gmail.com'
```

## 🎯 Cas de Test Rapide

1. **Créer un emprunt en retard**:
   - Allez dans le dashboard
   - Créez un emprunt avec une date de retour passée

2. **Voir l'emprunt en retard**:
   - Allez à `/equipement/emprunts/en-retard/`
   - L'emprunt devrait apparaître

3. **Envoyer les rappels manuellement**:
   - Cliquez sur "📧 Envoyer les Rappels"
   - Ou exécutez: `python manage.py send_reminders --verbose`

4. **Consulter l'historique**:
   - Allez à `/equipement/rappels/`
   - Vous devriez voir le rappel envoyé

## 🚨 Dépannage

### Erreur: "No module named 'equipement.reminder_service'"
→ Assurez-vous que `reminder_service.py` est dans `equipement/`

### Erreur lors de la migration
```bash
# Réinitialiser les migrations si nécessaire
python manage.py migrate equipement 0001_initial
python manage.py makemigrations equipement
python manage.py migrate equipement
```

### Les emails ne s'envoient pas
- Vérifier la configuration Gmail
- Tester avec: `python manage.py shell`
  ```python
  from django.core.mail import send_mail
  send_mail('Test', 'Message', 'from@gmail.com', ['to@test.com'])
  ```

## 📅 Automatisation (Optionnel)

### Cron Job (Linux/Mac)
```bash
# Éditer crontab
crontab -e

# Ajouter pour 8h du matin tous les jours
0 8 * * * cd /chemin/du/projet && python manage.py send_reminders
```

### Task Scheduler (Windows)
1. Créer un fichier `send_reminders.bat`:
```batch
@echo off
cd e:\FinTuto\ISJ_L2_PROJET-TUTORE_GROUPE-6
python manage.py send_reminders
```

2. Créer une tâche planifiée qui exécute ce fichier chaque jour

## 📊 Vérification du Système

```bash
# Vérifier les emprunts en retard
python manage.py shell

>>> from equipement.models import Emprunt
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> 
>>> # Voir les emprunts en retard
>>> today = timezone.now().date()
>>> emprunts = Emprunt.objects.filter(date_retour_prevue__lt=today, date_retour_reelle__isnull=True)
>>> for e in emprunts:
...     print(f"{e.emprunteur} - Retard: {(today - e.date_retour_prevue).days} jours")
```

## 🎓 Documentation

Pour plus d'informations, consultez:
- `REMINDER_SYSTEM_README.md` - Documentation complète du système
- Code source commenté dans `equipement/reminder_service.py`
- Tests dans `equipement/tests_reminders.py`

## ✨ Prochaines Étapes

1. Tester l'envoi des rappels
2. Configurer l'automatisation (cron ou task scheduler)
3. Personnaliser les templates d'email si nécessaire
4. Intégrer avec d'autres systèmes (SMS, notifications)

Bonne utilisation! 🚀
