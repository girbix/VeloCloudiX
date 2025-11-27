from functools import wraps
from flask import session, redirect, jsonify

# Linea 4-7: DATABASE UTENTI (in produzione usare DB con password hashate)
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'operatore': {'password': 'operatore123', 'role': 'operator'}
}

# Linea 10-14: DECORATORE PER RICHIEDERE LOGIN
def login_required(f):
    @wraps(f)  # Preserva i metadati della funzione originale
    def decorated(*args, **kwargs):
        if 'username' not in session:  # Se utente non loggato
            return redirect('/login')   # Reindirizza al login
        return f(*args, **kwargs)      # Altrimenti esegui la funzione
    return decorated

# Linea 17-21: DECORATORE PER RICHIEDERE PRIVILEGI ADMIN
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Controlla se loggato E se ruolo è admin
        if 'username' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Autorizzazione admin richiesta'}), 403
        return f(*args, **kwargs)
    return decorated