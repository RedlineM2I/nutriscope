-- ============================================================
-- Requêtes de contrôle NutriScope
-- Version : 1.0
-- Date    : 2026-09-10
-- Objectif : contrôles de cohérence à rejouer après chaque chargement
--            (staging DuckDB -> Postgres), sur le schéma optimisé
--            schema_nutriscope_optimise.sql
-- ============================================================


-- ============================================================
-- 1. Volumétrie par table
-- ============================================================

SELECT 'produits' AS table_nom, COUNT(*) AS nb_lignes FROM produits
UNION ALL SELECT 'marques', COUNT(*) FROM marques
UNION ALL SELECT 'produits_marques', COUNT(*) FROM produits_marques
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'produits_categories', COUNT(*) FROM produits_categories
UNION ALL SELECT 'labels', COUNT(*) FROM labels
UNION ALL SELECT 'produits_labels', COUNT(*) FROM produits_labels
UNION ALL SELECT 'origines', COUNT(*) FROM origines
UNION ALL SELECT 'produits_origines', COUNT(*) FROM produits_origines
UNION ALL SELECT 'ingredients', COUNT(*) FROM ingredients
UNION ALL SELECT 'produits_ingredients', COUNT(*) FROM produits_ingredients
UNION ALL SELECT 'additifs', COUNT(*) FROM additifs
UNION ALL SELECT 'produits_additifs', COUNT(*) FROM produits_additifs
UNION ALL SELECT 'valeurs_nutritionnelles', COUNT(*) FROM valeurs_nutritionnelles
UNION ALL SELECT 'nutriments', COUNT(*) FROM nutriments
UNION ALL SELECT 'produits_nutriments_secondaires', COUNT(*) FROM produits_nutriments_secondaires
UNION ALL SELECT 'images', COUNT(*) FROM images
ORDER BY nb_lignes DESC;


-- ============================================================
-- 2. Produits sans catégorie
-- ============================================================

SELECT
    COUNT(*)                                                    AS nb_produits_sans_categorie,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM produits), 1) AS part_pct
FROM produits p
LEFT JOIN produits_categories pc ON pc.produit_id = p.id
WHERE pc.categorie_id IS NULL;

-- Détail (échantillon à inspecter à la main)
-- SELECT p.id, p.code, p.product_name
-- FROM produits p
-- LEFT JOIN produits_categories pc ON pc.produit_id = p.id
-- WHERE pc.categorie_id IS NULL
-- LIMIT 50;


-- ============================================================
-- 3. Top marques
-- ============================================================


SELECT
    m.nom          AS marque,
    COUNT(*)       AS nb_produits
FROM produits_marques pm
JOIN marques m ON m.id = pm.marque_id
GROUP BY m.nom
ORDER BY nb_produits DESC
LIMIT 20;


-- ============================================================
-- 4. Complétude Nutri-Score par rayon
-- ============================================================

WITH rayons AS (
    SELECT id, nom
    FROM categories
    WHERE nom IN (
        'snacks',
        'beverages',
        'meats',
        'fruits-and-vegetables-based-foods',
        'desserts',
        'cheeses',
        'fishes'
    )
)
SELECT
    r.nom                                                              AS rayon,
    COUNT(p.id)                                                        AS nb_produits,
    COUNT(p.nutriscore_grade)                                          AS nb_avec_nutriscore,
    ROUND(100.0 * COUNT(p.nutriscore_grade) / NULLIF(COUNT(p.id), 0), 2) AS pct_complet
FROM rayons r
JOIN produits_categories pc ON pc.categorie_id = r.id
JOIN produits p ON p.id = pc.produit_id
GROUP BY r.nom
ORDER BY pct_complet ASC;


-- ============================================================
-- 5. Doublons restants
-- ============================================================
SELECT
    code,
    COUNT(*) AS nb_occurrences
FROM produits
GROUP BY code
HAVING COUNT(*) > 1;