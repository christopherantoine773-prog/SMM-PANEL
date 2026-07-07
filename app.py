return jsonify({'error': 'Méthode de paiement non supportée'}), 400

    deposit_address = generate_deposit_address(method)
    
    return jsonify({
        'amount': amount,
        'method': method,
        'address': deposit_address,
        'memo': str(user['_id'])[:8]
    }), 200

def generate_deposit_address(method):
    # Simulation d'une adresse de dépôt
    return f"{method.upper()}_ADDR_{secrets.token_hex(8)}"

if name == 'main':
    app.run(port=5000, debug=True)
