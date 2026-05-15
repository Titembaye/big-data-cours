# TP : Distribution des données avec PostgreSQL

## Introduction

Dans les parties précédentes, nous avons amélioré progressivement l'architecture de ShopFlow. Le partitionnement (Partie 2) a réduit le périmètre de lecture en segmentant les tables localement. FDW (Partie 3) a permis de déplacer physiquement des partitions sur des serveurs distants. Mais dans les deux cas, un point faible demeure : le serveur central supporte seul la charge de coordination et d'exécution des requêtes analytiques.

Citus répond à cette limite. Il transforme PostgreSQL en une base de données véritablement distribuée, où les requêtes sont découpées et exécutées en parallèle sur plusieurs machines — les workers. Plus on ajoute de workers, plus la capacité de traitement augmente. C'est de la scalabilité horizontale.

---

## A. Docker

Jusqu'ici, nous avons travaillé directement sur notre machine : PostgreSQL était installé localement, les instances tournaient sur différents ports. Pour la partie Citus, nous allons utiliser Docker.

### Qu'est-ce qu'un conteneur Docker ?

Un conteneur est une mini-machine isolée qui tourne à l'intérieur de votre machine. Il a son propre système de fichiers, ses propres processus, son propre réseau. Il est léger, reproductible, et s'arrête proprement sans laisser de traces sur votre système.

Concrètement, au lieu d'installer Citus directement sur votre ordinateur — ce qui nécessiterait de modifier la configuration système de votre machine — on va lancer des conteneurs qui contiennent déjà PostgreSQL + Citus préinstallés et préconfigurés.

### Docker Compose

Docker Compose est un outil qui permet de décrire et de gérer plusieurs conteneurs en même temps à partir d'un seul fichier de configuration (`docker-compose.yml`). Ce fichier permet de monter un cluster de 3 conteneurs en une seule commande.

### L'architecture des conteneurs

On va simuler un cluster Citus avec 3 conteneurs sur la même machine, chacun écoutant sur un port différent :

- `citus_coordinateur` — port 5432 : reçoit toutes les requêtes SQL, orchestre le travail
- `citus_worker1` — port 5433 : stocke et traite une partie des données
- `citus_worker2` — port 5434 : stocke et traite l'autre partie des données

Les trois conteneurs communiquent entre eux via un réseau interne Docker. Ils se reconnaissent par leur nom (`citus_worker1`, `citus_worker2`) — Docker gère cela automatiquement.

---

## B. Citus

### Principe de fonctionnement

Quand on déclare une table comme distribuée dans Citus, il la découpe en fragments appelés **shards**. Par défaut, Citus crée 32 shards par table et les répartit équitablement sur les workers disponibles.

La **clé de distribution** (distribution column) détermine dans quel shard va chaque ligne. C'est le choix le plus important de toute la configuration : une mauvaise clé peut créer des déséquilibres ou forcer des jointures coûteuses entre workers.

### Types de tables dans Citus

Citus distingue deux catégories de tables selon leur rôle :

- **Table distribuée** (distributed table) : fragmentée sur les workers selon la clé de distribution. Adaptée aux grandes tables (`clients`, `commandes`, `details_commande`).
- **Table de référence** (reference table) : répliquée intégralement sur tous les workers. Adaptée aux petites tables peu modifiées (`produits`, catégories). Cela évite d'envoyer ces données sur le réseau à chaque jointure.

### La colocalisation : éviter les jointures distribuées

Quand deux tables distribuées ont la même clé de distribution, Citus place leurs shards correspondants sur le même worker. On dit qu'elles sont **colocalisées**. Ainsi, une jointure entre ces deux tables s'exécute localement sur chaque worker sans transfert de données sur le réseau.

*Dans notre TP, `clients`, `commandes` et `details_commande` seront toutes trois distribuées sur `client_id`. Un client, ses commandes et les détails de ces commandes seront donc toujours sur le même worker.*

> **Note sur le schéma :** Pour que `details_commande` puisse être distribuée sur `client_id`, elle doit contenir cette colonne. C'est pourquoi on l'ajoute au schéma ci-dessous — elle ne crée pas de redondance fonctionnelle, elle est la condition technique de la colocalisation.

---

# Partie 4 — Distribution réelle avec Citus

Nous repartons d'une base propre — sans le travail FDW. L'objectif est de reconstruire le schéma de ShopFlow directement dans Citus et d'observer comment il distribue et parallélise le travail.

---

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

> **`POSTGRES_HOST_AUTH_METHOD: trust`** autorise les connexions entre nœuds sans mot de passe sur le réseau Docker interne. Sans cette option, le coordinateur ne peut pas interroger les workers et toute requête distribuée échoue avec `fe_sendauth: no password supplied`. Cette configuration est acceptable dans un réseau Docker isolé ; en production, on utiliserait `scram-sha-256` avec un fichier `.pgpass`.

---

## Étape 2 — Démarrer le cluster progressivement

On démarre les conteneurs un par un pour bien comprendre chaque rôle avant d'ajouter le suivant.

### a. Démarrer uniquement le coordinateur

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

```bash
sudo docker-compose up -d worker1
sudo docker ps
sudo docker exec -it citus_coordinateur psql -U postgres -d flowshop_db
```

```sql
SELECT citus_add_node('citus_worker1', 5432);
SELECT * FROM citus_get_active_worker_nodes();
```

Vous devez voir une ligne avec `citus_worker1`. Quittez avec `\q`.

### c. Ajouter le second worker

```bash
sudo docker-compose up -d worker2
sudo docker ps
sudo docker exec -it citus_coordinateur psql -U postgres -d flowshop_db
```

```sql
SELECT citus_add_node('citus_worker2', 5432);
SELECT * FROM citus_get_active_worker_nodes();
```

Vous devez voir deux lignes : `citus_worker1` et `citus_worker2`. Le cluster est prêt.

---

## Étape 3 — Créer les tables

On crée les tables une par une sur le coordinateur. Citus les propage automatiquement sur les workers au moment de la distribution.

```bash
sudo docker exec -it citus_coordinateur psql -U postgres -d flowshop_db
```

### a. Table clients

```sql
CREATE TABLE clients(
    client_id        SERIAL,
    nom              TEXT NOT NULL,
    prenom           TEXT NOT NULL,
    pays             TEXT NOT NULL,
    date_inscription DATE DEFAULT current_date
);
```

### b. Table produits

```sql
CREATE TABLE produits(
    produit_id  SERIAL,
    nom_produit TEXT NOT NULL,
    categorie   TEXT NOT NULL,
    prix        DECIMAL(10,2) NOT NULL
);
```

### c. Table commandes

`commandes` sera distribuée sur `client_id` — la même clé que `clients`. Cela garantit que les commandes d'un client seront sur le même worker que ce client (colocalisation).

```sql
CREATE TABLE commandes(
    commande_id   SERIAL,
    client_id     INT,
    date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut        TEXT DEFAULT 'validee'
);
```

### d. Table details_commande

`details_commande` sera distribuée sur `client_id` pour être colocalisée avec `clients` et `commandes`. On ajoute donc `client_id` comme colonne de distribution — elle sera renseignée lors de la génération des données.

```sql
CREATE TABLE details_commande(
    detail_id     SERIAL,
    commande_id   INT,
    client_id     INT,
    produit_id    INT,
    quantite      INT NOT NULL DEFAULT 1,
    prix_unitaire DECIMAL(10,2) NOT NULL
);
```

Vérifiez que les 4 tables sont créées :

```sql
\dt
```

---

## Étape 4 — Distribuer les tables sur le cluster

La création des tables ne suffit pas ; elles existent pour l'instant uniquement sur le coordinateur comme des tables ordinaires. On doit maintenant indiquer à Citus comment les distribuer.

### a. Distribuer clients

```sql
SELECT create_distributed_table('clients', 'client_id');
```

### b. Répliquer produits sur tous les workers

```sql
SELECT create_reference_table('produits');
```

### c. Distribuer commandes

On utilise `client_id` comme clé, même choix que pour les clients. Citus détecte automatiquement la colocalisation.

```sql
SELECT create_distributed_table('commandes', 'client_id');
```

### d. Distribuer details_commande

On distribue sur `client_id` — même clé que `clients` et `commandes` — pour garantir la colocalisation complète des trois tables.

```sql
SELECT create_distributed_table('details_commande', 'client_id');
```

### e. Vérifier la distribution

```sql
SELECT logicalrelid, partmethod, colocationid FROM pg_dist_partition;
```

La colonne `colocationid` montre quelles tables partagent la même stratégie de placement. `clients`, `commandes` et `details_commande` doivent avoir le **même** `colocationid`.

Résultat attendu :

```
   logicalrelid   | partmethod | colocationid
------------------+------------+--------------
 clients          | h          |            1
 produits         | n          |            2
 commandes        | h          |            1
 details_commande | h          |            1
```

---

## Étape 5 — Charger les données

### a. Copier les fichiers CSV dans le conteneur

Depuis un terminal sur votre machine (pas dans psql) :

```bash
sudo docker cp /tmp/produits.csv          citus_coordinateur:/tmp/
sudo docker cp /tmp/clients.csv           citus_coordinateur:/tmp/
sudo docker cp /tmp/commandes.csv         citus_coordinateur:/tmp/
sudo docker cp /tmp/details_commande.csv  citus_coordinateur:/tmp/
```

### b. Charger les données

```bash
sudo docker exec -it citus_coordinateur psql -U postgres -d flowshop_db
```

```sql
COPY produits(produit_id, nom_produit, categorie, prix)
FROM '/tmp/produits.csv' DELIMITER ',' CSV HEADER;

COPY clients(client_id, nom, prenom, pays, date_inscription)
FROM '/tmp/clients.csv' DELIMITER ',' CSV HEADER;

COPY commandes(commande_id, client_id, date_commande, statut)
FROM '/tmp/commandes.csv' DELIMITER ',' CSV HEADER;

COPY details_commande(detail_id, commande_id, client_id, produit_id, quantite, prix_unitaire)
FROM '/tmp/details_commande.csv' DELIMITER ',' CSV HEADER;
```

> La colonne `client_id` est maintenant présente dans `details_commande.csv`. Elle a été ajoutée lors de la génération des données pour permettre la colocalisation.

### c. Vérifier le chargement

```sql
SELECT
    (SELECT count(*) FROM clients)          AS nb_clients,
    (SELECT count(*) FROM produits)         AS nb_produits,
    (SELECT count(*) FROM commandes)        AS nb_commandes,
    (SELECT count(*) FROM details_commande) AS nb_details;
```

---

## Étape 6 — Observer la distribution des shards

### a. Répartition des shards par worker

```sql
SELECT
    nodename,
    count(*) AS nb_shards
FROM pg_dist_shard_placement psp
JOIN pg_dist_shard ps ON psp.shardid = ps.shardid
WHERE ps.logicalrelid = 'clients'::regclass
GROUP BY nodename;
```

Avec 32 shards et 2 workers, on attend 16 shards par worker.

### b. Vérifier les shards physiques sur un worker

```bash
sudo docker exec -it citus_worker1 psql -U postgres -d flowshop_db
\dt
```

---

## Étape 7 — Comparer les performances : impact de la colocalisation

Cette étape illustre concrètement pourquoi le choix de la clé de distribution est critique. On va comparer deux versions de la même requête analytique : l'une sans colocalisation complète, l'autre avec.

### a. Version sans colocalisation (référence)

Cette version correspond à une configuration où `details_commande` aurait été distribuée sur `commande_id` — une clé différente de `commandes` (distribuée sur `client_id`). Pour reproduire ce comportement, on active le repartitioning forcé :

```sql
SET citus.enable_repartition_joins = on;

EXPLAIN ANALYZE
SELECT
    cl.pays,
    SUM(d.quantite * d.prix_unitaire) AS chiffre_affaires
FROM clients cl
JOIN commandes c        ON cl.client_id  = c.client_id
JOIN details_commande d ON c.commande_id = d.commande_id
GROUP BY cl.pays
ORDER BY chiffre_affaires DESC;
```

Plan obtenu (résultats indicatifs) :

```
Sort  (actual time=35347..35347 rows=5)
  → HashAggregate
      → Custom Scan (Citus Adaptive)
            Task Count: 8
            → MapMergeJob
                 Map Task Count: 32 / Merge Task Count: 8
            → MapMergeJob
                 Map Task Count: 32 / Merge Task Count: 8
Execution Time: ~35 000 ms
```

**Ce que cela signifie :** `Task Count: 8` avec deux `MapMergeJob` indique que Citus a dû redistribuer physiquement les données entre workers deux fois (une fois par jointure non colocalisée). Chaque redistribution génère du trafic réseau inter-workers — même sur un réseau Docker local, ce shuffle est coûteux.

### b. Version avec colocalisation complète

Avec `details_commande` distribuée sur `client_id`, la jointure doit explicitement inclure la clé de distribution pour que Citus détecte la colocalisation :

```sql
EXPLAIN ANALYZE
SELECT
    cl.pays,
    SUM(d.quantite * d.prix_unitaire) AS chiffre_affaires
FROM clients cl
JOIN commandes c        ON cl.client_id  = c.client_id
JOIN details_commande d ON c.commande_id = d.commande_id
                       AND c.client_id   = d.client_id   -- condition de colocalisation
GROUP BY cl.pays
ORDER BY chiffre_affaires DESC;
```

Plan obtenu :

```
Sort  (actual time=3049..3049 rows=5)
  → HashAggregate
      → Custom Scan (Citus Adaptive)
            Task Count: 32
            Tasks Shown: One of 32
            → Task
                 Node: host=citus_worker2
                 → Hash Join
                      Hash Cond: (d.client_id = c.client_id) AND (d.commande_id = c.commande_id)
                      → Seq Scan on commandes_102052
                      → Seq Scan on details_commande_102116
Execution Time: ~3 050 ms
```

**Ce que cela signifie :** `Task Count: 32` sans aucun `MapMergeJob`. Citus a créé 32 tâches indépendantes — une par shard — chacune exécutée localement sur son worker. Les `Seq Scan` portent sur des shards du même worker (`commandes_102052` et `details_commande_102116`). Le coordinateur ne reçoit que les agrégats partiels (57 bytes au total).

### c. Tableau comparatif

| | Sans colocalisation | Avec colocalisation |
|---|---|---|
| **Temps d'exécution** | ~35 000 ms | **~3 050 ms** |
| **Task Count** | 8 | **32** |
| **MapMergeJob** | 2 (shuffle réseau) | **aucun** |
| **Traitement** | Redistribution inter-workers | **Local sur chaque worker** |
| **Données reçues par le coordinateur** | — | **57 bytes** |

Le facteur d'amélioration est d'environ **×10**, uniquement grâce à la co-localisation.

### d. Leçon à retenir

La colocalisation dans Citus repose sur deux conditions cumulatives :

**Condition structurelle :** les tables doivent être distribuées sur la même colonne sémantique (`client_id`), ce qui leur attribue le même `colocationid` dans `pg_dist_partition`.

**Condition déclarative :** la requête doit inclure explicitement la condition de jointure sur cette colonne (`c.client_id = d.client_id`). Sans elle, Citus ne peut pas détecter la colocalisation et recourt au repartitioning même si les tables sont correctement configurées.

---

## Étape 8 — Arrêter le cluster

### a. Arrêter et supprimer les conteneurs

```bash
sudo docker-compose down
```

Cette commande arrête les 3 conteneurs et supprime le réseau Docker créé. Les données sont perdues.

### b. Redémarrer PostgreSQL local

Le PostgreSQL local avait été arrêté pour libérer le port 5432. On le redémarre :

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```