# Explorer HDFS

Toutes les commandes s'exécutent depuis l'intérieur du conteneur (`docker exec -it hadoop-tp bash`).

---

## Structure des commandes

```
hdfs dfs -<commande> [options] [chemin]
```

`hdfs dfs` opère sur le système de fichiers distribué. Les chemins HDFS commencent par `/` (racine HDFS, distincte de la racine Linux du conteneur).

---

## Navigation et listage

```bash
# Lister la racine HDFS
hdfs dfs -ls /

# Lister récursivement
hdfs dfs -ls -R /

# Lister avec tailles lisibles (Ko, Mo, Go)
hdfs dfs -ls -h /user
```

La sortie de `-ls` ressemble à Unix mais ajoute le **facteur de réplication** (colonne 2) et le **nom du bloc** :

```
-rw-r--r--   1 root supergroup         15 2024-01-01 12:00 /user/root/test.txt
              ^
              facteur de réplication (1 = pas de copie redondante)
```

---

## Créer des répertoires

```bash
# Créer un répertoire
hdfs dfs -mkdir /data

# Créer avec les parents intermédiaires (-p comme mkdir -p Linux)
hdfs dfs -mkdir -p /user/root/projets
```

---

## Transférer des fichiers

```bash
# Uploader un fichier local vers HDFS
hdfs dfs -put /tmp/test.txt /user/root/

# Uploader plusieurs fichiers
hdfs dfs -put /tmp/*.txt /user/root/

# Même chose avec -copyFromLocal (alias de -put)
hdfs dfs -copyFromLocal /tmp/test.txt /user/root/

# Télécharger un fichier HDFS vers le système local
hdfs dfs -get /user/root/test.txt /tmp/copie.txt

# Alias de -get
hdfs dfs -copyToLocal /user/root/test.txt /tmp/copie.txt
```

---

## Lire des fichiers

```bash
# Afficher le contenu complet
hdfs dfs -cat /user/root/test.txt

# Afficher les N premières lignes
hdfs dfs -head /user/root/test.txt

# Afficher les dernières lignes
hdfs dfs -tail /user/root/test.txt

# Afficher avec décodage (fichiers texte compressés)
hdfs dfs -text /user/root/fichier.gz
```

---

## Copier et déplacer

```bash
# Copier dans HDFS (source et destination dans HDFS)
hdfs dfs -cp /user/root/test.txt /data/test.txt

# Déplacer / renommer dans HDFS
hdfs dfs -mv /user/root/test.txt /user/root/ancien.txt
```

---

## Supprimer

```bash
# Supprimer un fichier
hdfs dfs -rm /user/root/test.txt

# Supprimer un répertoire et son contenu
hdfs dfs -rm -r /user/root/projets

# Supprimer sans passer par la corbeille HDFS
hdfs dfs -rm -skipTrash /user/root/test.txt
```

Par défaut, les fichiers supprimés vont dans `/user/<nom>/.Trash` — comme une corbeille. `-skipTrash` supprime définitivement.

---

## Espace disque

```bash
# Espace total disponible sur HDFS
hdfs dfs -df -h /

# Taille d'un répertoire ou fichier
hdfs dfs -du -h /user/root

# Taille résumée (total du répertoire seulement)
hdfs dfs -du -s -h /user/root
```

---

## Permissions et propriété

```bash
# Changer les permissions (même syntaxe que chmod Linux)
hdfs dfs -chmod 755 /user/root/test.txt

# Changer le propriétaire
hdfs dfs -chown root:supergroup /user/root/test.txt
```

---

## Facteur de réplication

Le facteur de réplication définit combien de copies d'un bloc HDFS sont conservées sur les DataNodes.

```bash
# Voir le facteur de réplication d'un fichier
hdfs dfs -stat %r /user/root/test.txt

# Changer le facteur de réplication
hdfs dfs -setrep 2 /user/root/test.txt

# Changer récursivement sur un répertoire
hdfs dfs -setrep -R 2 /user/root
```

Avec un seul DataNode, mettre un facteur > 1 génère des warnings ("under-replicated blocks") car il n'y a pas assez de nœuds pour stocker les copies.

---

## Vérifier l'intégrité des fichiers

```bash
# Vérifier les checksums d'un fichier
hdfs dfs -checksum /user/root/test.txt

# Vérifier l'état du système de fichiers (blocs manquants, corrompus)
hdfs fsck /
```

`hdfs fsck` analyse l'ensemble du système de fichiers et signale les blocs sous-répliqués, manquants ou corrompus.

---

## Administration du cluster

```bash
# Rapport complet : DataNodes actifs, espace disque, blocs
hdfs dfsadmin -report

# État du Safemode (mode lecture seule au démarrage)
hdfs dfsadmin -safemode get

# Forcer la sortie du Safemode
hdfs dfsadmin -safemode leave
```

Le **Safemode** est un état de démarrage : le NameNode attend que suffisamment de DataNodes aient rapporté leurs blocs avant d'accepter des écritures. En TP, s'il reste bloqué : `hdfs dfsadmin -safemode leave`.
