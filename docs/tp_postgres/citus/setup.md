# Setup — Cluster, tables et distribution

## Étape 1 — Préparer l'environnement Docker

### Créer le dossier de travail

```bash
mkdir ~/citus_tp && cd ~/citus_tp
```

### Créer le fichier docker-compose.yml

```bash
nano docker-compose.yml
```

Copiez le contenu suivant, puis sauvegardez avec `Ctrl+O` et quittez avec `Ctrl+X` :

```yaml
networks:
  citus_network:
    driver: bridge

services:

  coordinateur:
    image: citusdata/citus:12.1.3
    container_name: citus_coordinateur
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: admin
      POSTGRES_DB: flowshop_db
      POSTGRES_HOST_AUTH_METHOD: trust
    networks:
      - citus_network

  worker1:
    image: citusdata/citus:12.1.3
    container_name: citus_worker1
    ports:
      - "5433:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: admin
      POSTGRES_DB: flowshop_db
      POSTGRES_HOST_AUTH_METHOD: trust
    networks:
      - citus_network

  worker2:
    image: citusdata/citus:12.1.3
    container_name: citus_worker2
    ports:
      - "5434:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: admin
      POSTGRES_DB: flowshop_db
      POSTGRES_HOST_AUTH_METHOD: trust
    networks:
      - citus_network
```

!!! warning
    `POSTGRES_HOST_AUTH_METHOD: trust` autorise les connexions entre nœuds sans mot de passe sur le réseau Docker interne. Sans cette option, le coordinateur ne peut pas interroger les workers et toute requête distribuée échoue avec `fe_sendauth: no password supplied`.

---

## Étape 2 — Démarrer le cluster progressivement

### a. Démarrage du coordinateur

```bash
sudo docker-compose up -d coordinateur
sudo docker ps
sudo docker exec -it citus_coordinateur psql -U postgres -d flowshop_db
```

```sql
SELECT citus_version();
```

Vous devez voir le numéro de version de Citus. Quittez avec `\q`.

### b. Ajouter le premier worker

Dans un autre terminal, démarrez le worker1 :

```bash
sudo docker-compose up -d worker1
sudo docker ps
```

Sur le coordinateur, déclarez le worker :

```sql
SELECT citus_add_node('citus_worker1', 5432);
SELECT * FROM citus_get_active_worker_nodes();
```

Vous devez voir une ligne avec `citus_worker1`.

### c. Ajouter le second worker

```bash
sudo docker-compose up -d worker2
```

```sql
SELECT citus_add_node('citus_worker2', 5432);
SELECT * FROM citus_get_active_worker_nodes();
```

Vous devez voir deux lignes. Le cluster est prêt.

---

## Étape 3 — Créer et distribuer les tables

Connectez-vous au coordinateur :

```bash
sudo docker exec -it citus_coordinateur psql -U postgres -d flowshop_db
```

### a. Créer les tables

```sql
CREATE TABLE clients(
    client_id        SERIAL,
    nom              TEXT NOT NULL,
    prenom           TEXT NOT NULL,
    pays             TEXT NOT NULL,
    date_inscription DATE DEFAULT current_date
);

CREATE TABLE produits(
    produit_id  SERIAL,
    nom_produit TEXT NOT NULL,
    categorie   TEXT NOT NULL,
    prix        DECIMAL(10,2) NOT NULL
);

CREATE TABLE commandes(
    commande_id   SERIAL,
    client_id     INT,
    date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut        TEXT DEFAULT 'validee'
);

CREATE TABLE details_commande(
    detail_id     SERIAL,
    commande_id   INT,
    client_id     INT,
    produit_id    INT,
    quantite      INT NOT NULL DEFAULT 1,
    prix_unitaire DECIMAL(10,2) NOT NULL
);
```

!!! note
    `details_commande` contient `client_id` pour permettre sa colocalisation avec `clients` et `commandes`.

### b. Distribuer les tables

```sql
-- Distribuer clients sur client_id
SELECT create_distributed_table('clients', 'client_id');

-- Répliquer produits sur tous les workers (table de référence)
SELECT create_reference_table('produits');

-- Distribuer commandes — même clé que clients → colocalisation automatique
SELECT create_distributed_table('commandes', 'client_id');

-- Distribuer details_commande — même clé → colocalisation complète
SELECT create_distributed_table('details_commande', 'client_id');
```

### c. Vérifier la distribution

```sql
SELECT logicalrelid, partmethod, colocationid FROM pg_dist_partition;
```

Résultat attendu — `clients`, `commandes` et `details_commande` ont le **même** `colocationid` :

```
   logicalrelid   | partmethod | colocationid
------------------+------------+--------------
 clients          | h          |            1
 produits         | n          |            2
 commandes        | h          |            1
 details_commande | h          |            1
```
