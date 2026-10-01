DROP TABLE IF EXISTS products_secondary_nutrients CASCADE;
DROP TABLE IF EXISTS products_additives CASCADE;
DROP TABLE IF EXISTS products_labels CASCADE;
DROP TABLE IF EXISTS products_brands CASCADE;
DROP TABLE IF EXISTS products_origins CASCADE;
DROP TABLE IF EXISTS products_categories CASCADE;
DROP TABLE IF EXISTS products_ingredients CASCADE;
DROP TABLE IF EXISTS secondary_nutrients CASCADE;
DROP TABLE IF EXISTS products CASCADE ;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS origins CASCADE;
DROP TABLE IF EXISTS additives CASCADE;
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS brands CASCADE;
DROP TABLE IF EXISTS labels CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS nutritional_values CASCADE;

-- ============================================================
-- OpenFoodFacts relational schema (for dbdiagram.io)
-- ============================================================

-- Created before products, which references categories (id)
CREATE TABLE categories
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

-- Main table: one product per barcode
CREATE TABLE products
(
    id                        SERIAL PRIMARY KEY,
    code                      VARCHAR UNIQUE NOT NULL,
    product_name              VARCHAR,
    quantity                  VARCHAR,
    main_category             INTEGER REFERENCES categories (id),
    foodgroup_id             INTEGER REFERENCES foodgroups (id),
    nutrition_data_per        VARCHAR,
    nutriscore_grade          VARCHAR, -- CHAR(1) CHECK (nutriscore_grade IN ('a','b','c','d','e'))
    nutriscore_score          SMALLINT,
    nova_group                SMALLINT CHECK (nova_group BETWEEN 1 AND 4),
    completeness              REAL,
    environmental_score_grade VARCHAR, -- CHAR(1) CHECK (environmental_score_grade IN ('a','b','c','d','e'))
    environmental_score_score SMALLINT,
    last_modified_t           DATETIME
);

CREATE TABLE foodgroups
(
    id  SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL
);

-- ============================================================
-- Classification (many-to-many relations via link tables)
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

CREATE TABLE products_categories
(
    product_id   INTEGER REFERENCES products (id),
    category_id INTEGER REFERENCES categories (id),
    PRIMARY KEY (product_id, category_id)

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
-- Ingredients
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
-- Nutrition (one product has several nutrient rows)
-- ============================================================

CREATE TABLE nutritional_values
(
    product_id          INTEGER REFERENCES products (id),
    energy_100g         FLOAT, -- in kJ
    fat_100g            FLOAT,
    saturated_fat_100g  FLOAT,
    carbohydrates_100g  FLOAT,
    sugars_100g         FLOAT,
    fiber_100g          FLOAT,
    proteins_100g       FLOAT,
    salt_100g           FLOAT,
    fruits_nuts_100g    FLOAT,
    fruits_legumes_100g FLOAT
);

CREATE TABLE secondary_nutrients
(
    id    SMALLINT PRIMARY KEY,
    name   VARCHAR UNIQUE,
    unit VARCHAR
);

CREATE TABLE products_secondary_nutrients
(
    product_id   INTEGER REFERENCES products (id),
    nutrient_id SMALLINT REFERENCES secondary_nutrients (id),
    value_100g  REAL,
    PRIMARY KEY (product_id, nutrient_id)
);

-- ============================================================
-- Images (several photos per product)
-- ============================================================

CREATE TABLE images
(
    id         SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products (id),
    url        VARCHAR,
    type       VARCHAR,
    language     VARCHAR
);
