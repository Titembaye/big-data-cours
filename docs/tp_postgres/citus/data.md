# Données — Chargement et vérification

## Étape 4 — Récupérer les fichiers CSV

Les données ShopFlow sont disponibles en téléchargement :

> **[Télécharger les données ShopFlow](#)** ← lien à mettre à jour

Téléchargez et placez les fichiers dans `/tmp/` :

```
/tmp/clients.csv           # 800 000 clients
/tmp/produits.csv          # 100 produits
/tmp/commandes.csv         # 1 300 000 commandes
/tmp/details_commande.csv  # 3 250 000 lignes
```

---

## Étape 5 — Charger les données

### a. Copier les fichiers CSV dans le conteneur

Depuis votre terminal :

```bash
sudo docker cp /tmp/produits.csv         citus_coordinateur:/tmp/
sudo docker cp /tmp/clients.csv          citus_coordinateur:/tmp/
sudo docker cp /tmp/commandes.csv        citus_coordinateur:/tmp/
sudo docker cp /tmp/details_commande.csv citus_coordinateur:/tmp/
```

### b. Charger via COPY

Sur le coordinateur :

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

### c. Vérifier le chargement

```sql
SELECT
    (SELECT count(*) FROM clients)          AS nb_clients,
    (SELECT count(*) FROM produits)         AS nb_produits,
    (SELECT count(*) FROM commandes)        AS nb_commandes,
    (SELECT count(*) FROM details_commande) AS nb_details;
```
