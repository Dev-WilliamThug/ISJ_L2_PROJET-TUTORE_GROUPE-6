# 🚀 DÉMARRAGE EN 5 MINUTES

## ⚡ TL;DR (Trop Long; Pas Lu)

```bash
# 1. Appliquer la migration
python manage.py migrate equipement

# 2. Tester (optionnel)
python manage.py test equipement.tests_reminders

# 3. Envoyer les rappels
python manage.py send_reminders --verbose

# 4. Ouvrir dans le navigateur
# http://localhost:8000/equipement/emprunts/en-retard/
# http://localhost:8000/equipement/rappels/
```

---

## ✅ Checklist d'Installation

- [ ] Exécuter: `python manage.py migrate equipement`
- [ ] Vérifier qu'aucune erreur n'apparait
- [ ] Redémarrer le serveur Django: `python manage.py runserver`
- [ ] Tester les URLs dans le navigateur
- [ ] Exécuter: `python manage.py send_reminders --verbose`
- [ ] Consulter le fichier `REMINDER_SYSTEM_README.md` pour plus de détails

---

## 📍 Accès Rapide

| Fonction | URL |
|----------|-----|
| **Emprunts en retard** | http://localhost:8000/equipement/emprunts/en-retard/ |
| **Historique rappels** | http://localhost:8000/equipement/rappels/ |
| **Admin Django** | http://localhost:8000/admin/equipement/rappel/ |
| **Envoyer rappels** | Bouton 📧 sur la page des emprunts en retard |

---

## 🔄 Flux de Travail Quotidien

### Matin (Automatique ou Manuel)
```bash
# Envoyer les rappels
python manage.py send_reminders --verbose
```

### Administration
```
1. Allez à /equipement/emprunts/en-retard/
2. Visualisez les emprunts en retard
3. Cliquez "📧 Envoyer les Rappels" (ou utilisez la commande)
```

### Consultation
```
1. Allez à /equipement/rappels/
2. Filtrez par type ou statut
3. Consultez l'historique complet
```

---

## 📊 Cas Simple

**Créer un test rapide:**

1. Allez au dashboard
2. Créez un emprunt avec date retour = **hier**
3. Allez à `/equipement/emprunts/en-retard/`
4. Vous devriez voir l'emprunt
5. Cliquez "📧 Envoyer les Rappels"
6. L'email est envoyé à `jeanemmanuelmahop@gmail.com`

---

## 🛑 En Cas de Problème

### Erreur: "No migrations found"
```bash
python manage.py makemigrations equipement
python manage.py migrate equipement
```

### Pas d'emprunts affichés
- Vérifier qu'il y a des emprunts avec `date_retour_prevue` < aujourd'hui
- Vérifier que `date_retour_reelle` est NULL
- Vérifier que le statut est APPROUVE

### Emails ne s'envoient pas
- Tester: `python manage.py shell`
  ```python
  from django.core.mail import send_mail
  send_mail('Test', 'Test', 'from@gmail.com', ['to@test.com'])
  ```

---

## 📁 Fichiers Importants

```
📦 Système de Rappels
├── 📄 SYNTHESE_CREATION.md ← Résumé complet
├── 📄 REMINDER_SYSTEM_README.md ← Documentation complète
├── 📄 INSTALLATION_REMINDERS.md ← Guide détaillé
├── 📄 SQL_QUERIES.md ← Requêtes SQL (optionnel)
├── 🐍 equipement/reminder_service.py ← Moteur
├── 🐍 equipement/reminder_config.py ← Configuration
├── 🐍 equipement/management/commands/send_reminders.py ← Commande
├── 🌐 equipement/templates/equipement/overdue_emprunts.html
├── 🌐 equipement/templates/equipement/rappels_list.html
└── 📝 equipement/tests_reminders.py ← Tests
```

---

## 🎯 Étapes Recommandées

### Jour 1: Installation
```bash
python manage.py migrate equipement
python manage.py test equipement.tests_reminders
```

### Jour 2: Test Manuel
```bash
# Créer un emprunt en retard dans l'admin
# Puis exécuter:
python manage.py send_reminders --verbose
```

### Jour 3: Mise en Automatique
```bash
# Ajouter au crontab (Linux/Mac)
0 8 * * * cd /chemin/du/projet && python manage.py send_reminders
```

---

## 💡 Tips Utiles

```bash
# Voir l'aide de la commande
python manage.py send_reminders --help

# Voir les logs détaillés
python manage.py send_reminders --verbose

# Lancer les tests
python manage.py test equipement.tests_reminders -v 2

# Ouvrir le shell Django
python manage.py shell

# Accéder à PostgreSQL
python manage.py dbshell
```

---

## 🔐 Permissions

Seuls **gestionnaires** et **administrateurs** peuvent:
- Voir les emprunts en retard
- Consulter les rappels
- Envoyer les rappels

---

## ⏰ Automation (Optionnel)

### Linux/Mac (Cron)
```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (tous les jours à 8h)
0 8 * * * cd /chemin/du/projet && python manage.py send_reminders >> /var/log/reminders.log 2>&1
```

### Windows (Task Scheduler)
1. Créer `send_reminders.bat`:
   ```batch
   @echo off
   cd e:\FinTuto\ISJ_L2_PROJET-TUTORE_GROUPE-6
   python manage.py send_reminders
   ```
2. Créer une tâche planifiée qui exécute ce fichier chaque matin

---

## 📞 Support Rapide

| Problème | Solution |
|----------|----------|
| Pas d'emprunts | Créer un emprunt avec date passée |
| Pas d'emails | Tester config SMTP dans settings.py |
| Erreur migration | Exécuter makemigrations puis migrate |
| Permission refusée | Vérifier que l'utilisateur est gestionnaire |

---

## 🎓 Pour en Savoir Plus

📖 Lire dans cet ordre:
1. Ce fichier (QUICK_START.md) ← Vous êtes ici
2. SYNTHESE_CREATION.md ← Résumé du projet
3. REMINDER_SYSTEM_README.md ← Documentation complète
4. Code source avec commentaires

---

## ✨ C'est Tout!

Le système est **prêt à l'emploi**. 

Juste exécuter:
```bash
python manage.py migrate equipement
```

Et c'est fait! 🎉

---

**Créé:** Mai 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready
