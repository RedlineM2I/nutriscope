-- ============================================================
-- Requêtes de contrôle NutriScope
-- Version : 1.0
-- Date    : 2026-09-10
-- Objectif : contrôles de cohérence à rejouer après chaque chargement
--            (staging DuckDB -> Postgres), sur le schéma optimisé
--            create_tables.sql
-- ============================================================


-- ============================================================
-- 1. Volumétrie par table
-- ============================================================

SELECT 'products' AS table_name, COUNT(*) AS row_count FROM products
UNION ALL SELECT 'brands', COUNT(*) FROM brands
UNION ALL SELECT 'products_brands', COUNT(*) FROM products_brands
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'products_categories', COUNT(*) FROM products_categories
UNION ALL SELECT 'labels', COUNT(*) FROM labels
UNION ALL SELECT 'products_labels', COUNT(*) FROM products_labels
UNION ALL SELECT 'origins', COUNT(*) FROM origins
UNION ALL SELECT 'products_origins', COUNT(*) FROM products_origins
UNION ALL SELECT 'ingredients', COUNT(*) FROM ingredients
UNION ALL SELECT 'products_ingredients', COUNT(*) FROM products_ingredients
UNION ALL SELECT 'additives', COUNT(*) FROM additives
UNION ALL SELECT 'products_additives', COUNT(*) FROM products_additives
UNION ALL SELECT 'nutritional_values', COUNT(*) FROM nutritional_values
UNION ALL SELECT 'secondary_nutriments', COUNT(*) FROM secondary_nutriments
UNION ALL SELECT 'products_secondary_nutriments', COUNT(*) FROM products_secondary_nutriments
UNION ALL SELECT 'images', COUNT(*) FROM images
ORDER BY row_count DESC;


-- ============================================================
-- 2. Produits sans catégorie
-- ============================================================

SELECT
    COUNT(*)                                                    AS nb_products_without_category,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM products), 1) AS share_pct
FROM products p
LEFT JOIN products_categories pc ON pc.product_id = p.id
WHERE pc.categorie_id IS NULL;

-- Détail (échantillon à inspecter à la main)
-- SELECT p.id, p.code, p.product_name
-- FROM products p
-- LEFT JOIN products_categories pc ON pc.product_id = p.id
-- WHERE pc.categorie_id IS NULL
-- LIMIT 50;


-- ============================================================
-- 3. Top marques
-- ============================================================


SELECT
    b.name         AS brand,
    COUNT(*)       AS nb_products
FROM products_brands pb
JOIN brands b ON b.id = pb.brand_id
GROUP BY b.name
ORDER BY nb_products DESC
LIMIT 20;


-- ============================================================
-- 4. Complétude Nutri-Score par rayon
-- ============================================================

WITH aisles AS (
    SELECT id, name
    FROM categories
    WHERE name IN (
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
    a.name                                                             AS aisle,
    COUNT(p.id)                                                        AS nb_products,
    COUNT(p.nutriscore_grade)                                          AS nb_with_nutriscore,
    ROUND(100.0 * COUNT(p.nutriscore_grade) / NULLIF(COUNT(p.id), 0), 2) AS completeness_pct
FROM aisles a
JOIN products_categories pc ON pc.categorie_id = a.id
JOIN products p ON p.id = pc.product_id
GROUP BY a.name
ORDER BY completeness_pct ASC;


-- ============================================================
-- 5. Doublons restants
-- ============================================================
SELECT
    code,
    COUNT(*) AS nb_occurrences
FROM products
GROUP BY code
HAVING COUNT(*) > 1;
