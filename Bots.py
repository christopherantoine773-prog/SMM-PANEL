from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import random
from pymongo import MongoClient

# Connexion à la même base MongoDB (Mets l'URI Atlas si tu es sur le cloud)
client = MongoClient('mongodb://localhost:27017/')
db = client['viewbooster']
orders = db['orders']

def create_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    # options.add_argument(f'--proxy-server=http://{get_random_proxy()}')
    return webdriver.Chrome(options=options)

def watch_video(url, duration):
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(5)
        # Simulation clic Like de temps en temps
        if random.random() > 0.5:
            like_button = driver.find_elements(By.XPATH, '//button[@aria-label="J’aime"]')
            if like_button:
                like_button[0].click()
                print("[Bot] Vidéo likée !")
        
        print(f"[Bot] Visionnage en cours pour {duration} secondes...")
        time.sleep(duration)
    except Exception as e:
        print(f"[Erreur Bot]: {e}")
    finally:
        driver.quit()

def process_order(order):
    order_id = order['_id']
    url = order['url']
    quantity = order['quantity']
    
    print(f"\n[Worker] Début du traitement de la commande {order_id} ({quantity} vues)")
    
    # On met à jour le statut dans MongoDB pour dire qu'on s'en occupe
    orders.update_one({'_id': order_id}, {'$set': {'status': 'processing'}})
    
    # On exécute les vues les unes après les autres de manière stable
    for i in range(quantity):
        print(f"[Worker] Lancement de la vue {i+1}/{quantity}")
        duration = random.randint(30, 60) # Temps de visionnage aléatoire
        
        watch_video(url, duration)
        
        # Pause aléatoire entre deux vues pour ne pas éveiller les soupçons
        time.sleep(random.uniform(2, 5))
        
    # Une fois fini, on passe le statut à 'completed'
    orders.update_one({'_id': order_id}, {'$set': {'status': 'completed'}})
    print(f"[Worker] Commande {order_id} terminée avec succès !")

if name == 'main':
    print("[Système] Le gestionnaire de bots est démarré et écoute MongoDB...")
    
    while True:
        # On cherche une commande en attente (la plus ancienne)
        next_order = orders.find_one({'status': 'pending'})
        
        if next_order:
            # Si on trouve une commande, on la traite
            process_order(next_order)
        else:
            # Si pas de commande, on dort 5 secondes avant de revérifier
            time.sleep(5)
