# Phase 4 — MapReduce avec des scripts Python

WordCount c'est bien pour comprendre le principe, mais en pratique on écrit ses propres mapper et reducer. Hadoop Streaming permet de le faire dans n'importe quel langage — ici Python.

L'objectif : calculer le chiffre d'affaires total par produit à partir de 500 000 transactions.

---

## 4.1 Récupérer les données

Télécharger le fichier de transactions et le placer dans le dossier `data/` du projet :

> **[Télécharger transactions.csv](https://drive.google.com/file/d/1TE-vGFsSrXRposB7YDpz8g9lzoeKh_zz/view?usp=sharing)**

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

## 4.3 Créer les scripts

Dans le dossier `scripts/`, créer deux fichiers.

**`scripts/mapper.py`** — lit le CSV ligne par ligne et émet une paire `(produit, montant)` pour chaque transaction :

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

for ligne in sys.stdin:
    ligne = ligne.strip()

    # Ignorer l'en-tête
    if ligne.startswith('transaction_id'):
        continue

    champs = ligne.split(',')

    if len(champs) != 5:
        continue

    produit = champs[1]
    montant = champs[3]

    print('{}\t{}'.format(produit, montant))
```

**`scripts/reducer.py`** — reçoit les paires triées par clé et additionne les montants par produit :

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

produit_courant = None
total = 0

for ligne in sys.stdin:
    ligne = ligne.strip()
    champs = ligne.split('\t')

    if len(champs) != 2:
        continue

    produit = champs[0]

    try:
        montant = float(champs[1])
    except ValueError:
        continue

    # Nouveau produit — afficher le résultat du précédent
    if produit_courant and produit != produit_courant:
        print('{}\t{:.2f}'.format(produit_courant, total))
        total = 0

    produit_courant = produit
    total += montant

# Dernier produit
if produit_courant:
    print('{}\t{:.2f}'.format(produit_courant, total))
```

Une fois les fichiers créés, les copier dans le conteneur et les rendre exécutables :

```bash
sudo docker cp scripts/mapper.py namenode:/tmp/
sudo docker cp scripts/reducer.py namenode:/tmp/
```

```bash
sudo docker exec -it namenode bash
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
