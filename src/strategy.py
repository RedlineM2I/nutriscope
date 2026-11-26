DEFAULT_STRATEGY = {
    # --- Identité / général ---
    "code": "keep",                          # jamais de manquant normalement, clé du produit
    "product_name": "keep",                  # texte libre, pas d'imputation qui aurait du sens
    "quantity": "drop_column",                      # texte libre, non structuré + 65% de la colonne vide
    "nutrition_data_per": "keep",             # déjà traité comme incertitude (booléen/NULL) plus haut dans le pipeline

    # --- Classification ---
    "brands_tags": "constant:unknown",         # une marque manquante n'empêche pas d'afficher le produit
    "categories_tags": "keep",                # déjà géré par traiter_categories_vides en amont
    "labels_tags": "constant:none",           # absence de label = "pas de label", valeur par défaut sûre
    "origins_tags": "constant:unknown",       # provenance non renseignée, affichage "unknown" acceptable
    "food_groups_tags": "keep",               # déjà géré par traiter_categories_vides (food_group dérivé)

    # --- Ingrédients ---
    "ingredients_tags": "constant:unknown",
    "additives_tags": "constant:none",        # absence d'additif listé peut aussi être une vraie absence

    # --- Nutrition (nutriments clés, cf. perimetre.md §8) ---
    "energy-kcal_100g": "flag",              # 28,7 % manquant — MNAR probable, l'absence est informative
    "fat_100g": "flag",
    "saturated-fat_100g": "flag",
    "carbohydrates_100g": "flag",
    "sugars_100g": "flag",                   # 29,3 % manquant
    "fiber_100g": "flag",                    # souvent >10 %, MNAR classique (peu de marques le déclarent)
    "proteins_100g": "flag",
    "salt_100g": "flag",                     # 33,7 % manquant
    "sodium_100g": "flag",

    # --- Scores ---
    "nutriscore_grade": "keep",               # c'est la cible potentielle du TP14, jamais imputée ici
    "nutriscore_score": "keep",               # idem, ne pas fuiter d'information avant le split ML
    "nova_group": "mode",                       # catégorie à 4 valeurs, le mode est une approximation raisonnable pour l'affichage
    "environmental_score_grade": "keep",      # score encore peu répandu, imputer serait trompeur
    "environmental_score_score": "keep",

    # --- Qualité ---
    "completeness": "keep",                   # sert justement à mesurer la qualité, ne pas la fausser
    "last_modified_t": "keep",                # horodatage technique, pas de sens à imputer

    # --- Images ---
    "images": "keep",                         # déjà couvert par le critère "au moins une image" du périmètre
}