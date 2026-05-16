
# Cours Big Data

Bienvenue — cette documentation est organisée pour faciliter la lecture et la navigation.

Objectif : déployer un cluster Hadoop en pseudo-distribué via Docker, explorer HDFS et exécuter un job MapReduce.

Pages principales :

- Architecture
- Déploiement
- Configuration
- Volumes Docker
- Lancer le cluster
- Vérifier l'état
- HDFS - Commandes

Vous pouvez modifier chaque chapitre séparément. Les pages détaillées sont listées dans la navigation.
---

## Table des matières

1. [Comprendre les modes de déploiement Hadoop](#1-comprendre-les-modes-de-déploiement-hadoop)
2. [Architecture du cluster Docker](#2-architecture-du-cluster-docker)
3. [Récupérer le dépôt](#3-récupérer-le-dépôt)
4. [Comprendre la configuration — `hadoop.env`](#4-comprendre-la-configuration--hadoopenv)
5. [Comprendre les volumes Docker](#5-comprendre-les-volumes-docker)
6. [Lancer le cluster](#6-lancer-le-cluster)
7. [Vérifier l'état du cluster](#7-vérifier-létat-du-cluster)
8. [Explorer HDFS en ligne de commande](#8-explorer-hdfs-en-ligne-de-commande)

---

## 1. Comprendre les modes de déploiement Hadoop

Hadoop peut être déployé dans trois configurations selon le contexte d'utilisation.

### Mode Local (Standalone)

Hadoop tourne comme un simple processus Java, sans démon, sans HDFS. Il utilise le système de fichiers local de la machine. Ce mode est adapté au débogage rapide de jobs MapReduce — il n'y a aucune configuration à faire, mais aucun composant distribué n'est actif.

### Mode Pseudo-Distribué

Hadoop tourne sur une seule machine, mais simule un vrai cluster : chaque démon (NameNode, DataNode, ResourceManager, etc.) tourne dans un **processus séparé**. HDFS et YARN sont actifs. C'est le mode utilisé dans ce TP — via Docker, chaque démon est isolé dans son propre conteneur.

### Mode Fully Distributed

Plusieurs machines physiques ou virtuelles forment un vrai cluster. Un nœud Master héberge le NameNode et le ResourceManager, les nœuds Workers hébergent les DataNodes et NodeManagers. Ce mode est utilisé en production.

| Critère | Local | Pseudo-distribué | Fully Distributed |
|---|---|---|---|
| Machines | 1 | 1 | N (≥ 2) |
| HDFS actif | Non | Oui | Oui |
| YARN actif | Non | Oui | Oui |
| Usage | Debug | Apprentissage / TP | Production |

---

## 2. Architecture du cluster Docker

Dans ce TP, chaque démon Hadoop tourne dans un conteneur Docker isolé. Le réseau Docker joue le rôle du réseau physique d'un vrai cluster.

### Les deux couches de Hadoop

**HDFS** — le système de fichiers distribué

| Démon | Rôle |
|---|---|
| NameNode | Gère les métadonnées : qui stocke quoi, où |
| DataNode | Stocke physiquement les blocs de données |

**YARN** — le gestionnaire de ressources et d'exécution

| Démon | Rôle |
|---|---|
| ResourceManager | Gère les ressources du cluster (CPU, RAM) et planifie les jobs |
| NodeManager | Tourne sur chaque worker, exécute les tâches |
| HistoryServer | Conserve l'historique des jobs MapReduce |

> **À retenir** : NameNode et ResourceManager sont deux rôles distincts. Ils peuvent tourner sur la même machine (ou dans le même nœud), mais leurs responsabilités n'ont aucun lien. Le NameNode gère les fichiers, le ResourceManager gère les calculs.

### Les ports exposés

Le NameNode expose deux ports, chacun avec un rôle précis :

| Port | Protocole | Utilisé par |
|---|---|---|
| `9870` | HTTP | Navigateur — interface web de supervision HDFS |
| `9000` | RPC | Clients HDFS, jobs MapReduce, autres démons |

Le port `9000` est le point d'entrée déclaré dans `core-site.xml` :

```xml
<property>
  <name>fs.defaultFS</name>
  <value>hdfs://namenode:9000</value>
</property>
```

Quand une commande `hdfs dfs` est exécutée, le client contacte le NameNode sur le port `9000` pour obtenir les métadonnées, puis communique directement avec les DataNodes pour lire ou écrire les blocs.

> **Note sur la notation Docker** : dans `docker ps`, les ports apparaissent en double :
> ```
> 0.0.0.0:9870->9870/tcp, [::]:9870->9870/tcp
> ```
> `0.0.0.0` désigne toutes les interfaces IPv4, `[::]` toutes les interfaces IPv6. Ce n'est pas une duplication — Docker expose le port sur les deux protocoles réseau par défaut.

---

## 3. Récupérer le dépôt

```bash
git clone https://github.com/big-data-europe/docker-hadoop.git
cd docker-hadoop
```

### Structure du dépôt

```
docker-hadoop/
├── base/               # Image de base commune à tous les conteneurs
├── namenode/           # Démon NameNode (HDFS)
├── datanode/           # Démon DataNode (HDFS)
├── resourcemanager/    # Démon ResourceManager (YARN)
├── nodemanager/        # Démon NodeManager (YARN)
├── historyserver/      # Historique des jobs MapReduce
├── submit/             # Utilitaire pour soumettre des jobs
├── hadoop.env          # Fichier de configuration central
└── docker-compose.yml  # Définition du cluster
```

Chaque dossier contient un `Dockerfile` qui étend l'image `base` pour configurer le démon correspondant.

### Note sur la version

Le dépôt utilise Hadoop **3.2.1** via les images `bde2020`. Ces images ne sont plus maintenues activement et ne disposent pas de tags pour la version 3.3.6. Les concepts HDFS et MapReduce sont identiques entre les deux versions — ce TP est valable pour les deux.

> En Phase 2, nous construirons notre propre image avec la version cible.

---

## 4. Comprendre la configuration — `hadoop.env`

Le fichier `hadoop.env` est le fichier de configuration central partagé entre tous les conteneurs. Il utilise une convention de nommage précise que les étudiants doivent maîtriser.

### Convention de nommage

Chaque variable suit le schéma :

```
PRÉFIXE_CONF_clé_avec_underscores=valeur
```

Le préfixe indique dans quel fichier XML Hadoop la propriété sera injectée au démarrage du conteneur :

| Préfixe | Fichier XML Hadoop |
|---|---|
| `CORE_CONF_` | `core-site.xml` |
| `HDFS_CONF_` | `hdfs-site.xml` |
| `YARN_CONF_` | `yarn-site.xml` |
| `MAPRED_CONF_` | `mapred-site.xml` |

Les points `.` dans les noms de propriétés Hadoop sont remplacés par des underscores `_` :

```
dfs.replication              →   HDFS_CONF_dfs_replication
fs.defaultFS                 →   CORE_CONF_fs_defaultFS
yarn.resourcemanager.hostname →   YARN_CONF_yarn_resourcemanager_hostname
```

> **Piège — le triple underscore `___`** : certaines clés contiennent des tirets `-` dans leur nom original. Ces tirets sont représentés par **trois underscores** dans `hadoop.env` :
>
> ```
> HDFS_CONF_dfs_namenode_datanode_registration_ip___hostname___check
> ```
> correspond à la propriété XML :
> ```
> dfs.namenode.datanode.registration.ip-hostname-check
> ```

---

## 5. Comprendre les volumes Docker

Par défaut, tout ce qui est écrit à l'intérieur d'un conteneur est perdu quand il s'arrête. C'est un problème majeur pour Hadoop :

- Le **NameNode** doit persister ses métadonnées entre les redémarrages
- Le **DataNode** doit persister les blocs de données
- Le **HistoryServer** doit persister l'historique des jobs

Les volumes résolvent ce problème en montant un répertoire persistant dans le conteneur.

```yaml
# Extrait de docker-compose.yml
namenode:
  volumes:
    - hadoop_namenode:/hadoop/dfs/name
```

Cela signifie que `/hadoop/dfs/name` à l'intérieur du conteneur est stocké dans un volume Docker nommé `hadoop_namenode` sur la machine hôte. Après un `docker-compose down` puis `docker-compose up`, le NameNode retrouve ses métadonnées intactes.

```bash
# Lister les volumes créés
docker volume ls
```

Résultat attendu :

```
DRIVER    VOLUME NAME
local     docker-hadoop_hadoop_namenode
local     docker-hadoop_hadoop_datanode
local     docker-hadoop_hadoop_historyserver
```

> **Piège — données corrompues entre deux lancements** : si la configuration Hadoop est modifiée après un premier démarrage (par exemple `dfs.replication`), le NameNode peut détecter une incohérence avec les métadonnées persistées et refuser de démarrer. Solution : supprimer les volumes avant de relancer.
>
> ```bash
> docker-compose down -v   # -v supprime les volumes
> docker-compose up -d
> ```
>
> Ne jamais faire `-v` en production. En TP, c'est acceptable car les données sont temporaires.

---

## 6. Lancer le cluster

### Résoudre le problème de permission Docker

Par défaut, seul `root` peut communiquer avec le démon Docker. Si la commande `docker-compose up` retourne :

```
permission denied while trying to connect to the Docker daemon socket
```

Exécuter :

```bash
# Ajouter l'utilisateur courant au groupe docker
sudo usermod -aG docker $USER

# Appliquer le changement dans le terminal courant
newgrp docker
```

> `newgrp docker` applique le changement dans le terminal courant uniquement. Un redémarrage de session est nécessaire pour que ce soit permanent.

### Démarrer le cluster

```bash
docker-compose up -d
```

L'option `-d` (detached) lance les conteneurs en arrière-plan.

> **Note** : l'avertissement `version is obsolete` n'est pas bloquant. Les nouvelles versions de Docker Compose n'ont plus besoin du champ `version:` en tête du fichier.

### Vérifier que les conteneurs sont démarrés

```bash
docker ps
```

Les 5 conteneurs doivent être en état `Up` et `healthy` :

```
NAMES             STATUS
namenode          Up X minutes (healthy)
datanode          Up X minutes (healthy)
resourcemanager   Up X minutes (healthy)
nodemanager       Up X minutes (healthy)
historyserver     Up X minutes (healthy)
```

> **Piège — conteneur qui ne passe pas `healthy`** : si un conteneur reste en état `starting` ou passe en `unhealthy`, consulter ses logs :
>
> ```bash
> docker logs namenode
> ```

---

## 7. Vérifier l'état du cluster

### Interface web du NameNode

Ouvrir dans un navigateur : `http://localhost:9870`

Les informations importantes à lire sur le dashboard :

| Information | Signification |
|---|---|
| **Security : Off** | Pas d'authentification Kerberos — normal en TP |
| **Safemode : Off** | Cluster opérationnel, HDFS accepte les écritures |
| **Live Nodes** | Nombre de DataNodes actifs |
| **DFS Used** | Espace HDFS consommé |
| **Non DFS Used** | Espace consommé par le système hôte (hors HDFS) |

> **Concept Safemode** : au démarrage, le NameNode passe en Safemode le temps de recevoir les rapports des DataNodes. Il refuse toute écriture pendant cette phase. En TP, s'il reste bloqué en Safemode, c'est un signe de problème — consulter les logs.

> **Piège — interfaces web inaccessibles** : seul le NameNode expose ses ports vers la machine hôte (`localhost:9870` et `localhost:9000`). Les autres démons (ResourceManager sur 8088, NodeManager sur 8042, HistoryServer sur 8188) sont uniquement accessibles depuis le réseau Docker interne. Tenter d'ouvrir `http://localhost:8088` depuis le navigateur ne fonctionnera pas.

### Rapport détaillé via la ligne de commande

```bash
# Entrer dans le conteneur NameNode
docker exec -it namenode bash

# Rapport complet du cluster
hdfs dfsadmin -report
```

> **L'option `-it`** : `-i` (interactive) maintient l'entrée standard ouverte pour taper des commandes. `-t` (tty) alloue un pseudo-terminal pour avoir un prompt shell. Les deux ensemble donnent une session interactive comme un SSH.

Le rapport affiche pour chaque DataNode actif : son adresse IP interne Docker, son hostname (ID du conteneur), l'espace disque configuré, utilisé et disponible.

> **Piège — Under-Replicated Blocks** : le rapport peut afficher des blocs sous-répliqués :
>
> ```
> Under replicated blocks: 5
> ```
>
> Par défaut, Hadoop veut répliquer chaque bloc 3 fois (`dfs.replication=3`). Avec un seul DataNode, c'est impossible. Ces blocs correspondent aux fichiers internes que Hadoop stocke dans HDFS au démarrage. Ce warning est **attendu** dans ce contexte et n'est pas bloquant pour le TP.

---

## 8. Explorer HDFS en ligne de commande

### Entrer dans le NameNode

```bash
docker exec -it namenode bash
```

### La syntaxe `hdfs dfs`

Les commandes HDFS imitent volontairement Unix pour réduire la courbe d'apprentissage :

```
hdfs dfs -ls /
│    │    │
│    │    └─ commande style Unix
│    └─ sous-système : opérations sur le système de fichiers distribué
└─ outil principal Hadoop
```

| Commande Unix | Équivalent HDFS |
|---|---|
| `ls` | `hdfs dfs -ls` |
| `mkdir` | `hdfs dfs -mkdir` |
| `cp` | `hdfs dfs -cp` |
| `rm` | `hdfs dfs -rm` |
| `cat` | `hdfs dfs -cat` |
| `mv` | `hdfs dfs -mv` |

### Commandes de base

```bash
# Lister la racine HDFS
hdfs dfs -ls /

# Voir l'espace disque
hdfs dfs -df -h /

# Créer un répertoire utilisateur
hdfs dfs -mkdir -p /user/root

# Créer un fichier de test en local dans le conteneur
echo "Bonjour Hadoop" > /tmp/test.txt

# Uploader le fichier dans HDFS
hdfs dfs -put /tmp/test.txt /user/root/

# Vérifier que le fichier est bien dans HDFS
hdfs dfs -ls /user/root/

# Lire le contenu depuis HDFS
hdfs dfs -cat /user/root/test.txt

# Supprimer le fichier
hdfs dfs -rm /user/root/test.txt
```

---

*Phase 2 : Construction d'une image custom Hadoop 3.3.6 et exécution de jobs MapReduce — à venir.*
