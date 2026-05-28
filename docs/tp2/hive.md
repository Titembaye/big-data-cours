# Phase 5 — Hive

Hive permet d'interroger des données stockées dans HDFS avec du SQL standard. Sous le capot, chaque requête est traduite en un ou plusieurs jobs MapReduce.

L'architecture repose sur trois composants supplémentaires :

```
Toi (beeline)
      |
      v
 HiveServer2     ← reçoit les requêtes SQL (port 10000)
      |
      v
  Metastore      ← stocke les métadonnées : tables, colonnes, types (port 9083)
      |
      v
 PostgreSQL      ← base de données du metastore
      +
   HDFS          ← là où les données sont réellement stockées
```

---

## 5.1 Télécharger le driver PostgreSQL

Le metastore se connecte à PostgreSQL via JDBC. L'image Hive n'inclut pas ce driver — il faut le télécharger manuellement dans `drivers/` :

```bash
mkdir -p drivers
wget -O drivers/postgresql.jar https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
```

---

## 5.2 Mettre à jour docker-compose.yml

Ajouter les trois nouveaux services à la suite des services existants :

```yaml
  postgres:
    image: postgres:15
    container_name: postgres
    environment:
      - POSTGRES_DB=metastore
      - POSTGRES_USER=hive
      - POSTGRES_PASSWORD=hive123
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hive -d metastore"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  metastore:
    image: apache/hive:4.0.0
    container_name: metastore
    depends_on:
      postgres:
        condition: service_healthy
      namenode:
        condition: service_started
    environment:
      - SERVICE_NAME=metastore
      - DB_DRIVER=postgres
      - SERVICE_OPTS=-Djavax.jdo.option.ConnectionDriverName=org.postgresql.Driver -Djavax.jdo.option.ConnectionURL=jdbc:postgresql://postgres:5432/metastore -Djavax.jdo.option.ConnectionUserName=hive -Djavax.jdo.option.ConnectionPassword=hive123
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/hive-site.xml:/opt/hive/conf/hive-site.xml
      - ./drivers/postgresql.jar:/opt/hive/lib/postgresql.jar
    ports:
      - "9083:9083"
    healthcheck:
      test: ["CMD", "bash", "-c", "echo > /dev/tcp/localhost/9083"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 60s

  hiveserver2:
    image: apache/hive:4.0.0
    container_name: hiveserver2
    depends_on:
      metastore:
        condition: service_healthy
    environment:
      - SERVICE_NAME=hiveserver2
      - IS_RESUME=true
      - SERVICE_OPTS=-Dhive.metastore.uris=thrift://metastore:9083
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
      - ./conf/hive-site.xml:/opt/hive/conf/hive-site.xml
      - ./drivers/postgresql.jar:/opt/hive/lib/postgresql.jar
    ports:
      - "10000:10000"
      - "10002:10002"
```

Le `healthcheck` sur postgres et metastore est important : sans lui, le metastore essaie de se connecter à PostgreSQL avant qu'il soit prêt et échoue au démarrage.

---

## 5.3 Préparer le répertoire HDFS pour Hive

Hive stocke les données des tables dans `/user/hive/warehouse` sur HDFS. Créer ce répertoire depuis le namenode :

```bash
sudo docker exec -it namenode bash
hdfs dfs -mkdir -p /user/hive/warehouse
hdfs dfs -chmod 777 /user/hive/warehouse
```

---

## 5.4 Démarrer les nouveaux services

```bash
sudo docker-compose up -d postgres metastore hiveserver2
sudo docker ps
```

Le démarrage prend environ 1 à 2 minutes — le metastore initialise le schéma PostgreSQL au premier lancement. Attendre que les 9 conteneurs soient tous en état `Up`.

---

## 5.5 Se connecter à Hive via beeline

Beeline est le client SQL de Hive, inclus dans le conteneur hiveserver2 :

```bash
sudo docker exec -it hiveserver2 beeline -u "jdbc:hive2://localhost:10000"
```

Vérifier que la connexion fonctionne :

```sql
SHOW DATABASES;
```

---

## 5.6 Créer une table et interroger les transactions

Créer une base et une table externe pointant vers les données déjà dans HDFS :

```sql
CREATE DATABASE tp;
USE tp;

CREATE EXTERNAL TABLE transactions (
    transaction_id INT,
    produit        STRING,
    region         STRING,
    montant        DOUBLE,
    date_tr        STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/tp/transactions/'
TBLPROPERTIES ("skip.header.line.count"="1");
```

Vérifier le chargement :

```sql
SELECT count(*) FROM transactions;
```

Calculer le chiffre d'affaires par produit :

```sql
SELECT produit, ROUND(SUM(montant), 2) AS chiffre_affaires
FROM transactions
GROUP BY produit
ORDER BY chiffre_affaires DESC;
```

Chiffre d'affaires par région :

```sql
SELECT region, ROUND(SUM(montant), 2) AS chiffre_affaires
FROM transactions
GROUP BY region
ORDER BY chiffre_affaires DESC;
```

Pour quitter beeline :

```sql
!quit
```

---

## 5.7 Interfaces web disponibles

| Service | URL | Rôle |
|---------|-----|------|
| HiveServer2 | http://localhost:10002 | Suivi des requêtes en cours |

---

## Problèmes courants

Voir [HIVE_TROUBLESHOOTING.md](https://github.com/Titembaye/big-data-cours/blob/hadoop-tp2/HIVE_TROUBLESHOOTING.md) pour les erreurs rencontrées lors de la mise en place (driver JDBC, timing PostgreSQL, boucle HiveServer2).
