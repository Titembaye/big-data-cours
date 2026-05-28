# Phase 4 — MapReduce avec des scripts Python

WordCount c'est bien pour comprendre le principe, mais en pratique on écrit ses propres mapper et reducer. Hadoop Streaming permet de le faire dans n'importe quel langage — ici Python.

L'objectif : calculer le chiffre d'affaires total par produit à partir de 500 000 transactions.

---

## 4.1 Récupérer les données

Télécharger le fichier de transactions et le placer dans le dossier `data/` du projet :

> **[Télécharger transactions.csv](#)** ← lien à mettre à jour

Le fichier contient 500 000 lignes au format :

```
transaction_id,produit,region,montant,date
1,telephone,Lome,125430.50,2026-01-15
2,ordinateur,Kara,89200.00,2026-02-03
...
```

---

## 4.2 Charger dans HDFS — terminal namenode

Copier le CSV dans le conteneur puis dans HDFS :

```bash
sudo docker cp data/transactions.csv namenode:/tmp/
sudo docker exec -it namenode bash
```

```bash
hdfs dfs -mkdir -p /user/tp/transactions
hdfs dfs -put /tmp/transactions.csv /user/tp/transactions/
hdfs dfs -ls /user/tp/transactions/
```

---

## 4.3 Copier les scripts dans le conteneur

Les scripts doivent être accessibles depuis le namenode au moment du lancement du job. Depuis votre machine :

```bash
sudo docker cp scripts/mapper.py namenode:/tmp/
sudo docker cp scripts/reducer.py namenode:/tmp/
```

Rendre les scripts exécutables (depuis le conteneur) :

```bash
chmod +x /tmp/mapper.py /tmp/reducer.py
```

---

## 4.4 Lancer le job avec Hadoop Streaming

Hadoop Streaming est inclus dans l'image. Depuis le conteneur namenode :

```bash
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -files /tmp/mapper.py,/tmp/reducer.py \
  -mapper mapper.py \
  -reducer reducer.py \
  -input /user/tp/transactions/ \
  -output /user/tp/output_transactions
```

Le job distribue le fichier sur les DataNodes. Chaque NodeManager exécute une instance du mapper sur sa portion de données. Le reducer agrège ensuite les résultats par produit.

---

## 4.5 Lire les résultats

```bash
hdfs dfs -cat /user/tp/output_transactions/part-00000
```

Résultat attendu — chiffre d'affaires total par produit :

```
batterie          1823450234.12
camera            1821903847.50
climatiseur       1819234012.33
imprimante        1824501923.88
machine_a_laver   1820394857.11
ordinateur        1822039485.22
refrigerateur     1819283746.99
tablette          1821039485.33
telephone         1823049285.44
television        1820394857.55
```

Pour relancer le job, supprimer d'abord le dossier de sortie :

```bash
hdfs dfs -rm -r /user/tp/output_transactions
```
