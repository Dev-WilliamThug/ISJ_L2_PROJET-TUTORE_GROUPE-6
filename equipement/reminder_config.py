"""
Configuration du système de rappels pour les emprunts en retard.
Ce fichier peut être customisé pour adapter les paramètres à vos besoins.
"""

# Seuils de jours de retard pour l'envoi des rappels
REMINDER_THRESHOLDS = {
    'RETARD_1_JOUR': 1,    # Envoyer un rappel après 1 jour de retard
    'RETARD_3_JOURS': 3,   # Envoyer un rappel après 3 jours de retard
    'RETARD_7_JOURS': 7,   # Envoyer un rappel après 7 jours de retard
}

# Template du message email
EMAIL_REMINDER_TEMPLATE = """
Bonjour {prenom} {nom},

Nous vous rappelons que vous avez actuellement du matériel en retard :

Matériel(s): {materiels}
Date de retour prévue: {date_retour}
Nombre de jours de retard: {jours_retard}

Veuillez retourner le matériel au plus vite possible.

Cordialement,
L'équipe de gestion des équipements
"""

# Sujet du message email
EMAIL_REMINDER_SUBJECT = "Rappel : Retour de matériel en retard"

# Configuration des permissions
PERMISSIONS = {
    'view_reminders': ['gestionnaire', 'administrateur'],
    'send_reminders': ['gestionnaire', 'administrateur'],
    'view_overdue': ['gestionnaire', 'administrateur'],
}

# Configuration du logging
LOGGING_REMINDERS = {
    'enable': True,
    'log_file': 'logs/reminders.log',
    'log_level': 'INFO',
}

# Configuration de l'escalade (Futur)
ESCALATION = {
    'enable': False,  # Activer l'escalade
    'escalation_days': 14,  # Escalader après 14 jours
    'escalation_recipients': ['gestionnaire@example.com'],  # Qui avertir
}

# Filtres par défaut
DEFAULT_FILTERS = {
    'filter_by_status': 'APPROUVE',  # Filtrer par statut d'emprunt
    'exclude_returned': True,  # Exclure les emprunts retournés
}

# Configuration du cache (optionnel)
CACHE_REMINDERS = {
    'enable': False,
    'timeout': 3600,  # 1 heure en secondes
}

# Configuration des notifications (Futur)
NOTIFICATIONS = {
    'email': True,
    'sms': False,
    'dashboard': True,  # Afficher sur le dashboard
}

def get_reminder_thresholds():
    """Retourner les seuils de rappels configurés."""
    return REMINDER_THRESHOLDS

def get_email_template():
    """Retourner le template d'email."""
    return EMAIL_REMINDER_TEMPLATE

def get_permission(action):
    """Vérifier si un utilisateur a la permission pour une action."""
    return PERMISSIONS.get(action, [])

def is_escalation_enabled():
    """Vérifier si l'escalade est activée."""
    return ESCALATION.get('enable', False)
