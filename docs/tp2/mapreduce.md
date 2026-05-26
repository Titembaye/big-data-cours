# Phase 2 — MapReduce

MapReduce est le moteur de calcul distribué de Hadoop. L'idée fondamentale est d'envoyer le programme vers les données plutôt que l'inverse — chaque nœud traite les blocs qu'il stocke localement.

Un job MapReduce se déroule en trois étapes :

- **Map** — chaque nœud lit sa portion de données et produit des paires clé/valeur
- **Shuffle** — Hadoop regroupe automatiquement toutes les valeurs par clé
- **Reduce** — chaque nœud agrège les valeurs d'une même clé pour produire le résultat final

---

## 2.1 Vérifier que les exemples MapReduce sont disponibles

L'image `apache/hadoop:3.3.6` inclut un jar d'exemples prêts à l'emploi. Depuis le conteneur namenode :

```bash
sudo docker exec -it namenode bash
find /opt/hadoop -name "hadoop-mapreduce-examples*.jar"
```

Le fichier se trouve à :

```
/opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar
```

Pour lister tous les programmes disponibles :

```bash
hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar
```

---

## 2.2 Préparer les données dans HDFS

Créer un répertoire et y déposer un fichier texte :

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

## 2.3 Lancer le premier job WordCount

WordCount compte le nombre d'occurrences de chaque mot dans un fichier texte.

```bash
hadoop jar /opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar wordcount /user/tp/texte.txt /user/tp/output
```

Le dossier de sortie ne doit pas exister avant le lancement.

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

Pour relancer un job, supprimer d'abord le dossier de sortie :

```bash
hdfs dfs -rm -r /user/tp/output
```

---

## 2.4 Remarque sur le mode d'exécution

Dans les logs du job, on peut lire :

```
Running job: job_local1434341543_0001
```

Le mot **local** indique que MapReduce a tourné en mode local — tout s'est exécuté dans le NameNode sans distribuer le travail. C'est parce que YARN n'est pas encore configuré. On règle ça dans la [Phase 3](yarn.md).

---

## 2.5 Ajouter la configuration MapReduce

Il faut indiquer à MapReduce d'utiliser YARN comme gestionnaire de ressources. Sans ce fichier, MapReduce reste en mode local.

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
- `mapreduce.map.memory.mb` / `mapreduce.reduce.memory.mb` — mémoire par tâche, fixée à 512 MB pour rester dans les limites d'une machine avec 8 GB de RAM
- `yarn.app.mapreduce.am.resource.mb` — mémoire de l'ApplicationMaster. Par défaut il demande 1536 MB — on le fixe à 512 MB
