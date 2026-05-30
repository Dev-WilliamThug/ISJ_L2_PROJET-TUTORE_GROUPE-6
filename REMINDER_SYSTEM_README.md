# Système de Rappels pour Emprunts en Retard

## 📋 Description

Ce système automatise l'envoi de rappels par email aux emprunteurs dont la date de retour du matériel emprunté est dépassée. Le système envoie plusieurs rappels échelonnés à 1, 3 et 7 jours de retard.

## 🚀 Fonctionnalités

- **Détection automatique** des emprunts en retard
- **Rappels échelonnés** à 1, 3, et 7 jours de retard
- **Suivi des rappels** envoyés avec historique
- **Gestion des erreurs** avec enregistrement des messages d'erreur
- **Interface d'administration** pour gérer les rappels
- **Envoi manuel** des rappels depuis le tableau de bord
- **Filtrage** et recherche dans l'historique des rappels

## 📁 Fichiers Créés/Modifiés

### Modèles (`equipement/models.py`)
- **Rappel**: Nouveau modèle pour tracer les rappels envoyés
  - `emprunt`: Référence à l'emprunt
  - `type_rappel`: Type de rappel (1, 3 ou 7 jours)
  - `date_envoi`: Date et heure d'envoi
  - `email_destinataire`: Email de l'emprunteur
  - `statut_envoi`: Statut (envoyé ou échec)
  - `message_erreur`: Message d'erreur si applicable

### Services (`equipement/reminder_service.py`)
- **ReminderService**: Classe principale pour gérer les rappels
  - `get_overdue_emprunts()`: Récupère les emprunts en retard
  - `get_days_overdue()`: Calcule le nombre de jours de retard
  - `should_send_reminder()`: Détermine si un rappel doit être envoyé
  - `send_reminder_email()`: Envoie un email de rappel
  - `send_all_reminders()`: Envoie tous les rappels nécessaires

### Commandes Django (`equipement/management/commands/send_reminders.py`)
- Commande `send_reminders` pour exécuter l'envoi des rappels
- Utilisable via: `python manage.py send_reminders`
- Option `--verbose` pour afficher les détails

### Vues (`equipement/views.py`)
- `overdue_emprunts()`: Affiche la liste des emprunts en retard
- `rappels_list()`: Affiche l'historique des rappels envoyés
- `send_reminders_manual()`: Envoie manuellement les rappels

### Templates
- `equipement/overdue_emprunts.html`: Page affichant les emprunts en retard
- `equipement/rappels_list.html`: Page affichant l'historique des rappels

### Admin (`equipement/admin.py`)
- `RappelAdmin`: Interface d'administration pour gérer les rappels
  - Affichage coloré du statut d'envoi
  - Lien direct vers l'emprunt

### URLs (`equipement/urls.py`)
- `/emprunts/en-retard/`: Liste des emprunts en retard
- `/rappels/`: Historique des rappels
- `/rappels/envoyer/`: Envoyer les rappels manuellement

### Migration
- `0002_rappel.py`: Migration pour créer le modèle Rappel

## 🔧 Configuration

### Configuration Email (déjà faite dans `config/settings.py`)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jeanemmanuelmahop@gmail.com'
EMAIL_HOST_PASSWORD = 'flnabgmkmtcvrrbr'
DEFAULT_FROM_EMAIL = 'jeanemmanuelmahop@gmail.com'
```

## 📖 Utilisation

### 1. Appliquer les migrations
```bash
python manage.py migrate
```

### 2. Envoyer les rappels manuellement depuis le terminal
```bash
# Commande simple
python manage.py send_reminders

# Avec affichage détaillé
python manage.py send_reminders --verbose
```

### 3. Envoyer les rappels depuis le web
- Allez à: `/emprunts/en-retard/`
- Cliquez sur le bouton "📧 Envoyer les Rappels"

### 4. Consulter l'historique des rappels
- Allez à: `/rappels/`
- Filtrez par type de rappel ou statut d'envoi
- Consultez les détails et erreurs éventuelles

### 5. Voir les emprunts en retard
- Allez à: `/emprunts/en-retard/`
- Visualisez la liste avec le nombre de jours de retard

## ⏰ Scheduling Automatique (Optionnel)

Pour automatiser l'envoi des rappels, vous pouvez:

### Option 1: Utiliser Celery (Tâches asynchrones)
```python
# Dans equipement/tasks.py
from celery import shared_task
from .reminder_service import ReminderService

@shared_task
def send_reminders_task():
    return ReminderService.send_all_reminders()
```

### Option 2: Utiliser APScheduler
```bash
pip install django-apscheduler
```

### Option 3: Cron Job (Linux/Mac)
```bash
# Ajouter au crontab (tous les jours à 8h)
0 8 * * * cd /chemin/du/projet && python manage.py send_reminders
```

### Option 4: Task Scheduler (Windows)
- Créer une tâche programmée qui exécute:
  ```
  python manage.py send_reminders
  ```

## 📊 Schéma de la Logique

```
1. Détection des emprunts en retard
   ↓
2. Pour chaque emprunt en retard:
   - Vérifier les jours de retard
   - Si 1 jour et pas de rappel envoyé → Envoyer rappel 1 jour
   - Si 3 jours et pas de rappel envoyé → Envoyer rappel 3 jours
   - Si 7 jours et pas de rappel envoyé → Envoyer rappel 7 jours
   ↓
3. Enregistrer chaque rappel (succès ou erreur)
   ↓
4. Afficher le résumé des actions
```

## 📧 Contenu des Emails

Les emails contiennent:
- Prénom et nom de l'emprunteur
- Liste des matériels en retard
- Date de retour prévue
- Nombre de jours de retard
- Demande de retour rapide

## 🔒 Sécurité et Permissions

- Seuls les gestionnaires (managers) peuvent:
  - Voir les emprunts en retard
  - Consulter l'historique des rappels
  - Envoyer les rappels manuellement

## 🐛 Dépannage

### Les emails ne s'envoient pas
1. Vérifier la configuration SMTP dans `settings.py`
2. Vérifier les identifiants Gmail
3. Activer "Accès aux applications moins sûres" si Gmail
4. Vérifier la connexion Internet

### Pas de rappels trouvés
1. Vérifier qu'il y a des emprunts approuvés (`statut=APPROUVE`)
2. Vérifier que `date_retour_prevue` est définie et dépassée
3. Vérifier que `date_retour_reelle` est NULL

### Erreur lors de la migration
1. Vérifier que le modèle Rappel est bien défini
2. Exécuter: `python manage.py makemigrations equipement`
3. Puis: `python manage.py migrate`

## 🎯 Cas d'Usage

**Exemple**: Un emprunt dû le 20 avril
- **21 avril**: Rappel 1 jour envoyé
- **23 avril**: Rappel 3 jours envoyé
- **27 avril**: Rappel 7 jours envoyé

Le même type de rappel n'est envoyé qu'une seule fois par emprunt.

## 📝 Améliorations Futures

- [ ] Notifications SMS
- [ ] Rappels par SMS
- [ ] Escalade automatique (copie gestionnaire après X jours)
- [ ] Système de pénalités
- [ ] Dashboard des statistiques de retard
- [ ] Templates d'email personnalisables
- [ ] Multilangue pour les emails

## 👤 Auteur

Créé pour ISJ_L2_PROJET-TUTORE_GROUPE-6

## 📄 Licence

Interne au projet
