from flask import Flask, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import os

app = Flask(name)

# Gestion de la connexion MongoDB (Local ou Cloud pour Render)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['viewbooster']
users = db['users']
orders = db['orders']

# --- UTILITAIRES ---
def generate_api_key():
    return secrets.token_hex(32)

# --- INSCRIPTION ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email et mot de passe requis'}), 400

    if users.find_one({'email': email}):
        return jsonify({'error': 'Email déjà utilisé'}), 400
    
    # Sécurisation forte du mot de passe
    hashed_password = generate_password_hash(password)
    
    user = {
        'email': email,
        'password': hashed_password,
        'api_key': generate_api_key(),
        'credits': 0.0,
        'role': 'user'
    }
    users.insert_one(user)
    return jsonify({'api_key': user['api_key']}), 201

# --- COMMANDE DE VUES ---
@app.route('/order/views', methods=['POST'])
def order_views():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'Clé API manquante'}), 401

    user = users.find_one({'api_key': api_key})
    if not user:
        return jsonify({'error': 'Accès refusé'}), 403

    data = request.json or {}
    url = data.get('url')
    
    # Validation stricte des entrées
    try:
        quantity = int(data.get('quantity', 0))
        if quantity <= 0:
            return jsonify({'error': 'La quantité doit être supérieure à 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Quantité invalide'}), 400

    if not url:
        return jsonify({'error': 'Lien URL requis'}), 400

    # Calcul du coût (0.50€ / 1000 vues)
    cost = (quantity / 1000) * 0.5 

    if user.get('credits', 0) < cost:
        return jsonify({'error': 'Crédits insuffisants'}), 400

    # On glisse la commande dans MongoDB avec le statut 'pending'
    # C'est l'équivalent de la déposer dans une boîte aux lettres
    order = {
        'user_id': user['_id'],
        'type': 'youtube_views',
        'url': url,
        'quantity': quantity,
        'status': 'pending'
    }
    orders.insert_one(order)

    # Déduire les crédits du client
    users.update_one({'_id': user['_id']}, {'$inc': {'credits': -cost}})
    
    return jsonify({
        'status': 'Commande enregistrée et mise en file d\'attente', 
        'order_id': str(order['_id'])
    }), 200

# --- AJOUT DE CREDITS ---
@app.route('/add_credits', methods=['POST'])
def add_credits():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'Clé API manquante'}), 401

    user = users.find_one({'api_key': api_key})
    if not user:
        return jsonify({'error': 'Accès refusé'}), 403

    data = request.json or {}
    method = data.get('method')
    
    try:
        amount = float(data.get('amount', 0))
        if amount <= 0:
            return jsonify({'error': 'Le montant doit être supérieur à 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Montant invalide'}), 400

    if not method or method.lower() not in ['btc', 'xmr', 'usdt']:
        return jsonify({'error': 'Méthode non supportée'}), 400

    deposit_address = generate_deposit_address(method)
    
    return jsonify({
        'amount': amount,
        'method': method,
        'address': deposit_address,
        'memo': str(user['_id'])[:8]
    }), 200

def generate_deposit_address(method):
    return f"{method.upper()}_ADDR_{secrets.token_hex(8)}"

if name == 'main':
    # Le mode debug permet de voir les erreurs s'afficher directement dans la console
    app.run(port=5000, debug=True)
