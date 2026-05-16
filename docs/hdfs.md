# HDFS - Commandes

Commandes de base HDFS :

```bash
# Lister la racine HDFS
hdfs dfs -ls /

# Voir l'espace disque
hdfs dfs -df -h /

# Créer un répertoire utilisateur
hdfs dfs -mkdir -p /user/root

# Uploader un fichier
hdfs dfs -put /tmp/test.txt /user/root/

# Lire le contenu
hdfs dfs -cat /user/root/test.txt

# Supprimer
hdfs dfs -rm /user/root/test.txt
```
