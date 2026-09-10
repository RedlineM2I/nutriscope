# Création de la base de donnée et de l'utilisateur

> Voici comment créer une base de données et un utilisateur PostgreSQL dédiés à Nutriscope, avec les bonnes pratiques de sécurité.

### 1. Se connecter en tant que superutilisateur

```bash
sudo -u postgres psql
```

### 2. Créer un utilisateur avec un mot de passe fort

```sql
CREATE USER nutriscope_app WITH PASSWORD 'un_mot_de_passe_fort_et_unique';
```

**Bonnes pratiques pour le mot de passe :**
- Générez-le aléatoirement (ex: `openssl rand -base64 32`), ne réutilisez jamais un mot de passe existant
- Ne le mettez **jamais en clair dans votre code** — stockez-le dans une variable d'environnement ou un gestionnaire de secrets (voir point 6)

### 3. Créer la base de données avec cet utilisateur comme propriétaire

```sql
CREATE DATABASE nutriscope_db OWNER nutriscope_app;
```

### 4. Limiter les privilèges au strict nécessaire (principe du moindre privilège)

Par défaut, PostgreSQL donne accès à toutes les bases à tout utilisateur connecté sur le rôle `public`. Il faut restreindre :

```sql
-- Révoquer l'accès public par défaut
REVOKE ALL ON DATABASE nutriscope_db FROM PUBLIC;

-- Donner uniquement les droits nécessaires à l'utilisateur applicatif
GRANT CONNECT ON DATABASE nutriscope_db TO nutriscope_app;
```

Ensuite, connecté à `nutriscope_db` :
```sql
\c nutriscope_db

GRANT USAGE ON SCHEMA public TO nutriscope_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nutriscope_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nutriscope_app;

-- Pour que les futures tables héritent aussi de ces droits
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO nutriscope_app;
```

⚠️ **Ne donnez surtout pas `SUPERUSER` ou `CREATEDB`/`CREATEROLE`** à l'utilisateur applicatif — il n'en a jamais besoin pour fonctionner, seulement pour lire/écrire ses propres données.

### 5. Restreindre les connexions réseau (`pg_hba.conf`)

Limitez qui peut se connecter et comment, dans `/etc/postgresql/<version>/main/pg_hba.conf` :

```
# Autoriser nutriscope_app uniquement en local (ou depuis l'IP de votre serveur app), avec mot de passe
host    nutriscope_db    nutriscope_app    127.0.0.1/32    scram-sha-256
```

Utilisez `scram-sha-256` comme méthode d'authentification (plus sécurisée que `md5`, qui est obsolète).

### 6. Ne jamais coder les identifiants en dur

Stockez les informations de connexion dans un fichier `.env` (jamais commité dans git) :

```bash
# .env
DB_NAME=nutriscope_db
DB_USER=nutriscope_app
DB_PASSWORD=un_mot_de_passe_fort_et_unique
DB_HOST=localhost
DB_PORT=5432
```