# Démarrage

## 1. Lancer le cluster

```bash
docker-compose up -d
```

Cela démarre deux conteneurs :
- `namenode` — le NameNode HDFS (interface web sur le port 9870)
- `datanode` — le DataNode HDFS (se connecte automatiquement au NameNode)

## 2. Vérifier que le cluster est prêt

```bash
docker-compose ps
```

Attendre que les deux conteneurs soient en état `Up`. Puis vérifier que le DataNode est bien enregistré :

```bash
docker exec -it namenode hdfs dfsadmin -report
```

Résultat attendu : **Live datanodes (1)**

Interface web disponible sur la machine hôte : `http://localhost:9870`

## 3. Accéder au NameNode

Toutes les commandes HDFS s'exécutent depuis le conteneur `namenode` :

```bash
docker exec -it namenode bash
```

## 4. Arrêter le cluster

```bash
docker-compose down
```

Pour supprimer aussi les volumes (données HDFS perdues) :

```bash
docker-compose down -v
```
