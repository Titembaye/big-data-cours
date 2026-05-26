import random

produits = ['telephone', 'ordinateur', 'tablette', 'television', 'climatiseur', 
            'refrigerateur', 'machine_a_laver', 'camera', 'imprimante', 'batterie']

regions = ['Lome', 'Kara', 'Sokode', 'Atakpame', 'Dapaong', 
           'Tsevie', 'Aneho', 'Notse', 'Bafilo', 'Mango']

with open('data/transactions.csv', 'w') as f:
    f.write('transaction_id,produit,region,montant,date\n')
    for i in range(500000):
        f.write('{},{},{},{:.2f},{}\n'.format(
            i + 1,
            random.choice(produits),
            random.choice(regions),
            random.uniform(5000, 500000),
            '2026-{:02d}-{:02d}'.format(random.randint(1, 3), random.randint(1, 28))
        ))

print("Fichier généré : data/transactions.csv")