from functools import wraps
from flask import session, redirect, url_for, jsonify

USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'operatore': {'password': 'operatore123', 'role': 'operator'}
}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Autorizzazione admin richiesta'}), 403
        return f(*args, **kwargs)
    return decorated