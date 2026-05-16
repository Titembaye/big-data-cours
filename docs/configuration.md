# Configuration

Le fichier central `hadoop.env` injecte les propriétés dans les fichiers XML Hadoop.

Convention :

```
PRÉFIXE_CONF_clé_avec_underscores=valeur
```

Préfixes : `CORE_CONF_`, `HDFS_CONF_`, `YARN_CONF_`, `MAPRED_CONF_`.

Remplacement : les points `.` deviennent `_`. Les tirets `-` sont représentés par `___`.
