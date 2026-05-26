# Hadoop TP2 — Cluster complet avec HDFS, MapReduce et YARN

Objectif : construire un cluster Hadoop multi-nœuds depuis zéro en trois phases progressives.

## Prérequis

Vérifier que Docker et Docker Compose sont installés :

```bash
docker --version
docker-compose --version
```

## Structure du projet

```bash
mkdir hd-bigdata
cd hd-bigdata
mkdir -p conf data scripts
```

- `conf/` — les fichiers de configuration Hadoop
- `data/` — les données persistantes des DataNodes
- `scripts/` — les scripts utilitaires

## Phases du TP

| Phase | Contenu | Port |
|-------|---------|------|
| [Phase 1 — HDFS](hdfs.md) | NameNode + 4 DataNodes, stockage des blocs | 9870 |
| [Phase 2 — MapReduce](mapreduce.md) | Premier job distribué (WordCount) | — |
| [Phase 3 — YARN](yarn.md) | ResourceManager + NodeManagers, exécution réelle | 8088 |
