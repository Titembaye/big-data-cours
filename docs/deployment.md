# Démarrage

## 1. Récupérer l'image

```bash
docker pull apache/hadoop:3
```

## 2. Lancer le conteneur

```bash
docker run -it --name hadoop-tp \
  --hostname hadoop \
  -p 9870:9870 \
  apache/hadoop:3 bash
```

## 3. Démarrer HDFS dans le conteneur

```bash
# Formater le NameNode (première fois uniquement)
hdfs namenode -format -nonInteractive

# Démarrer les démons HDFS
hdfs --daemon start namenode
hdfs --daemon start datanode
```

Vérifier que les démons tournent :

```bash
jps
```

Résultat attendu :

```
NameNode
DataNode
Jps
```

Interface web disponible sur la machine hôte : `http://localhost:9870`
