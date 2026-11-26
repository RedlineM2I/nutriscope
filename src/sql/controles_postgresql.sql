-- 1. Volumétrie et doublons
SELECT count(*) AS produits, count(DISTINCT code) AS codes_distincts FROM products;

-- 2. Comptage par rayon (= contrôle 1)
SELECT f.name AS rayon, count(*) AS produits,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS part_pct
FROM products p
LEFT JOIN foodgroups f ON f.id = p.foodgroup_id
GROUP BY f.name
ORDER BY produits DESC;

-- 3. Distribution du Nutri-Score (= contrôle 5)
SELECT coalesce(nutriscore_grade, 'null') AS grade, count(*) AS produits,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS part_pct,
       round(avg(nutriscore_score), 2) AS score_moyen
FROM products GROUP BY 1 ORDER BY 1;

-- 4. Hors bornes (= contrôle 4, mêmes 6 nutriments que le SQL DuckDB)
SELECT count(*) AS nutriments_hors_0_100
FROM nutritional_values
WHERE fat_100g NOT BETWEEN 0 AND 100
   OR saturated_fat_100g NOT BETWEEN 0 AND 100
   OR carbohydrates_100g NOT BETWEEN 0 AND 100
   OR sugars_100g NOT BETWEEN 0 AND 100
   OR proteins_100g NOT BETWEEN 0 AND 100
   OR salt_100g NOT BETWEEN 0 AND 100;

-- 5. Cohérences (= fin du contrôle 4)
SELECT count(*) FILTER (WHERE sugars_100g > carbohydrates_100g) AS sucres_sup_glucides,
       count(*) FILTER (WHERE saturated_fat_100g > fat_100g)    AS satures_sup_lipides
FROM nutritional_values;