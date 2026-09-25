DROP TABLE IF EXISTS produits_nutriments_secondaires CASCADE;
DROP TABLE IF EXISTS produits_additifs CASCADE;
DROP TABLE IF EXISTS produits_labels CASCADE;
DROP TABLE IF EXISTS produits_marques CASCADE;
DROP TABLE IF EXISTS produits_origines CASCADE;
DROP TABLE IF EXISTS produits_categories CASCADE;
DROP TABLE IF EXISTS produits_ingredients CASCADE;
DROP TABLE IF EXISTS nutriments CASCADE;
DROP TABLE IF EXISTS produits CASCADE ;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS origins CASCADE;
DROP TABLE IF EXISTS additives CASCADE;
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS brands CASCADE;
DROP TABLE IF EXISTS labels CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS nutritional_values CASCADE;

-- ============================================================
-- Schéma relationnel OpenFoodFacts (pour dbdiagram.io)
-- ============================================================

-- Table principale : un produit par code-barres
CREATE TABLE products
(
    id                        SERIAL PRIMARY KEY,
    code                      VARCHAR UNIQUE NOT NULL,
    product_name              VARCHAR,
    quantity                  VARCHAR,
    main_category             INTEGER REFERENCES categories (id),
    nutrition_data_per        VARCHAR,
    nutriscore_grade          VARCHAR, -- CHAR(1) CHECK (nutriscore_grade IN ('a','b','c','d','e'))
    nutriscore_score          SMALLINT,
    nova_group                SMALLINT CHECK (nova_group BETWEEN 1 AND 4),
    completeness              REAL,
    environmental_score_grade VARCHAR, -- CHAR(1) CHECK (environmental_score_grade IN ('a','b','c','d','e'))
    environmental_score_score SMALLINT
);

-- ============================================================
-- Classification (relations many-to-many via tables de liaison)
-- ============================================================

CREATE TABLE brands
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE products_brands
(
    product_id INTEGER REFERENCES products (id),
    brand_id  INTEGER REFERENCES brands (id),
    PRIMARY KEY (product_id, brand_id)
);

CREATE TABLE categories
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE products_categories
(
    product_id   INTEGER REFERENCES products (id),
    categorie_id INTEGER REFERENCES categories (id),
    PRIMARY KEY (product_id, categorie_id)

);

CREATE TABLE labels
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE products_labels
(
    product_id INTEGER REFERENCES products (id),
    label_id   INTEGER REFERENCES labels (id),
    PRIMARY KEY (product_id, label_id)
);

CREATE TABLE origins
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE products_origins
(
    product_id INTEGER REFERENCES products (id),
    origin_id INTEGER REFERENCES origins (id),
    PRIMARY KEY (product_id, origin_id)
);

-- ============================================================
-- Ingrédients
-- ============================================================

CREATE TABLE ingredients
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE products_ingredients
(
    product_id    INTEGER REFERENCES products (id),
    ingredient_id INTEGER REFERENCES ingredients (id),
    PRIMARY KEY (product_id, ingredient_id)
);

CREATE TABLE additives
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE products_additives
(
    product_id INTEGER REFERENCES products (id),
    additive_id INTEGER REFERENCES additives (id),
    PRIMARY KEY (product_id, additive_id)
);

-- ============================================================
-- Nutrition (un produit a plusieurs lignes de nutriments)
-- ============================================================

CREATE TABLE nutritional_values
(
    product_id               INTEGER REFERENCES products (id),
    energie_100g             FLOAT, --En kJ
    matieres_grasses_100g    FLOAT,
    acides_gras_satures_100g FLOAT,
    glucides_100g            FLOAT,
    sucres_100g              FLOAT,
    fibres_100g              FLOAT,
    proteines_100g           FLOAT,
    sel_100g                 FLOAT,
    fruits_nuts_100g         FLOAT,
    fruits_legumes_100g      FLOAT
);

CREATE TABLE nutriments_secondaires
(
    id    SMALLINT PRIMARY KEY,
    name   VARCHAR UNIQUE,
    unit VARCHAR
);

CREATE TABLE products_nutriments_secondary
(
    produit_id   INTEGER REFERENCES produits (id),
    nutriment_id SMALLINT REFERENCES nutriments (id),
    valeur_100g  REAL,
    PRIMARY KEY (product_id, nutriment_id)
);

-- ============================================================
-- Images (plusieurs photos par produit)
-- ============================================================

CREATE TABLE images
(
    id         SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products (id),
    url        VARCHAR,
    type       VARCHAR,
    language     VARCHAR
);