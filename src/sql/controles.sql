-- @nom: comptage_par_rayon
SELECT food_group AS rayon,
       count(*) AS produits,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS part_pct
FROM produits
GROUP BY food_group
ORDER BY produits DESC;

-- @nom: completude
SELECT food_group AS rayon,
       count(*) AS produits,
       round(100.0 * count(*) FILTER (WHERE nutriscore_grade IN ('a','b','c','d','e')) / count(*), 2) AS nutriscore_pct,
       round(100.0 * count(*) FILTER (WHERE "energy-kcal_100g" IS NOT NULL
                                        AND fat_100g IS NOT NULL
                                        AND "saturated-fat_100g" IS NOT NULL
                                        AND carbohydrates_100g IS NOT NULL
                                        AND sugars_100g IS NOT NULL
                                        AND proteins_100g IS NOT NULL
                                        AND salt_100g IS NOT NULL) / count(*), 2) AS nutriments_cles_pct,
       round(100.0 * count(*) FILTER (WHERE nullif(main_category, 'unknown') IS NOT NULL) / count(*), 2) AS categorie_pct
FROM produits
GROUP BY food_group
ORDER BY produits DESC;

-- @nom: doublons_codes
SELECT count(*) AS groupes_en_double,
       coalesce(sum(n - 1), 0) AS lignes_en_trop
FROM (SELECT code, count(*) AS n FROM produits GROUP BY code HAVING count(*) > 1);

-- @nom: doublons_nom_marque
-- Pas de colonne marque dans le Parquet : on utilise nom + catégorie principale
SELECT product_name, brand, count(*) AS n
FROM produits
WHERE product_name IS NOT NULL
GROUP BY product_name, brand
HAVING count(*) > 1
ORDER BY n DESC
LIMIT 20;

-- @nom: bornes_et_coherences
SELECT
  count(*) FILTER (WHERE fat_100g < 0 OR fat_100g > 100
                      OR "saturated-fat_100g" < 0 OR "saturated-fat_100g" > 100
                      OR carbohydrates_100g < 0 OR carbohydrates_100g > 100
                      OR sugars_100g < 0 OR sugars_100g > 100
                      OR proteins_100g < 0 OR proteins_100g > 100
                      OR salt_100g < 0 OR salt_100g > 100)        AS nutriments_hors_0_100,
  count(*) FILTER (WHERE "energy-kcal_100g" < 0 OR "energy-kcal_100g" > 900) AS energie_hors_0_900,
  count(*) FILTER (WHERE sugars_100g > carbohydrates_100g)         AS sucres_sup_glucides,
  count(*) FILTER (WHERE "saturated-fat_100g" > fat_100g)          AS satures_sup_lipides,
  count(*) FILTER (WHERE "energy-kcal_100g" = 0
                     AND (fat_100g + carbohydrates_100g + proteins_100g) > 0) AS energie_nulle_avec_macros,
  count(*) FILTER (WHERE abs(salt_100g - sodium_100g * 2.5) > 0.1) AS sel_incoherent
FROM produits;

-- @nom: distribution_nutriscore
SELECT coalesce(nutriscore_grade, 'null') AS grade,
       count(*) AS produits,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS part_pct,
       round(avg(nutriscore_score), 2) AS score_moyen
FROM produits
GROUP BY 1
ORDER BY 1;