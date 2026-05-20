# TP Hadoop — HDFS

Cluster Hadoop 3.2.1 (NameNode + DataNode) via Docker.

## Prérequis

- Docker
- Docker Compose
- Git

## 1. Récupérer les fichiers

```bash
git clone https://github.com/Titembaye/big-data-cours.git
cd big-data-cours
```

## 2. Vérifier les permissions Docker

Si la commande `docker-compose up` retourne `permission denied` :

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 3. Démarrer le cluster

```bash
docker-compose up -d
```

Vérifier que les deux conteneurs sont actifs :

```bash
docker ps
```

Interface web NameNode : `http://localhost:9870`

## 4. Accéder au cluster

```bash
docker exec -it namenode bash
```

## 5. Arrêter le cluster

```bash
docker-compose down
```

> Consultez le site du cours pour les instructions détaillées et les exercices.
