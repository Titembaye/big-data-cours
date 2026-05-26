# TP Hadoop avec Docker

## Prérequis

Vérifier que Docker et Docker Compose sont installés :

```bash
docker --version
docker-compose --version
```

---

## Structure du projet

On crée le dossier de travail avec trois sous-dossiers :

```bash
mkdir hd-bigdata
cd hd-bigdata
mkdir -p conf data scripts
```

- `conf/` — les fichiers de configuration Hadoop
- `data/` — les données persistantes des DataNodes
- `scripts/` — les scripts utilitaires (phases suivantes)

---

## Phase 1 — HDFS

### 1.1 Configuration de base

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

Le paramètre `dfs.datanode.data.dir.perm` évite une erreur de permissions lors du démarrage. Par défaut, Hadoop essaie de forcer ses propres permissions sur le dossier de données, ce qui échoue quand ce dossier est monté depuis la machine hôte via Docker.

---

### 1.2 Démarrer le NameNode

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

### 1.3 Ajouter les DataNodes

Les DataNodes sont les nœuds de stockage. Chaque DataNode stocke des blocs de données et envoie régulièrement un signal au NameNode (heartbeat) pour indiquer qu'il est toujours en vie.

On prépare d'abord les dossiers de données persistants pour chaque DataNode, et on leur donne les permissions nécessaires. L'image Docker fait tourner Hadoop avec un utilisateur interne `hadoop` (UID 1000). Même si cet utilisateur correspond à l'UID de l'utilisateur hôte, Hadoop tente de modifier les permissions du dossier au démarrage — ce qui échoue sur un montage bind Docker. Le `chmod 777` règle ce problème pour le contexte du TP.

```bash
mkdir data/datanode1 data/datanode2 data/datanode3 data/datanode4
chmod 777 data/datanode1 data/datanode2 data/datanode3 data/datanode4
```

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

Vérifier que les cinq conteneurs tournent :

```bash
sudo docker ps
```

Sur `http://localhost:9870`, on voit maintenant **Live Nodes: 4** et la capacité totale du cluster (somme des disques alloués aux quatre DataNodes).

---

### 1.4 Erreur courante — clusterID incompatible

Si un DataNode refuse de démarrer avec l'erreur suivante :

```
Incompatible clusterIDs in /opt/hadoop/data/datanode:
namenode clusterID = CID-xxx ; datanode clusterID = CID-yyy
```

Cela signifie que le NameNode a été recréé (nouveau `docker-compose down` puis `up`) et a généré un nouvel identifiant de cluster, mais le DataNode a conservé l'ancien identifiant dans son dossier persistant. Les deux ne se reconnaissent plus.

Solution : vider les dossiers de données des DataNodes pour qu'ils repartent à zéro et adoptent le nouvel identifiant du NameNode.

```bash
sudo docker-compose down
rm -rf data/datanode1/* data/datanode2/* data/datanode3/* data/datanode4/*
sudo docker-compose up -d
```

---

### 1.5 Premiers fichiers dans HDFS

HDFS a son propre système de fichiers, complètement séparé du système Linux du conteneur. Les commandes `hdfs dfs` sont l'équivalent des commandes Linux classiques mais pour HDFS.

Entrer dans le conteneur namenode :

```bash
sudo docker exec -it namenode bash
```

Créer un répertoire dans HDFS :

```bash
hdfs dfs -mkdir -p /user/tp
```

Vérifier qu'il existe :

```bash
hdfs dfs -ls /user/
```

Créer un fichier de test et l'envoyer dans HDFS :

```bash
echo "Bonjour Hadoop, ceci est mon premier fichier HDFS !" > /tmp/test.txt
hdfs dfs -put /tmp/test.txt /user/tp/
```

Lire le fichier depuis HDFS :

```bash
hdfs dfs -cat /user/tp/test.txt
```

Pour quitter le conteneur :

```bash
exit
```

---

### 1.6 Vérifier le stockage physique des blocs

HDFS découpe chaque fichier en blocs (128 MB par défaut) et les distribue sur les DataNodes. Pour un petit fichier comme `test.txt`, un seul bloc est créé.

Depuis la machine hôte, on peut naviguer dans le dossier du DataNode pour voir le bloc physique :

```bash
ls data/datanode1/current/
```

On trouve un dossier `BP-XXXXXXXXX-IP-TIMESTAMP` (Block Pool) et un fichier `VERSION`. En descendant dans l'arborescence :

```bash
ls data/datanode1/current/BP-*/current/finalized/subdir0/subdir0/
```

On voit deux fichiers :

- `blk_XXXXXXXXXX` — le bloc de données brut, contient le contenu réel du fichier
- `blk_XXXXXXXXXX_XXXX.meta` — les métadonnées du bloc, contient le checksum pour détecter toute corruption

```bash
cat data/datanode1/current/BP-*/current/finalized/subdir0/subdir0/blk_*[^meta]
```

Le contenu de `test.txt` est lisible directement dans le bloc. C'est ainsi que HDFS fonctionne : le NameNode connaît la carte, les DataNodes stockent les blocs physiques.

---

## État du cluster à l'issue de la Phase 1

```
NameNode   — port 9870  — carte du système de fichiers
DataNode1  — stockage physique des blocs
DataNode2  — stockage physique des blocs
DataNode3  — stockage physique des blocs
DataNode4  — stockage physique des blocs
```

La Phase 2 introduira MapReduce pour exécuter des traitements distribués sur les données stockées dans HDFS.

## Phase 2 — MapReduce

MapReduce est le moteur de calcul distribué de Hadoop. L'idée fondamentale est d'envoyer le programme vers les données plutôt que l'inverse — chaque nœud traite les blocs qu'il stocke localement, ce qui évite de transférer de gros volumes de données sur le réseau.

Un job MapReduce se déroule en trois étapes :

- **Map** — chaque nœud lit sa portion de données et produit des paires clé/valeur
- **Shuffle** — Hadoop regroupe automatiquement toutes les valeurs par clé
- **Reduce** — chaque nœud agrège les valeurs d'une même clé pour produire le résultat final

### 2.1 Vérifier que les exemples MapReduce sont disponibles

L'image `apache/hadoop:3.3.6` inclut un jar d'exemples contenant plusieurs programmes MapReduce prêts à l'emploi. On vérifie sa présence depuis le conteneur namenode :

```bash
sudo docker exec -it namenode bash
find /opt/hadoop -name "hadoop-mapreduce-examples*.jar"
```

Le fichier doit se trouver à :

```
/opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar
```

Pour lister tous les programmes disponibles dans ce jar :

```bash
hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar
```

---

### 2.2 Préparer les données dans HDFS

On crée un répertoire de travail dans HDFS et on y dépose un fichier texte :

```bash
hdfs dfs -mkdir -p /user/tp
```

```bash
echo "hadoop est un framework distribue
hadoop permet de stocker des donnees sur plusieurs noeuds
hdfs est le systeme de fichiers de hadoop
mapreduce est le moteur de calcul de hadoop
les datanodes stockent les blocs de donnees
le namenode gere la carte des fichiers" > /tmp/texte.txt
```

```bash
hdfs dfs -put /tmp/texte.txt /user/tp/
hdfs dfs -ls /user/tp/
```

---

### 2.3 Lancer le premier job WordCount

WordCount est le programme MapReduce classique — il compte le nombre d'occurrences de chaque mot dans un fichier texte.

```bash
hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar wordcount /user/tp/texte.txt /user/tp/output
```

- Le premier argument est le fichier d'entrée dans HDFS
- Le second est le dossier de sortie — il ne doit pas exister avant le lancement

Les logs affichent la progression :

```
map 0% reduce 0%
map 100% reduce 0%
map 100% reduce 100%
Job completed successfully
```

Lire le résultat :

```bash
hdfs dfs -cat /user/tp/output/part-r-00000
```

On obtient chaque mot avec son nombre d'occurrences, par exemple :

```
hadoop    4
est       3
de        6
```

---

### 2.4 Remarque sur le mode d'exécution

Dans les logs du job, on peut lire :

```
Running job: job_local1434341543_0001
```

Le mot **local** indique que MapReduce a tourné en mode local — tout s'est exécuté dans le NameNode sans distribuer le travail. C'est parce que YARN n'est pas encore configuré. On règle ça dans la Phase 3.

Pour relancer un job, le dossier de sortie doit être supprimé au préalable :

```bash
hdfs dfs -rm -r /user/tp/output
```

---

### 2.5 Ajouter la configuration MapReduce

Il faut indiquer à MapReduce d'utiliser YARN comme gestionnaire de ressources. Sans ce fichier, MapReduce ne sait pas qu'un cluster YARN existe et tombe en mode local.

Créer `conf/mapred-site.xml` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
  <property>
    <name>mapreduce.application.classpath</name>
    <value>/opt/hadoop/share/hadoop/mapreduce/*:/opt/hadoop/share/hadoop/mapreduce/lib/*</value>
  </property>
  <property>
    <name>mapreduce.map.memory.mb</name>
    <value>512</value>
  </property>
  <property>
    <name>mapreduce.reduce.memory.mb</name>
    <value>512</value>
  </property>
  <property>
    <name>mapreduce.map.java.opts</name>
    <value>-Xmx400m</value>
  </property>
  <property>
    <name>mapreduce.reduce.java.opts</name>
    <value>-Xmx400m</value>
  </property>
  <property>
    <name>yarn.app.mapreduce.am.resource.mb</name>
    <value>512</value>
  </property>
  <property>
    <name>yarn.app.mapreduce.am.command-opts</name>
    <value>-Xmx400m</value>
  </property>
</configuration>
```

- `mapreduce.framework.name=yarn` — bascule MapReduce en mode distribué via YARN
- `mapreduce.application.classpath` — indique où trouver les jars MapReduce dans le conteneur
- `mapreduce.map.memory.mb` et `mapreduce.reduce.memory.mb` — mémoire allouée par tâche Map et Reduce. Fixée à 512 MB pour rester dans les limites d'une machine avec 8 GB de RAM
- `mapreduce.map.java.opts` et `mapreduce.reduce.java.opts` — mémoire JVM par tâche, toujours inférieure à la mémoire du conteneur YARN
- `yarn.app.mapreduce.am.resource.mb` — mémoire de l'ApplicationMaster, le processus qui orchestre le job. Par défaut il demande 1536 MB ce qui dépasse notre limite — on le fixe à 512 MB
- `yarn.app.mapreduce.am.command-opts` — mémoire JVM de l'ApplicationMaster

---

## Phase 3 — YARN

YARN (Yet Another Resource Negotiator) est le gestionnaire de ressources du cluster. Il reçoit les demandes de jobs, alloue les ressources disponibles sur les nœuds, et surveille l'exécution. Sans YARN, MapReduce tourne en mode local sur un seul nœud.

YARN est composé de deux types de processus :

- **ResourceManager** — un seul par cluster, c'est le chef d'orchestre qui alloue les ressources
- **NodeManager** — un par nœud de données, il exécute concrètement les tâches et rend compte au ResourceManager

### 3.1 Configuration YARN

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
- `yarn.resourcemanager.address` — adresse et port principal du ResourceManager (port 8032)
- `yarn.resourcemanager.scheduler.address` — port du scheduler, utilisé pour négocier les ressources (port 8030)
- `yarn.resourcemanager.resource-tracker.address` — port utilisé par les NodeManagers pour s'enregistrer et envoyer leurs heartbeats (port 8031). Sans ce paramètre explicite, les NodeManagers ne trouvent pas le ResourceManager et refusent de démarrer
- `yarn.nodemanager.aux-services=mapreduce_shuffle` — active le service shuffle qui transfère les données entre les tâches Map et Reduce
- `yarn.nodemanager.resource.memory-mb=1024` — chaque NodeManager expose 1 GB de RAM au cluster. Adapté pour des machines avec 8 GB de RAM
- `yarn.nodemanager.resource.cpu-vcores=1` — chaque NodeManager expose 1 CPU virtuel
- `yarn.scheduler.minimum-allocation-mb=512` — un conteneur YARN demande au minimum 512 MB
- `yarn.scheduler.maximum-allocation-mb=1024` — un conteneur YARN ne peut pas dépasser 1 GB

---

### 3.2 Mettre à jour docker-compose.yml

On ajoute le ResourceManager et deux NodeManagers. On garde 2 DataNodes et 2 NodeManagers pour rester dans les limites d'une machine avec 8 GB de RAM — au-delà, Docker commence à utiliser le swap et les jobs deviennent instables.

Les quatre fichiers de configuration doivent être montés dans tous les conteneurs — chaque service doit avoir la même vue du cluster.

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

Points importants :

- Le ResourceManager expose le port `8088` — c'est l'interface web YARN
- Les DataNodes dépendent uniquement du NameNode — ils ne parlent qu'à lui
- Les NodeManagers dépendent uniquement du ResourceManager — ils s'y enregistrent au démarrage
- Chaque DataNode a son propre dossier de données persistant

Relancer le cluster :

```bash
sudo docker-compose down
sudo docker-compose up -d
sudo docker ps
```

On doit voir 6 conteneurs actifs : namenode, resourcemanager, datanode1, datanode2, nodemanager1, nodemanager2.

---

### 3.3 Erreur courante — NodeManager ne trouve pas le ResourceManager

Si les NodeManagers démarrent puis s'arrêtent avec l'erreur :

```
Your endpoint configuration is wrong; UnsetHostnameOrPort
Retrying connect to server: 0.0.0.0/0.0.0.0:8031
```

Cela signifie que `yarn-site.xml` n'est pas correctement monté dans le conteneur. Vérifier le chemin de montage dans `docker-compose.yml` :

```bash
sudo docker inspect nodemanager1 | grep yarn-site
```

Le chemin de destination doit être exactement `/opt/hadoop/etc/hadoop/yarn-site.xml` et non `/opt/etc/hadoop/yarn-site.xml` — une faute de frappe courante.

---

### 3.4 Vérifier le cluster YARN

L'interface web YARN est accessible sur `http://localhost:8088`. Elle permet de monitorer le cluster en temps réel :

- `Active Nodes` — nombre de NodeManagers connectés au ResourceManager
- `Total Resources` — capacité totale du cluster en mémoire et CPU
- `Applications` — historique et état des jobs soumis

---

### 3.5 Tester la distribution réelle avec un grand fichier

Avec un petit fichier, Hadoop ne crée qu'un seul bloc et une seule tâche Map — le job ne se distribue pas vraiment. Pour observer la distribution, on génère un fichier assez grand pour être découpé en plusieurs blocs.

On a configuré `dfs.blocksize=1048576` (1 MB) dans `hdfs-site.xml`. Un fichier de 15 MB sera donc découpé en 15 blocs et Hadoop lancera 15 tâches Map.

Depuis le conteneur namenode, générer le fichier :

```bash
python -c "
import random
words = ['hadoop', 'hdfs', 'mapreduce', 'yarn', 'datanode', 'namenode', 'cluster', 'distribue', 'bloc', 'fichier']
for i in range(100000):
    print(' '.join([random.choice(words) for _ in range(20)]))
" > /tmp/grand_fichier.txt
```

Envoyer dans HDFS et lancer le WordCount :

```bash
hdfs dfs -mkdir -p /user/tp
hdfs dfs -put /tmp/grand_fichier.txt /user/tp/
hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar wordcount /user/tp/grand_fichier.txt /user/tp/output2
```

Dans les compteurs du job on voit cette fois :

```
Launched map tasks=15
number of splits: 15
Running job: job_1775780999512_0001   (plus de "local" dans l'identifiant)
```

Les 15 tâches Map sont distribuées sur les 2 NodeManagers et s'exécutent par lots de 2 en parallèle — limité par la mémoire disponible (2 x 1 GB, 2 tâches x 512 MB).

---

### 3.6 Interfaces web disponibles

| Interface | URL | Rôle |
|-----------|-----|------|
| HDFS NameNode | http://localhost:9870 | État du cluster HDFS, navigation dans les fichiers, répartition des blocs |
| YARN ResourceManager | http://localhost:8088 | État du cluster YARN, suivi des jobs en cours et terminés |

Les deux interfaces sont uniquement en lecture — on observe et on monitore, toutes les actions se font en ligne de commande.

---

## État du cluster à l'issue des phases 2 et 3

```
NameNode          — port 9870  — carte du système de fichiers HDFS
ResourceManager   — port 8088  — allocation des ressources YARN
DataNode1         — stockage des blocs HDFS
DataNode2         — stockage des blocs HDFS
NodeManager1      — exécution des tâches MapReduce
NodeManager2      — exécution des tâches MapReduce
```

La Phase 4 introduira Hive pour exécuter des requêtes SQL sur les données stockées dans HDFS.
