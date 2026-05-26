# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys

produit_courant = None
total = 0

for ligne in sys.stdin:
    ligne = ligne.strip()
    champs = ligne.split('\t')
    
    if len(champs) != 2:
        continue
    
    produit = champs[0]
    
    try:
        montant = float(champs[1])
    except ValueError:
        continue
    
    # Nouveau produit — afficher le resultat du precedent
    if produit_courant and produit != produit_courant:
        print('{}\t{:.2f}'.format(produit_courant, total))
        total = 0
    
    produit_courant = produit
    total += montant

# Afficher le dernier produit
if produit_courant:
    print('{}\t{:.2f}'.format(produit_courant, total))