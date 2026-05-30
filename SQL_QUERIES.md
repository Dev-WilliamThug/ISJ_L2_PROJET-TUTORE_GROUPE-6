-- ============================================================
-- REQUÊTES SQL OPTIONNELLES - Système de Rappels
-- ============================================================
-- Ces requêtes sont optionnelles et pour usage avancé.
-- La plupart des opérations se font via Django ORM.
-- ============================================================

-- ============================================================
-- 1. EMPRUNTS EN RETARD - Requêtes d'Analyse
-- ============================================================

-- Tous les emprunts en retard avec nombre de jours
SELECT 
    e.id,
    e.date_retour_prevue,
    NOW()::DATE - e.date_retour_prevue as jours_retard,
    t.prenom,
    t.nom,
    t.email
FROM equipement_emprunt e
JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
WHERE e.date_retour_prevue < NOW()::DATE
  AND e.date_retour_reelle IS NULL
  AND e.statut = 'approuve'
ORDER BY e.date_retour_prevue ASC;

-- Emprunts en retard groupés par jours
SELECT 
    NOW()::DATE - e.date_retour_prevue as jours_retard,
    COUNT(*) as nombre_emprunts,
    COUNT(DISTINCT t.id_Tierce) as nombre_emprunteurs
FROM equipement_emprunt e
JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
WHERE e.date_retour_prevue < NOW()::DATE
  AND e.date_retour_reelle IS NULL
  AND e.statut = 'approuve'
GROUP BY NOW()::DATE - e.date_retour_prevue
ORDER BY jours_retard DESC;

-- Emprunteurs avec le plus de retards
SELECT 
    t.prenom,
    t.nom,
    t.email,
    COUNT(*) as nombre_retards,
    MAX(NOW()::DATE - e.date_retour_prevue) as max_jours_retard
FROM equipement_emprunt e
JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
WHERE e.date_retour_prevue < NOW()::DATE
  AND e.date_retour_reelle IS NULL
  AND e.statut = 'approuve'
GROUP BY t.id_Tierce, t.prenom, t.nom, t.email
ORDER BY nombre_retards DESC;

-- Matériels les plus souvent en retard
SELECT 
    m.nom,
    COUNT(*) as nombre_retards
FROM equipement_lignement el
JOIN equipement_emprunt e ON el.emprunt_id = e.id
JOIN equipement_materiel m ON el.materiel_id = m.id_materiel
WHERE e.date_retour_prevue < NOW()::DATE
  AND e.date_retour_reelle IS NULL
  AND e.statut = 'approuve'
GROUP BY m.id_materiel, m.nom
ORDER BY nombre_retards DESC;

-- ============================================================
-- 2. RAPPELS - Requêtes d'Analyse
-- ============================================================

-- Tous les rappels avec détails
SELECT 
    r.id,
    e.id as emprunt_id,
    t.prenom,
    t.nom,
    r.type_rappel,
    r.date_envoi,
    r.statut_envoi,
    CASE 
        WHEN r.message_erreur IS NOT NULL THEN r.message_erreur
        ELSE 'Envoyé avec succès'
    END as details
FROM equipement_rappel r
JOIN equipement_emprunt e ON r.emprunt_id = e.id
JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
ORDER BY r.date_envoi DESC;

-- Taux de réussite des rappels
SELECT 
    statut_envoi,
    COUNT(*) as nombre,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM equipement_rappel), 2) as pourcentage
FROM equipement_rappel
GROUP BY statut_envoi;

-- Rappels échoués avec raison
SELECT 
    r.id,
    t.email,
    r.type_rappel,
    r.date_envoi,
    r.message_erreur
FROM equipement_rappel r
JOIN equipement_emprunt e ON r.emprunt_id = e.id
JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
WHERE r.statut_envoi = 'echec'
ORDER BY r.date_envoi DESC;

-- Nombre de rappels envoyés par jour
SELECT 
    DATE(r.date_envoi) as jour,
    COUNT(*) as nombre_rappels,
    COUNT(CASE WHEN r.statut_envoi = 'envoye' THEN 1 END) as reussis,
    COUNT(CASE WHEN r.statut_envoi = 'echec' THEN 1 END) as echoues
FROM equipement_rappel r
GROUP BY DATE(r.date_envoi)
ORDER BY jour DESC;

-- Rappels par type
SELECT 
    type_rappel,
    COUNT(*) as nombre,
    COUNT(CASE WHEN statut_envoi = 'envoye' THEN 1 END) as reussis,
    COUNT(CASE WHEN statut_envoi = 'echec' THEN 1 END) as echoues
FROM equipement_rappel
GROUP BY type_rappel
ORDER BY nombre DESC;

-- ============================================================
-- 3. STATISTIQUES COMBINÉES
-- ============================================================

-- Vue d'ensemble du système de rappels
SELECT 
    (SELECT COUNT(*) FROM equipement_emprunt 
     WHERE date_retour_prevue < NOW()::DATE 
     AND date_retour_reelle IS NULL 
     AND statut = 'approuve') as emprunts_en_retard,
    
    (SELECT COUNT(*) FROM equipement_rappel
     WHERE statut_envoi = 'envoye') as rappels_envoyes,
    
    (SELECT COUNT(*) FROM equipement_rappel
     WHERE statut_envoi = 'echec') as rappels_echoues,
    
    (SELECT COUNT(*) FROM equipement_emprunt
     WHERE date_retour_prevue < NOW()::DATE 
     AND date_retour_reelle IS NULL 
     AND statut = 'approuve'
     AND id NOT IN (
         SELECT DISTINCT emprunt_id FROM equipement_rappel
     )) as emprunts_sans_rappel;

-- ============================================================
-- 4. OPÉRATIONS DE MAINTENANCE
-- ============================================================

-- Supprimer les doublons de rappels (si nécessaire)
-- ⚠️ À utiliser avec précaution!
-- DELETE FROM equipement_rappel r
-- WHERE r.id NOT IN (
--     SELECT MIN(id) FROM equipement_rappel 
--     GROUP BY emprunt_id, type_rappel
-- );

-- Réinitialiser les rappels pour un emprunt (test)
-- DELETE FROM equipement_rappel 
-- WHERE emprunt_id = [ID_EMPRUNT];

-- ============================================================
-- 5. EXPORTS DE DONNÉES
-- ============================================================

-- Export: Emprunts en retard (format rapport)
COPY (
    SELECT 
        e.id,
        e.date_retour_prevue::TEXT,
        (NOW()::DATE - e.date_retour_prevue)::TEXT as jours_retard,
        t.prenom || ' ' || t.nom as emprunteur,
        t.email,
        e.classe_id
    FROM equipement_emprunt e
    JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
    WHERE e.date_retour_prevue < NOW()::DATE
      AND e.date_retour_reelle IS NULL
      AND e.statut = 'approuve'
    ORDER BY e.date_retour_prevue ASC
) TO '/tmp/emprunts_retard.csv' WITH CSV HEADER;

-- Export: Rappels envoyés
COPY (
    SELECT 
        r.id,
        r.type_rappel,
        r.date_envoi::TEXT,
        r.statut_envoi,
        t.email,
        r.message_erreur
    FROM equipement_rappel r
    JOIN equipement_emprunt e ON r.emprunt_id = e.id
    JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
    ORDER BY r.date_envoi DESC
) TO '/tmp/rappels_envoy.csv' WITH CSV HEADER;

-- ============================================================
-- 6. INDEX OPTIMISÉS (optionnel)
-- ============================================================

-- Index pour les requêtes d'emprunts en retard
-- CREATE INDEX idx_emprunt_retard ON equipement_emprunt(date_retour_prevue, date_retour_reelle, statut);

-- Index pour les requêtes de rappels
-- CREATE INDEX idx_rappel_emprunt_type ON equipement_rappel(emprunt_id, type_rappel);
-- CREATE INDEX idx_rappel_date ON equipement_rappel(date_envoi);
-- CREATE INDEX idx_rappel_statut ON equipement_rappel(statut_envoi);

-- ============================================================
-- 7. VUES UTILES (Optionnel)
-- ============================================================

-- Créer une vue pour les emprunts en retard
-- CREATE OR REPLACE VIEW v_emprunts_retard AS
-- SELECT 
--     e.id,
--     e.date_retour_prevue,
--     NOW()::DATE - e.date_retour_prevue as jours_retard,
--     t.prenom,
--     t.nom,
--     t.email,
--     COUNT(r.id) as nombre_rappels
-- FROM equipement_emprunt e
-- JOIN equipement_tierce t ON e.emprunteur_id = t.id_Tierce
-- LEFT JOIN equipement_rappel r ON e.id = r.emprunt_id
-- WHERE e.date_retour_prevue < NOW()::DATE
--   AND e.date_retour_reelle IS NULL
--   AND e.statut = 'approuve'
-- GROUP BY e.id, e.date_retour_prevue, t.id_Tierce, t.prenom, t.nom, t.email;

-- Créer une vue pour les stats de rappels
-- CREATE OR REPLACE VIEW v_stats_rappels AS
-- SELECT 
--     DATE(date_envoi) as jour,
--     statut_envoi,
--     COUNT(*) as nombre
-- FROM equipement_rappel
-- GROUP BY DATE(date_envoi), statut_envoi;

-- ============================================================
-- 8. REQUÊTES DE TEST
-- ============================================================

-- Vérifier la structure du modèle Rappel
-- \d equipement_rappel;

-- Voir les colonnes du modèle Emprunt
-- \d equipement_emprunt;

-- Voir tous les types de rappels distincts
SELECT DISTINCT type_rappel FROM equipement_rappel ORDER BY type_rappel;

-- Vérifier que les contraintes unique fonctionnent
SELECT emprunt_id, type_rappel, COUNT(*) 
FROM equipement_rappel 
GROUP BY emprunt_id, type_rappel 
HAVING COUNT(*) > 1;
-- (Devrait retourner 0 lignes)

-- ============================================================
-- NOTES D'UTILISATION
-- ============================================================
-- 
-- 1. Ces requêtes utilisent PostgreSQL
--    (Compatible avec Django sur DB PostgreSQL)
-- 
-- 2. Pour exécuter depuis Django:
--    python manage.py dbshell
--    Puis coller les requêtes
--
-- 3. Pour exporter les résultats:
--    psql -U postgres -d gestionEquipement -c "SELECT ..."
--
-- 4. N'exécuter les DELETE que si vous êtes sûr!
--    Toujours tester d'abord avec SELECT
--
-- 5. Les vues/index sont optionnels mais recommandés en prod
--
-- ============================================================
