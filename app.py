# Import di tutte le librerie necessarie
from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
from datetime import datetime
from src.auth import login_required, admin_required, USERS
from src.azure_monitor import (
    start_monitoring, stop_monitoring, get_monitoring_status,
    restart_vm, start_vm, stop_vm, get_manual_operations, get_vm_states
)

# Linea 1-8: INIZIALIZZAZIONE
# Creazione dell'app Flask e configurazione
app = Flask(__name__)
app.secret_key = 'velocloudix-secret-2024'  # Chiave per cifrare le sessioni
DB_PATH = 'velocloudix.db'  # Percorso del database SQLite

# Linea 11-18: ROTTA PRINCIPALE /
@app.route('/')
def index():
    # Se l'utente è già loggato (session contiene username)
    if 'username' in session:
        return redirect('/dashboard')  # Reindirizza alla dashboard
    return redirect('/login')  # Altrimenti alla login

# Linea 21-35: ROTTA LOGIN (GET e POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se il metodo è POST (form inviato)
    if request.method == 'POST':
        username = request.form['username']    # Prende username dal form
        password = request.form['password']    # Prende password dal form
        
        # Controlla se l'utente esiste e la password è corretta
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username                    # Salva username in session
            session['role'] = USERS[username]['role']        # Salva ruolo in session
            return redirect('/dashboard')                    # Reindirizza alla dashboard
        return render_template('login.html', error='Credenziali non valide')  # Se errore
    
    # Se metodo GET, mostra semplicemente la pagina login
    return render_template('login.html')

# Linea 38-41: ROTTA LOGOUT
@app.route('/logout')
def logout():
    session.clear()          # Cancella tutti i dati della sessione
    return redirect('/login') # Reindirizza al login

# Linea 44-85: DASHBOARD PRINCIPALE
@app.route('/dashboard')
@login_required  # Decoratore: richiede il login per accedere
def dashboard():
    # Connessione al database SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query per ottenere gli ultimi stati di ogni VM
    # La sottoquery seleziona l'ultimo timestamp per ogni node_id
    cursor.execute('''
        SELECT node_id, status, timestamp 
        FROM monitoring_log 
        WHERE (node_id, timestamp) IN (
            SELECT node_id, MAX(timestamp) 
            FROM monitoring_log 
            GROUP BY node_id
        )
    ''')
    # Crea un dizionario {node_id: [node_id, status, timestamp]} per accesso rapido
    node_statuses = {row[0]: row for row in cursor.fetchall()}
    
    # Importa la configurazione Azure per ottenere la lista delle VM
    from src.azure_config import AZURE_CONFIG
    azure_vms = AZURE_CONFIG["vms"]  # Lista delle VM da configurazione
    
    # Prepara i dati per il template
    nodes_with_status = []
    for vm in azure_vms:
        vm_name = vm["name"]
        # Se esiste uno stato nel DB, usalo, altrimenti 'unknown'
        status_data = node_statuses.get(vm_name, [vm_name, 'unknown', None])
        nodes_with_status.append({
            'name': vm_name,
            'display_name': vm["display_name"],  # Nome visualizzato
            'status': status_data[1],           # Stato (running/stopped/unknown)
            'timestamp': status_data[2]         # Timestamp ultimo check
        })
    
    # Query per ottenere gli eventi recenti (ultimi 20)
    cursor.execute('SELECT node_id, timestamp, status, action_taken FROM monitoring_log ORDER BY timestamp DESC LIMIT 20')
    recent_events = cursor.fetchall()  # Lista di tuple
    conn.close()  # Chiude la connessione al database
    
    # Renderizza il template dashboard con tutti i dati
    return render_template('dashboard.html',
                         nodes=nodes_with_status,        # Lista VM con stati
                         recent_events=recent_events,    # Eventi recenti
                         monitoring_status=get_monitoring_status(),  # Stato monitoraggio
                         username=session['username'],   # Nome utente loggato
                         azure_available=True)          # Flag Azure disponibile

# Linea 88-94: API PER AVVIARE MONITORAGGIO
@app.route('/api/start_monitoring', methods=['POST'])
@admin_required  # Solo gli admin possono avviare il monitoraggio
def api_start_monitoring():
    start_monitoring()  # Chiama la funzione del modulo azure_monitor
    return jsonify({'status': 'success', 'message': 'Monitoraggio avviato'})

# Linea 97-103: API PER FERMARE MONITORAGGIO
@app.route('/api/stop_monitoring', methods=['POST'])
@admin_required  # Solo admin possono fermare
def api_stop_monitoring():
    stop_monitoring()   # Ferma il monitoraggio
    return jsonify({'status': 'success', 'message': 'Monitoraggio fermato'})

# Linea 106-120: API PER RIAVVIARE VM
@app.route('/api/vm/<vm_name>/restart', methods=['POST'])
@admin_required  # Solo admin possono riavviare
def api_restart_vm(vm_name):
    # Chiama la funzione di riavvio e ottiene risultato
    success, message = restart_vm(vm_name)
    
    # Registra l'operazione nel database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO monitoring_log (node_id, status, action_taken) VALUES (?, ?, ?)',
                  (vm_name, 'unknown', f'manual_restart: {message}'))
    conn.commit()  # Salva le modifiche
    conn.close()   # Chiude connessione
    
    # Restituisce risultato come JSON
    return jsonify({'status': 'success' if success else 'error', 'message': message})

# Linea 123-137: API PER AVVIARE VM (simile a restart)
@app.route('/api/vm/<vm_name>/start', methods=['POST'])
@admin_required
def api_start_vm(vm_name):
    success, message = start_vm(vm_name)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO monitoring_log (node_id, status, action_taken) VALUES (?, ?, ?)',
                  (vm_name, 'unknown', f'manual_start: {message}'))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success' if success else 'error', 'message': message})

# Linea 140-154: API PER FERMARE VM (simile a restart)
@app.route('/api/vm/<vm_name>/stop', methods=['POST'])
@admin_required
def api_stop_vm(vm_name):
    success, message = stop_vm(vm_name)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO monitoring_log (node_id, status, action_taken) VALUES (?, ?, ?)',
                  (vm_name, 'unknown', f'manual_stop: {message}'))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success' if success else 'error', 'message': message})

# Linea 157-175: API PER OTTENERE OPERAZIONI MANUALI DI UNA VM
@app.route('/api/vm/<vm_name>/operations')
@login_required  # Richiede login ma non necessariamente admin
def api_vm_operations(vm_name):
    # Ottiene le operazioni manuali per la VM specificata
    operations = get_manual_operations(vm_name)
    
    # Converte in formato serializzabile per JSON
    serializable_ops = []
    for op_id, op_data in operations.items():
        serializable_op = op_data.copy()
        # Converte datetime in stringhe per JSON
        if 'start_time' in op_data and op_data['start_time']:
            serializable_op['start_time'] = op_data['start_time'].isoformat()
        if 'end_time' in op_data and op_data['end_time']:
            serializable_op['end_time'] = op_data['end_time'].isoformat()
        serializable_op['id'] = op_id
        serializable_ops.append(serializable_op)
    
    # Ordina per data (più recente prima)
    serializable_ops.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    return jsonify({'operations': serializable_ops})

# Linea 178-191: API PER OTTENERE I LOG
@app.route('/api/logs')
@login_required
def api_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Seleziona ultimi 50 eventi ordinati per data discendente
    cursor.execute('SELECT node_id, timestamp, status, action_taken FROM monitoring_log ORDER BY timestamp DESC LIMIT 50')
    # Converte le righe in dizionari per JSON
    logs = [{'node_id': row[0], 'timestamp': row[1], 'status': row[2], 'action_taken': row[3]} 
            for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)  # Restituisce come JSON

# Linea 194-200: AVVIO APPLICAZIONE
if __name__ == '__main__':
    from src.database import init_database
    init_database()  # Inizializza il database
    print("🚀 VeloCloudiX avviato: http://localhost:5000")
    # Avvia il server Flask
    app.run(debug=True, host='0.0.0.0', port=5000)  # debug=True per sviluppo