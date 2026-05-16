# Lancer le cluster

Résoudre les permissions Docker :

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Démarrer le cluster :

```bash
docker-compose up -d
```
