DROP TABLE IF EXISTS produits CASCADE ;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS origines CASCADE;
DROP TABLE IF EXISTS additifs CASCADE;
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS nutriments CASCADE;
DROP TABLE IF EXISTS marques CASCADE;
DROP TABLE IF EXISTS labels CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS produits_additifs CASCADE;
DROP TABLE IF EXISTS produits_labels CASCADE;
DROP TABLE IF EXISTS produits_marques CASCADE;
DROP TABLE IF EXISTS produits_origines CASCADE;
DROP TABLE IF EXISTS produits_categories CASCADE;
DROP TABLE IF EXISTS produits_ingredients CASCADE;
DROP TABLE IF EXISTS produits_nutriments CASCADE;

-- ============================================================
-- Schéma relationnel OpenFoodFacts (pour dbdiagram.io)
-- ============================================================

-- Table principale : un produit par code-barres
CREATE TABLE produits
(
    code                      VARCHAR PRIMARY KEY,
    product_name              VARCHAR,
    quantity                  VARCHAR,
    nutrition_data_per        VARCHAR,
    nutriscore_grade          VARCHAR,
    nutriscore_score          INTEGER,
    nova_group                INTEGER,
    completeness              FLOAT,
    environmental_score_grade VARCHAR,
    environmental_score_score INTEGER
);

-- ============================================================
-- Classification (relations many-to-many via tables de liaison)
-- ============================================================

CREATE TABLE marques
(
    id  SERIAL PRIMARY KEY,
    nom VARCHAR UNIQUE NOT NULL
);

CREATE TABLE produits_marques
(
    produit_code VARCHAR REFERENCES produits (code),
    marque_id    INTEGER REFERENCES marques (id),
    PRIMARY KEY (produit_code, marque_id)
);

CREATE TABLE categories
(
    id  SERIAL PRIMARY KEY,
    nom VARCHAR UNIQUE NOT NULL
);

CREATE TABLE produits_categories
(
    produit_code VARCHAR REFERENCES produits (code),
    categorie_id INTEGER REFERENCES categories (id),
    PRIMARY KEY (produit_code, categorie_id)
);

CREATE TABLE labels
(
    id  SERIAL PRIMARY KEY,
    nom VARCHAR UNIQUE NOT NULL
);

CREATE TABLE produits_labels
(
    produit_code VARCHAR REFERENCES produits (code),
    label_id     INTEGER REFERENCES labels (id),
    PRIMARY KEY (produit_code, label_id)
);

CREATE TABLE origines
(
    id  SERIAL PRIMARY KEY,
    nom VARCHAR UNIQUE NOT NULL
);

CREATE TABLE produits_origines
(
    produit_code VARCHAR REFERENCES produits (code),
    origine_id   INTEGER REFERENCES origines (id),
    PRIMARY KEY (produit_code, origine_id)
);

-- ============================================================
-- Ingrédients
-- ============================================================

CREATE TABLE ingredients
(
    id  SERIAL PRIMARY KEY,
    nom VARCHAR UNIQUE NOT NULL
);

CREATE TABLE produits_ingredients
(
    produit_code  VARCHAR REFERENCES produits (code),
    ingredient_id INTEGER REFERENCES ingredients (id),
    PRIMARY KEY (produit_code, ingredient_id)
);

CREATE TABLE additifs
(
    id  SERIAL PRIMARY KEY,
    nom VARCHAR UNIQUE NOT NULL
);

CREATE TABLE produits_additifs
(
    produit_code VARCHAR REFERENCES produits (code),
    additif_id   INTEGER REFERENCES additifs (id),
    PRIMARY KEY (produit_code, additif_id)
);

-- ============================================================
-- Nutrition (un produit a plusieurs lignes de nutriments)
-- ============================================================

CREATE TABLE nutriments
(
    id         SERIAL PRIMARY KEY,
    name       VARCHAR,
    value_100g FLOAT,
    unit       VARCHAR
);
CREATE TABLE produits_nutriments
(
    produit_code  VARCHAR REFERENCES produits (code),
    nutriments_id INTEGER REFERENCES nutriments (id),
    PRIMARY KEY (produit_code, nutriments_id)
);

-- ============================================================
-- Images (plusieurs photos par produit)
-- ============================================================

CREATE TABLE images
(
    id           SERIAL PRIMARY KEY,
    produit_code VARCHAR REFERENCES produits (code),
    url          VARCHAR,
    type         VARCHAR,
    langue       VARCHAR
);