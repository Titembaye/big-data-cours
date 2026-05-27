# Analyse — Shards et performances

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

Avec 32 shards et 2 workers, on attend **16 shards par worker**.

### b. Vérifier les shards physiques sur un worker

```bash
sudo docker exec -it citus_worker1 psql -U postgres -d flowshop_db
\dt
```

---

## Étape 7 — Impact de la colocalisation sur les performances

Cette étape illustre pourquoi le choix de la clé de distribution est critique.

### a. Version sans colocalisation (référence)

Cette requête simule une configuration où `details_commande` aurait été distribuée sur `commande_id` — une clé différente de `commandes` :

```sql
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

!!! tip
    Si vous obtenez une alerte demandant d'activer le repartitioning forcé :
    ```sql
    SET citus.enable_repartition_joins = on;
    ```
    puis relancez l'`EXPLAIN ANALYZE`.

### b. Version avec colocalisation complète

Avec `details_commande` distribuée sur `client_id`, la jointure doit inclure explicitement la clé de distribution :

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

### Pourquoi cette différence ?

La colocalisation dans Citus repose sur deux conditions cumulatives :

- **Condition structurelle** : les tables doivent être distribuées sur la même colonne (`client_id`), ce qui leur attribue le même `colocationid` dans `pg_dist_partition`.
- **Condition déclarative** : la requête doit inclure explicitement la jointure sur cette colonne (`c.client_id = d.client_id`). Sans elle, Citus recourt au repartitioning même si les tables sont correctement configurées.
