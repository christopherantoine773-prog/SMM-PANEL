from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import random
import os
from pymongo import MongoClient

# Connexion à la base MongoDB (Local)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['viewbooster']
orders = db['orders']

def get_random_proxy():
    # Liste de proxies résidentiels (pense à y mettre de vrais proxies fonctionnels)
    proxies = [
        "203.10.10.10:8080",
        "192.168.1.20:3128",
        "104.25.78.1:80"
    ]
    return random.choice(proxies)

def create_driver():
    options = Options()
    options.add_argument('--headless')  # S'exécute sans ouvrir de fenêtre visible
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Optionnel : Désactive la ligne pour les proxies si tu n'as pas encore de liste valide
    # options.add_argument(f'--proxy-server=http://{get_random_proxy()}')
    
    driver = webdriver.Chrome(options=options)
    return driver

def watch_video(url, duration):
    print(f"   [Bot] Ouverture du navigateur pour : {url}")
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(5)  # Laisse la page charger un peu
        
        # Simuler un comportement humain (Liker de temps en temps)
        if random.random() > 0.5:
            like_button = driver.find_elements(By.XPATH, '//button[@aria-label="J’aime"]')
            if like_button:
                like_button[0].click()
                print("   [Bot] Bouton J'aime cliqué !")
        
        # Visionnage
        total_sleep = duration + random.uniform(5, 15)
        print(f"   [Bot] Visionnage en cours pendant {int(total_sleep)} secondes...")
        time.sleep(total_sleep)
        
    except Exception as e:
        print(f"   [Erreur Bot] Problème durant le visionnage : {e}")
    finally:
        driver.quit()
        print("   [Bot] Fermeture du navigateur.")

def process_order(order):
    order_id = order['_id']
    url = order['url']
    quantity = order['quantity']
    
    print(f"\n[Worker] >>> Nouvelle commande détectée ! ID: {order_id}")
    print(f"[Worker] Cible : {url} | Quantité demandée : {quantity}")
    
    # 1. On passe le statut à 'processing' pour éviter qu'un autre worker ne la prenne
    orders.update_one({'_id': order_id}, {'$set': {'status': 'processing'}})
    
    # 2. On exécute la quantité demandée
    for i in range(quantity):
        print(f"[Worker] Lancement de la vue {i+1}/{quantity}")
        duration = random.randint(30, 90)  # Durée de vue aléatoire entre 30 et 90 sec
        
        watch_video(url, duration)
        
        # Pause aléatoire pour paraître naturel entre chaque lancement de bot
        pause = random.uniform(3, 7)
        print(f"[Worker] Pause de {int(pause)} secondes avant la prochaine vue...")
        time.sleep(pause)
        
    # 3. La commande est complétée
    orders.update_one({'_id': order_id}, {'$set': {'status': 'completed'}})
    print(f"[Worker] <<< Commande {order_id} terminée avec succès !")

if name == 'main':
    print("="*60)
    print("  GESTIONNAIRE DE BOTS VIEWBOOSTER PRO DÉMARRÉ")
    print("  En attente de commandes dans MongoDB...")
    print("="*60)
    
    while True:
        # Recherche la commande 'pending' la plus ancienne
        next_order = orders.find_one({'status': 'pending'})
        
        if next_order:
            process_order(next_order)
        else:
            # Attend 5 secondes avant de vérifier à nouveau si la base est vide
            time.sleep(5)
