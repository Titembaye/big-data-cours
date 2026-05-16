# Architecture

Dans ce TP, chaque démon Hadoop tourne dans un conteneur Docker isolé. Le réseau Docker joue le rôle du réseau physique d'un vrai cluster.

Sections :

- HDFS (NameNode, DataNode)
- YARN (ResourceManager, NodeManager, HistoryServer)
- Ports exposés et rôle

Révisez la page `Configuration` pour comprendre comment les conteneurs sont paramétrés.
