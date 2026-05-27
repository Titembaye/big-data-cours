import requests
from faker import Faker
import csv
import random
from datetime import datetime, timedelta

NUM_CL= 800000
NUM_COM = 1300000

fake = Faker('fr-FR')
def get_dummy_products(url):
    response = requests.get(url)
    data = response.json()
    return  data['products']





def generate_data():
    # 1. for product
    raw_products = get_dummy_products(url)
    products=[]

    with open('produits.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        #ajouter les noms de colonnes
        writer.writerow(['produit_id', 'nom_produit', 'categorie', 'prix'])

        #ajouter les éléments
        for p in raw_products:
            writer.writerow([p['id'], p['title'], p['category'], p['price']])
            products.append({'id': p['id'], 'prix': p['price']})

    #2. pour clients
    countries = ['Togo', 'Benin', 'Burkina Faso', 'Ghana', 'Mali']
    with open('clients.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id_client', 'nom', 'prenom', 'pays', 'date_inscription'])
        for i in range(1,NUM_CL+1):
            id = i
            nom = fake.last_name()
            prenom = fake.first_name()
            pays = random.choice(countries)
            date_inscription = fake.date_between(start_date='-3y', end_date='today')

            writer.writerow([id,nom,prenom,pays,date_inscription])

    #pour commandes
    statut=['Livrée', 'Validée', 'Expédiée']
    start_date = '2023-01-01'
    with open('commandes.csv', 'w', newline='') as f, open('details_commande.csv', 'w', newline='') as f_det:
        writer = csv.writer(f)
        w_det = csv.writer(f_det)

        writer.writerow(['commande_id', 'client_id', 'date_commande', 'statut'])
        w_det.writerow(['detail_id', 'commande_id', 'client_id', 'produit_id', 'quantite', 'prix_unitaire'])
        detail_id_counter = 1
        for i in range(1, NUM_COM):
            id = i,
            client = random.randint(1, NUM_CL),
            cmd_date = datetime.strptime(start_date , "%Y-%m-%d") + (timedelta(seconds=random.randint(0, 63000000)))
            stat = random.choice(statut)

            writer.writerow([id[0],client[0], cmd_date, stat])

            nb_articles = random.randint(1, 4)
            items = random.sample(products, nb_articles)
            for item in items:
                w_det.writerow([detail_id_counter, id[0], client[0], item['id'], random.randint(1, 2), item['prix']])
                detail_id_counter += 1


if __name__ == '__main__':
    url = "https://dummyjson.com/products?limit=100"
    generate_data()
 
