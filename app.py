from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
from datetime import datetime
from src.auth import login_required, admin_required, USERS
from src.azure_monitor import (
    start_monitoring, stop_monitoring, get_monitoring_status,
    restart_vm, start_vm, stop_vm, get_manual_operations, get_vm_states
)

app = Flask(__name__)
app.secret_key = 'velocloudix-secret-2024'
DB_PATH = 'velocloudix.db'

# === ROTTE PRINCIPALI ===
@app.route('/')
def index():
    if 'username' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            session['role'] = USERS[username]['role']
            return redirect('/dashboard')
        return render_template('login.html', error='Credenziali non valide')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ultimi stati VM
    cursor.execute('''
        SELECT node_id, status, timestamp 
        FROM monitoring_log 
        WHERE (node_id, timestamp) IN (
            SELECT node_id, MAX(timestamp) 
            FROM monitoring_log 
            GROUP BY node_id
        )
    ''')
    node_statuses = {row[0]: row for row in cursor.fetchall()}
    
    # VM Azure dalla configurazione
    from src.azure_config import AZURE_CONFIG
    azure_vms = AZURE_CONFIG["vms"]
    
    nodes_with_status = []
    for vm in azure_vms:
        vm_name = vm["name"]
        status_data = node_statuses.get(vm_name, [vm_name, 'unknown', None])
        nodes_with_status.append({
            'name': vm_name,
            'display_name': vm["display_name"],
            'status': status_data[1],
            'timestamp': status_data[2]
        })
    
    # Log recenti
    cursor.execute('SELECT node_id, timestamp, status, action_taken FROM monitoring_log ORDER BY timestamp DESC LIMIT 20')
    recent_events = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html',
                         nodes=nodes_with_status,
                         recent_events=recent_events,
                         monitoring_status=get_monitoring_status(),
                         username=session['username'],
                         azure_available=True)

# === API MONITORAGGIO ===
@app.route('/api/start_monitoring', methods=['POST'])
@admin_required
def api_start_monitoring():
    start_monitoring()
    return jsonify({'status': 'success', 'message': 'Monitoraggio avviato'})

@app.route('/api/stop_monitoring', methods=['POST'])
@admin_required
def api_stop_monitoring():
    stop_monitoring()
    return jsonify({'status': 'success', 'message': 'Monitoraggio fermato'})

# === API CONTROLLI VM ===
@app.route('/api/vm/<vm_name>/restart', methods=['POST'])
@admin_required
def api_restart_vm(vm_name):
    success, message = restart_vm(vm_name)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO monitoring_log (node_id, status, action_taken) VALUES (?, ?, ?)',
                  (vm_name, 'unknown', f'manual_restart: {message}'))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success' if success else 'error', 'message': message})

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

@app.route('/api/vm/<vm_name>/operations')
@login_required
def api_vm_operations(vm_name):
    operations = get_manual_operations(vm_name)
    return jsonify({'operations': list(operations.values())})

@app.route('/api/logs')
@login_required
def api_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT node_id, timestamp, status, action_taken FROM monitoring_log ORDER BY timestamp DESC LIMIT 50')
    logs = [{'node_id': row[0], 'timestamp': row[1], 'status': row[2], 'action_taken': row[3]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

if __name__ == '__main__':
    from src.database import init_database
    init_database()
    print("🚀 VeloCloudiX avviato: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)