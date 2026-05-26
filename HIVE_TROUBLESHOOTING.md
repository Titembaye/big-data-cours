# Hive sur Docker - Problèmes rencontrés et solutions

Ce fichier documente les problèmes rencontrés lors de l'intégration de Hive
dans le cluster Hadoop, et comment ils ont été résolus.

---

## Comprendre l'architecture Hive (en bref)

Hive permet d'écrire des requêtes SQL sur des données stockées dans HDFS.
Il est composé de 3 parties :

```
Toi (beeline / DBeaver)
        |
        v
  HiveServer2          ← reçoit tes requêtes SQL (port 10000)
        |
        v
   Metastore           ← garde la liste des tables, colonnes, types... (port 9083)
        |
        v
  PostgreSQL           ← base de données où le metastore stocke ses infos
        +
     HDFS              ← là où les vraies données sont stockées
```

---

## Problème 1 : Mode d'exécution LLAP non supporté

### Ce que c'est
Hive peut exécuter les requêtes de 3 façons différentes :
- **mr** (MapReduce) : le plus simple, compatible partout
- **tez** : plus rapide que MapReduce, nécessite Tez installé
- **llap** : le plus rapide, mais nécessite des serveurs dédiés (LLAP daemons)

### L'erreur
HiveServer2 démarrait puis s'arrêtait immédiatement car le mode `llap`
était configuré mais aucun daemon LLAP n'existait dans le cluster.

### La configuration fautive (hive-site.xml)
```xml
<property>
  <name>hive.execution.mode</name>
  <value>llap</value>   <!-- PROBLÈME : nécessite des daemons LLAP -->
</property>
```

### La correction
Supprimer cette propriété et utiliser `mr` comme moteur d'exécution :
```xml
<property>
  <name>hive.execution.engine</name>
  <value>mr</value>   <!-- MapReduce : simple et compatible -->
</property>
```

---

## Problème 2 : Driver JDBC PostgreSQL manquant

### Ce que c'est
Le **metastore** de Hive doit se connecter à PostgreSQL pour stocker
ses métadonnées (liste des tables, schémas, etc.).
Pour se connecter à PostgreSQL depuis Java, il faut un fichier `.jar`
appelé **driver JDBC**. L'image Docker `apache/hive:4.0.0` ne l'inclut pas.

### L'erreur
```
Failed to load driver
Underlying cause: java.lang.ClassNotFoundException: org.postgresql.Driver
*** schemaTool failed ***
```

### La correction
Télécharger le driver et le monter dans le conteneur :

```bash
# Télécharger le driver
mkdir -p drivers
wget -O drivers/postgresql.jar https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
```

Dans `docker-compose.yml`, ajouter le volume pour `metastore` et `hiveserver2` :
```yaml
volumes:
  - ./drivers/postgresql.jar:/opt/hive/lib/postgresql.jar
```

---

## Problème 3 : PostgreSQL pas encore prêt au démarrage du metastore

### Ce que c'est
Docker démarre les conteneurs "en même temps". Le metastore essayait de
se connecter à PostgreSQL avant que PostgreSQL soit prêt à accepter
des connexions.

### L'erreur
```
Failed to get schema version.
Underlying cause: org.postgresql.util.PSQLException: The connection attempt failed.
```

### La correction
Ajouter un **healthcheck** sur PostgreSQL, et faire attendre le metastore
que PostgreSQL soit vraiment prêt (`condition: service_healthy`) :

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U hive -d metastore"]
    interval: 10s
    retries: 10

metastore:
  depends_on:
    postgres:
      condition: service_healthy  # attend que postgres soit prêt
```

---

## Problème 4 : Incompatibilité de version PostgreSQL

### Ce que c'est
Le dossier `data/postgres/` contenait des données initialisées avec
PostgreSQL 13, mais l'image utilisée était PostgreSQL 15. Les deux versions
sont incompatibles au niveau du stockage de données.

### L'erreur
```
FATAL: database files are incompatible with server
DETAIL: The data directory was initialized by PostgreSQL version 13,
which is not compatible with this version 15.
```

### La correction
Supprimer les anciennes données (safe ici car c'est une base fraîche) :
```bash
sudo rm -rf data/postgres
sudo docker-compose up -d
```

---

## Problème 5 : HiveServer2 boucle à l'infini (le vrai problème bloquant)

### Ce que c'est
Au démarrage, HiveServer2 essaie de synchroniser les **événements de
notification** avec le metastore. C'est un mécanisme qui permet à
HiveServer2 d'être notifié quand une table est créée ou modifiée.
Dans notre configuration simple, cette fonctionnalité échoue car
la table interne du metastore retourne une erreur.

HiveServer2 réessayait donc toutes les **60 secondes** indéfiniment,
sans jamais démarrer réellement.

### L'erreur (dans /tmp/hive/hive.log)
```
java.lang.RuntimeException: Error initializing notification event poll
Caused by: org.apache.thrift.TApplicationException:
  Internal error processing get_current_notificationEventId
```

> Pour voir ce log : `sudo docker exec hiveserver2 tail -200 /tmp/hive/hive.log`

### La correction
Désactiver ce polling dans `hive-site.xml` :
```xml
<property>
  <name>hive.notification.event.poll.interval</name>
  <value>-1</value>   <!-- -1 = désactivé -->
</property>
```

---

## Résumé des fichiers modifiés

### conf/hive-site.xml
- Supprimé `hive.execution.mode: llap`
- Changé le moteur en `mr` (MapReduce)
- Ajouté `hive.metastore.warehouse.dir: /user/hive/warehouse`
- Ajouté `hive.notification.event.poll.interval: -1` (correctif principal)

### docker-compose.yml
- Ajouté healthcheck sur `postgres`
- Ajouté healthcheck sur `metastore`
- Ajouté `condition: service_healthy` sur les dépendances
- Monté `drivers/postgresql.jar` dans metastore et hiveserver2

### drivers/postgresql.jar
- Fichier téléchargé manuellement (driver JDBC PostgreSQL 42.7.3)

---

## Tester que tout fonctionne

```bash
# Se connecter à Hive
sudo docker exec -it hiveserver2 beeline -u "jdbc:hive2://localhost:10000"

# Dans beeline, tester :
SHOW DATABASES;
CREATE DATABASE test;
USE test;
CREATE TABLE employes (id INT, nom STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',';
SHOW TABLES;
!quit
```

---

## Ports exposés

| Service     | Port  | Usage                        |
|-------------|-------|------------------------------|
| HiveServer2 | 10000 | Connexions SQL (beeline, JDBC) |
| HiveServer2 | 10002 | Interface Web HiveServer2    |
| Metastore   | 9083  | Communication interne Thrift |
