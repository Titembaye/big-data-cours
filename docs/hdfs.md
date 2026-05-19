# Explorer HDFS

Commandes à exécuter depuis l'intérieur du conteneur.

```bash
# Lister la racine
hdfs dfs -ls /

# Créer un répertoire
hdfs dfs -mkdir -p /user/root

# Créer un fichier local et l'uploader
echo "Bonjour Hadoop" > /tmp/test.txt
hdfs dfs -put /tmp/test.txt /user/root/

# Lire le fichier depuis HDFS
hdfs dfs -cat /user/root/test.txt

# Espace disponible
hdfs dfs -df -h /

# Supprimer le fichier
hdfs dfs -rm /user/root/test.txt
```

Rapport de l'état du cluster :

```bash
hdfs dfsadmin -report
```
