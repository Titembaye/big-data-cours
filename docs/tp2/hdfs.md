# Phase 1 — HDFS

## 1.1 Configuration de base

HDFS a besoin de deux fichiers de configuration principaux. Le premier, `core-site.xml`, indique à Hadoop l'adresse du NameNode — sans ça, Hadoop ne sait pas où il se trouve sur le réseau et refuse de démarrer.

Créer `conf/core-site.xml` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://namenode:8020</value>
  </property>
</configuration>
```

Le second fichier, `hdfs-site.xml`, configure le comportement de HDFS. Le paramètre `dfs.replication` indique combien de fois chaque bloc de données doit être répliqué sur les DataNodes. On le fixe à 1 pour commencer avec un seul DataNode, puis on l'ajustera.

Le paramètre `dfs.datanode.data.dir` indique au DataNode où stocker physiquement les blocs sur le disque. Sans ce paramètre, Hadoop utilise `/tmp/` qui est effacé à chaque redémarrage du conteneur.

Créer `conf/hdfs-site.xml` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/opt/hadoop/data/datanode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir.perm</name>
    <value>777</value>
  </property>
</configuration>
```

`dfs.datanode.data.dir.perm` évite une erreur de permissions lors du démarrage. Par défaut, Hadoop essaie de forcer ses propres permissions sur le dossier de données, ce qui échoue quand ce dossier est monté depuis la machine hôte via Docker.

---

## 1.2 Démarrer le NameNode

Le NameNode est le chef d'orchestre du cluster HDFS. Il ne stocke pas de données, mais il connaît la carte complète du système de fichiers : quels fichiers existent, en combien de blocs ils sont découpés, et sur quels DataNodes ces blocs se trouvent.

Créer `docker-compose.yml` :

```yaml
services:
  namenode:
    image: apache/hadoop:3.3.6
    hostname: namenode
    container_name: namenode
    environment:
      - ENSURE_NAMENODE_DIR=/tmp/hadoop-root/dfs/name
    ports:
      - "9870:9870"
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
    command: ["hdfs", "namenode"]
```

La variable `ENSURE_NAMENODE_DIR` demande à l'image Docker de formater automatiquement le système de fichiers HDFS au premier démarrage. Le port `9870` expose l'interface web du NameNode.

Démarrer le conteneur :

```bash
sudo docker-compose up -d
sudo docker logs -f namenode
```

Le NameNode est prêt quand les logs affichent :

```
NameNode RPC up at: namenode/172.x.x.x:8020
IPC Server listener on 8020: starting
```

L'interface web est accessible sur `http://localhost:9870`. On y voit l'état du cluster, la mémoire utilisée, et le nombre de DataNodes connectés — pour l'instant **Live Nodes: 0**.

---

## 1.3 Ajouter les DataNodes

Les DataNodes sont les nœuds de stockage. Chaque DataNode stocke des blocs de données et envoie régulièrement un signal au NameNode (heartbeat) pour indiquer qu'il est toujours en vie.

Préparer les dossiers de données persistants pour chaque DataNode :

```bash
mkdir data/datanode1 data/datanode2 data/datanode3 data/datanode4
chmod 777 data/datanode1 data/datanode2 data/datanode3 data/datanode4
```

L'image Docker fait tourner Hadoop avec un utilisateur interne `hadoop` (UID 1000). Le `chmod 777` règle les problèmes de permissions sur les montages bind Docker.

Modifier `docker-compose.yml` pour ajouter les quatre DataNodes :

```yaml
services:
  namenode:
    image: apache/hadoop:3.3.6
    hostname: namenode
    container_name: namenode
    environment:
      - ENSURE_NAMENODE_DIR=/tmp/hadoop-root/dfs/name
    ports:
      - "9870:9870"
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
    command: ["hdfs", "namenode"]

  datanode1:
    image: apache/hadoop:3.3.6
    hostname: datanode1
    container_name: datanode1
    depends_on:
      - namenode
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./data/datanode1:/opt/hadoop/data/datanode
    command: ["hdfs", "datanode"]

  datanode2:
    image: apache/hadoop:3.3.6
    hostname: datanode2
    container_name: datanode2
    depends_on:
      - namenode
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./data/datanode2:/opt/hadoop/data/datanode
    command: ["hdfs", "datanode"]

  datanode3:
    image: apache/hadoop:3.3.6
    hostname: datanode3
    container_name: datanode3
    depends_on:
      - namenode
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./data/datanode3:/opt/hadoop/data/datanode
    command: ["hdfs", "datanode"]

  datanode4:
    image: apache/hadoop:3.3.6
    hostname: datanode4
    container_name: datanode4
    depends_on:
      - namenode
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./data/datanode4:/opt/hadoop/data/datanode
    command: ["hdfs", "datanode"]
```

`depends_on: namenode` indique à Docker de démarrer le NameNode avant les DataNodes. Chaque DataNode a son propre dossier `data/datanodeX` monté au même chemin interne `/opt/hadoop/data/datanode`.

Relancer le cluster :

```bash
sudo docker-compose down
sudo docker-compose up -d
```

Sur `http://localhost:9870`, on voit maintenant **Live Nodes: 4**.

---

## 1.4 Erreur courante — clusterID incompatible

Si un DataNode refuse de démarrer avec l'erreur :

```
Incompatible clusterIDs in /opt/hadoop/data/datanode:
namenode clusterID = CID-xxx ; datanode clusterID = CID-yyy
```

Le NameNode a été recréé et a généré un nouvel identifiant de cluster, mais le DataNode a conservé l'ancien. Solution : vider les dossiers de données des DataNodes.

```bash
sudo docker-compose down
rm -rf data/datanode1/* data/datanode2/* data/datanode3/* data/datanode4/*
sudo docker-compose up -d
```

---

## 1.5 Premiers fichiers dans HDFS

Entrer dans le conteneur namenode :

```bash
sudo docker exec -it namenode bash
```

Créer un répertoire et y déposer un fichier :

```bash
hdfs dfs -mkdir -p /user/tp
echo "Bonjour Hadoop, ceci est mon premier fichier HDFS !" > /tmp/test.txt
hdfs dfs -put /tmp/test.txt /user/tp/
hdfs dfs -cat /user/tp/test.txt
```

---

## 1.6 Vérifier le stockage physique des blocs

HDFS découpe chaque fichier en blocs (128 MB par défaut) et les distribue sur les DataNodes. Depuis la machine hôte, on peut voir le bloc physique :

```bash
ls data/datanode1/current/BP-*/current/finalized/subdir0/subdir0/
```

On trouve deux fichiers :

- `blk_XXXXXXXXXX` — le bloc de données brut
- `blk_XXXXXXXXXX_XXXX.meta` — le checksum pour détecter toute corruption

```bash
cat data/datanode1/current/BP-*/current/finalized/subdir0/subdir0/blk_*[^meta]
```

Le contenu de `test.txt` est lisible directement dans le bloc. Le NameNode connaît la carte, les DataNodes stockent les blocs physiques.

---

## État du cluster à l'issue de la Phase 1

```
NameNode   — port 9870  — carte du système de fichiers
DataNode1  — stockage physique des blocs
DataNode2  — stockage physique des blocs
DataNode3  — stockage physique des blocs
DataNode4  — stockage physique des blocs
```
