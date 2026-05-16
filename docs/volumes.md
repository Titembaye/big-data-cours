# Volumes Docker

Les volumes permettent de persister les données importantes : métadonnées NameNode, blocs DataNode, historique.

Exemple extrait de `docker-compose.yml` :

```yaml
namenode:
  volumes:
    - hadoop_namenode:/hadoop/dfs/name
```

Commande utile : `docker volume ls`.
