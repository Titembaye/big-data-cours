# PostgreSQL — Base de données distribuée

Ce TP explore comment PostgreSQL peut simuler et implémenter différentes architectures de bases de données distribuées, en trois parties progressives.

## Progression du cours

| Partie | Sujet | Concept clé |
|--------|-------|-------------|
| [Partie 1 — FDW Distribué](fdw_distribue/index.md) | Foreign Data Wrapper pour simuler une base distribuée | Fragmentation, nœuds distants |
| [Partie 2 — Citus](citus/index.md) | Distribution réelle avec Citus | Sharding, colocalisation, scalabilité horizontale |
| [Partie 3 — FDW Fédéré](fdw_federe/index.md) | Foreign Data Wrapper pour simuler une base fédérée | Hétérogénéité, transparence |

## Contexte : le projet ShopFlow

Tout au long de ce TP, on travaille sur **ShopFlow**, une base e-commerce avec quatre tables :

- `clients` — 800 000 clients
- `produits` — catalogue produits
- `commandes` — 1,3 million de commandes
- `details_commande` — 3,25 millions de lignes de détail

Le défi : rendre cette base performante à grande échelle, en explorant différentes stratégies de distribution.
