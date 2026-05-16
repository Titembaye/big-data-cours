# Vérifier l'état

Interface web NameNode : `http://localhost:9870`

Vérifier les conteneurs :

```bash
docker ps
```

Entrer dans le conteneur NameNode :

```bash
docker exec -it namenode bash
hdfs dfsadmin -report
```
