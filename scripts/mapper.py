# -*- coding: utf-8 -*-
#!/usr/bin/env python
import sys

for ligne in sys.stdin:
    ligne = ligne.strip()
    
    # Ignorer l'en-tete
    if ligne.startswith('transaction_id'):
        continue
    
    champs = ligne.split(',')
    
    # Verifier que la ligne est complete
    if len(champs) != 5:
        continue
    
    produit = champs[1]
    montant = champs[3]
    
    # Emettre la paire cle/valeur
    print('{}\t{}'.format(produit, montant))