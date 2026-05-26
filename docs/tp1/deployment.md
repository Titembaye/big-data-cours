# Démarrage

## 1. Récupérer les fichiers

```bash
git clone https://github.com/Titembaye/big-data-cours.git
cd big-data-cours
```

## 2. Vérifier les permissions Docker

Si la commande `docker-compose up` retourne `permission denied while trying to connect to the Docker daemon socket` :

```bash
# Ajouter l'utilisateur courant au groupe docker
sudo usermod -aG docker $USER

# Appliquer le changement dans le terminal courant
newgrp docker
```

> `newgrp docker` applique le changement dans le terminal courant uniquement. Un redémarrage de session est nécessaire pour que ce soit permanent.

## 3. Lancer le cluster

```bash
docker-compose up -d
```

Cela démarre deux conteneurs :
- `namenode` — le NameNode HDFS (interface web sur le port 9870)
- `datanode` — le DataNode HDFS (se connecte automatiquement au NameNode)

> L'avertissement `version is obsolete` n'est pas bloquant.

## 4. Vérifier que le cluster est prêt

```bash
docker-compose ps
```

Attendre que les deux conteneurs soient en état `Up`. Puis vérifier que le DataNode est bien enregistré :

```bash
docker exec -it namenode hdfs dfsadmin -report
```

Résultat attendu : **Live datanodes (1)**

Interface web disponible sur la machine hôte : `http://localhost:9870`

## 5. Accéder au NameNode

Toutes les commandes HDFS s'exécutent depuis le conteneur `namenode` :

```bash
docker exec -it namenode bash
```

## 6. Arrêter le cluster

```bash
docker-compose down
```

Pour supprimer aussi les volumes (données HDFS perdues) :

```bash
docker-compose down -v
```

> Ne jamais faire `-v` en production. En TP c'est acceptable car les données sont temporaires.
