# Phase 3 — YARN

YARN (Yet Another Resource Negotiator) est le gestionnaire de ressources du cluster. Il reçoit les demandes de jobs, alloue les ressources disponibles sur les nœuds, et surveille l'exécution. Sans YARN, MapReduce tourne en mode local sur un seul nœud.

YARN est composé de deux types de processus :

- **ResourceManager** — un seul par cluster, chef d'orchestre qui alloue les ressources
- **NodeManager** — un par nœud de données, exécute concrètement les tâches et rend compte au ResourceManager

---

## 3.1 Configuration YARN

Créer `conf/yarn-site.xml` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>yarn.resourcemanager.hostname</name>
    <value>resourcemanager</value>
  </property>
  <property>
    <name>yarn.resourcemanager.address</name>
    <value>resourcemanager:8032</value>
  </property>
  <property>
    <name>yarn.resourcemanager.scheduler.address</name>
    <value>resourcemanager:8030</value>
  </property>
  <property>
    <name>yarn.resourcemanager.resource-tracker.address</name>
    <value>resourcemanager:8031</value>
  </property>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
  <property>
    <name>yarn.nodemanager.aux-services.mapreduce_shuffle.class</name>
    <value>org.apache.hadoop.mapred.ShuffleHandler</value>
  </property>
  <property>
    <name>yarn.nodemanager.resource.memory-mb</name>
    <value>1024</value>
  </property>
  <property>
    <name>yarn.nodemanager.resource.cpu-vcores</name>
    <value>1</value>
  </property>
  <property>
    <name>yarn.scheduler.minimum-allocation-mb</name>
    <value>512</value>
  </property>
  <property>
    <name>yarn.scheduler.maximum-allocation-mb</name>
    <value>1024</value>
  </property>
</configuration>
```

- `yarn.resourcemanager.hostname` — nom du conteneur ResourceManager, utilisé par tous les nœuds pour le localiser sur le réseau Docker
- `yarn.resourcemanager.resource-tracker.address` — port utilisé par les NodeManagers pour s'enregistrer (8031). Sans ce paramètre explicite, les NodeManagers ne trouvent pas le ResourceManager
- `yarn.nodemanager.aux-services=mapreduce_shuffle` — active le service shuffle qui transfère les données entre les tâches Map et Reduce
- `yarn.nodemanager.resource.memory-mb=1024` — chaque NodeManager expose 1 GB de RAM au cluster
- `yarn.scheduler.minimum-allocation-mb=512` — un conteneur YARN demande au minimum 512 MB

---

## 3.2 Mettre à jour docker-compose.yml

On ajoute le ResourceManager et deux NodeManagers. On garde 2 DataNodes et 2 NodeManagers pour rester dans les limites d'une machine avec 8 GB de RAM.

Les quatre fichiers de configuration doivent être montés dans tous les conteneurs.

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
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
    command: ["hdfs", "namenode"]

  resourcemanager:
    image: apache/hadoop:3.3.6
    hostname: resourcemanager
    container_name: resourcemanager
    depends_on:
      - namenode
    ports:
      - "8088:8088"
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
    command: ["yarn", "resourcemanager"]

  datanode1:
    image: apache/hadoop:3.3.6
    hostname: datanode1
    container_name: datanode1
    depends_on:
      - namenode
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
      - ./data/datanode1:/opt/hadoop/data/datanode
    command: ["hdfs", "datanode"]

  nodemanager1:
    image: apache/hadoop:3.3.6
    hostname: nodemanager1
    container_name: nodemanager1
    depends_on:
      - resourcemanager
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
    command: ["yarn", "nodemanager"]

  datanode2:
    image: apache/hadoop:3.3.6
    hostname: datanode2
    container_name: datanode2
    depends_on:
      - namenode
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
      - ./data/datanode2:/opt/hadoop/data/datanode
    command: ["hdfs", "datanode"]

  nodemanager2:
    image: apache/hadoop:3.3.6
    hostname: nodemanager2
    container_name: nodemanager2
    depends_on:
      - resourcemanager
    volumes:
      - ./conf/core-site.xml:/opt/hadoop/etc/hadoop/core-site.xml
      - ./conf/hdfs-site.xml:/opt/hadoop/etc/hadoop/hdfs-site.xml
      - ./conf/mapred-site.xml:/opt/hadoop/etc/hadoop/mapred-site.xml
      - ./conf/yarn-site.xml:/opt/hadoop/etc/hadoop/yarn-site.xml
    command: ["yarn", "nodemanager"]
```

Relancer le cluster :

```bash
sudo docker-compose down
sudo docker-compose up -d
sudo docker ps
```

On doit voir 6 conteneurs actifs : namenode, resourcemanager, datanode1, datanode2, nodemanager1, nodemanager2.

---


## 3.3 Vérifier le cluster YARN

L'interface web YARN est accessible sur `http://localhost:8088` :

- `Active Nodes` — nombre de NodeManagers connectés
- `Total Resources` — capacité totale en mémoire et CPU
- `Applications` — historique et état des jobs soumis

---

## 3.4 Mise à jour de hdfs-site.xml — taille des blocs

Avant de tester la distribution, il faut modifier `conf/hdfs-site.xml` pour réduire la taille des blocs HDFS.

En production, la valeur par défaut est **128 MB** par bloc. Avec cette valeur, il faudrait un fichier de plus de 1,9 GB pour observer une vraie distribution en 15 blocs.

Pour observer la distribution, on la ramène à **1 MB** pour pouvoir travailler avec des fichiers légers :

```xml
<property>
    <name>dfs.blocksize</name>
    <value>1048576</value>  <!-- 1 MB = 1024 × 1024 octets (défaut prod : 134217728 = 128 MB) -->
</property>
```

Après cette modification, relancer le cluster :

```bash
sudo docker-compose down
sudo docker-compose up -d
```

!!! note
    Ce choix est purement pédagogique. L'objectif est de voir Hadoop découper un fichier en plusieurs blocs et distribuer les tâches Map sur les NodeManagers. Avec des blocs de 1 MB, un fichier de 15 MB suffit pour générer 15 blocs et 15 tâches Map parallèles.

---

## 3.5 Tester la distribution réelle avec un grand fichier

### a. Générer le fichier

Ouvrez un terminal sur **votre machine** (pas dans un conteneur) pour créer un fichier `test_file.txt` dans `/tmp/` de votre système local :

```bash
python -c "
import random
words = ['hadoop', 'hdfs', 'mapreduce', 'yarn', 'datanode', 'namenode', 'cluster', 'distribue', 'bloc', 'fichier']
for i in range(100000):
    print(' '.join([random.choice(words) for _ in range(20)]))
" > /tmp/test_file.txt
```

### b. Lancer le job

Les commandes suivantes s'exécutent **à l'intérieur du conteneur** `namenode`. Le fichier est d'abord transféré depuis `/tmp/` local vers HDFS, puis le job WordCount est lancé :

```bash
hdfs dfs -put /tmp/test_file.txt /user/tp/
hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar wordcount /user/tp/test_file.txt /user/tp/output2
```

Dans les compteurs du job :

```
Launched map tasks=15
number of splits: 15
Running job: job_1775780999512_0001   (plus de "local" dans l'identifiant)
```

Les 15 tâches Map sont distribuées sur les 2 NodeManagers et s'exécutent par lots de 2 en parallèle.

---

## 3.6 Interfaces web disponibles

| Interface | URL | Rôle |
|-----------|-----|------|
| HDFS NameNode | http://localhost:9870 | État du cluster HDFS, navigation dans les fichiers |
| YARN ResourceManager | http://localhost:8088 | État du cluster YARN, suivi des jobs |
