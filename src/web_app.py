# src/web_app.py
"""
Web App Flask per VeloCloudiX - Versione COMPLETA con Azure VM REALI e controlli manuali
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import os
from datetime import datetime
import json

# Inizializza l'app Flask
app = Flask(__name__)
app.secret_key = 'velocloudix-local-dev-secret-key-2024'

# Percorso del database
DB_PATH = os.path.join(os.path.dirname(__file__), 'velocloudix.db')

# Utenti per il login
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'operatore': {'password': 'operatore123', 'role': 'operator'},
    'test': {'password': 'test123', 'role': 'operator'}
}

# ========== CARICAMENTO SISTEMA DI MONITORAGGIO AZURE ==========
try:
    from azure_monitor import start_monitoring, stop_monitoring, get_monitoring_status, restart_vm, start_vm, stop_vm, get_manual_operations, get_vm_states
    AZURE_MONITOR_AVAILABLE = True
    print("✅ Sistema di monitoraggio Azure VM caricato")
except ImportError as e:
    print(f"⚠️ Monitor Azure non disponibile: {e}")
    # Fallback al monitor semplice
    AZURE_MONITOR_AVAILABLE = False
    monitoring_status = False
    
    def start_monitoring():
        global monitoring_status
        monitoring_status = True
        print("✅ Monitoraggio base avviato")
    
    def stop_monitoring():
        global monitoring_status  
        monitoring_status = False
        print("🛑 Monitoraggio base fermato")
    
    def get_monitoring_status():
        global monitoring_status
        return monitoring_status
    
    # Funzioni placeholder per Azure
    def restart_vm(vm_name):
        return False, "Sistema Azure non disponibile"
    
    def start_vm(vm_name):
        return False, "Sistema Azure non disponibile"
    
    def stop_vm(vm_name):
        return False, "Sistema Azure non disponibile"
    
    def get_manual_operations(vm_name=None):
        return {}
    
    def get_vm_states():
        return {}

# ========== FUNZIONI DATABASE ==========

def init_database():
    """Inizializza il database se non esiste"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabella utenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            pwd_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabella storico monitoraggio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('running','stopped','unknown', 'not_found', 'error')) NOT NULL,
            action_taken TEXT,
            notes TEXT
        )
    ''')
    
    # Inserisci utenti demo se non esistono
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO users (username, email, pwd_hash)
            VALUES (?, ?, ?)
        ''', [
            ('admin', 'admin@velocloudix.com', 'admin123_hash'),
            ('operatore', 'operatore@velocloudix.com', 'operatore456_hash')
        ])
        print("✅ Utenti demo inseriti")
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Restituisce una connessione al database"""
    return sqlite3.connect(DB_PATH)

def get_azure_vms():
    """Ottiene la lista delle VM Azure dalla configurazione"""
    try:
        from azure_config import AZURE_CONFIG
        return AZURE_CONFIG["vms"]
    except ImportError:
        return [
            {"name": "vm-web-server-01", "display_name": "Web Server", "resource_group": "VeloCloudix"},
            {"name": "vm-database-01", "display_name": "Database Server", "resource_group": "VeloCloudix"},
            {"name": "vm-test-01", "display_name": "Test Environment", "resource_group": "VeloCloudix"}
        ]

# ========== DECORATORI ==========

def login_required(f):
    """Decoratore per richiedere il login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decoratore per richiedere privilegi di admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Autorizzazione richiesta'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== ROTTE PRINCIPALI ==========

@app.route('/')
def index():
    """Pagina principale"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina di login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            session['role'] = USERS[username]['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenziali non valide')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principale"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ottieni le VM Azure
    azure_vms = get_azure_vms()
    
    # Ultimo stato di ogni nodo
    cursor.execute('''
        SELECT ml.node_id, ml.status, ml.timestamp, ml.action_taken, ml.notes
        FROM monitoring_log ml
        INNER JOIN (
            SELECT node_id, MAX(timestamp) as max_ts
            FROM monitoring_log
            GROUP BY node_id
        ) latest ON ml.node_id = latest.node_id AND ml.timestamp = latest.max_ts
        ORDER BY ml.node_id
    ''')
    
    node_statuses = {row[0]: row for row in cursor.fetchall()}
    
    # Combina dati Azure con stati dal database
    nodes_with_status = []
    for vm in azure_vms:
        vm_name = vm["name"]
        if vm_name in node_statuses:
            status_data = node_statuses[vm_name]
            nodes_with_status.append({
                'name': vm_name,
                'display_name': vm["display_name"],
                'status': status_data[1],
                'timestamp': status_data[2],
                'action_taken': status_data[3],
                'notes': status_data[4]
            })
        else:
            nodes_with_status.append({
                'name': vm_name,
                'display_name': vm["display_name"],
                'status': 'unknown',
                'timestamp': None,
                'action_taken': None,
                'notes': 'Nessun dato di monitoraggio'
            })
    
    # Log recenti
    cursor.execute('''
        SELECT node_id, timestamp, status, action_taken, notes
        FROM monitoring_log 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''')
    
    recent_events = cursor.fetchall()
    
    # Statistiche
    cursor.execute('''
        SELECT 
            COUNT(*) as total_checks
        FROM monitoring_log
        WHERE timestamp > datetime('now', '-1 day')
    ''')
    
    stats_result = cursor.fetchone()
    stats = stats_result if stats_result else (0,)
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         nodes=nodes_with_status,
                         recent_events=recent_events,
                         stats=stats,
                         monitoring_status=get_monitoring_status(),
                         username=session['username'],
                         now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         azure_available=AZURE_MONITOR_AVAILABLE)

# ========== API PER MONITORAGGIO ==========

@app.route('/api/start_monitoring', methods=['POST'])
@login_required
@admin_required
def api_start_monitoring():
    """API per avviare il monitoraggio"""
    try:
        start_monitoring()
        return jsonify({'status': 'success', 'message': 'Monitoraggio avviato'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop_monitoring', methods=['POST'])
@login_required
@admin_required
def api_stop_monitoring():
    """API per fermare il monitoraggio"""
    try:
        stop_monitoring()
        return jsonify({'status': 'success', 'message': 'Monitoraggio fermato'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/monitoring_status')
@login_required
def api_monitoring_status():
    """API per lo stato del monitoraggio"""
    return jsonify({'monitoring': get_monitoring_status()})

@app.route('/api/logs')
@login_required
def api_logs():
    """API per i log"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT node_id, timestamp, status, action_taken, notes
        FROM monitoring_log 
        ORDER BY timestamp DESC 
        LIMIT 100
    ''')
    
    logs = []
    for row in cursor.fetchall():
        logs.append({
            'node_id': row[0],
            'timestamp': row[1],
            'status': row[2],
            'action_taken': row[3],
            'notes': row[4]
        })
    
    cursor.close()
    conn.close()
    
    return jsonify(logs)

@app.route('/api/nodes/status')
@login_required
def api_nodes_status():
    """API per stato nodi"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ml.node_id, ml.status, ml.timestamp, ml.action_taken
        FROM monitoring_log ml
        INNER JOIN (
            SELECT node_id, MAX(timestamp) as max_ts
            FROM monitoring_log
            GROUP BY node_id
        ) latest ON ml.node_id = latest.node_id AND ml.timestamp = latest.max_ts
    ''')
    
    nodes_status = []
    for row in cursor.fetchall():
        nodes_status.append({
            'node_id': row[0],
            'status': row[1],
            'timestamp': row[2],
            'action_taken': row[3]
        })
    
    cursor.close()
    conn.close()
    
    return jsonify(nodes_status)

# ========== API PER GESTIONE VM AZURE ==========

@app.route('/api/vm/<vm_name>/restart', methods=['POST'])
@login_required
@admin_required
def api_restart_vm(vm_name):
    """API per riavviare una VM Azure MANUALMENTE"""
    if not AZURE_MONITOR_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Sistema Azure non disponibile'}), 500
    
    try:
        success, message = restart_vm(vm_name)
        
        # Log dell'operazione manuale
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO monitoring_log (node_id, status, action_taken, notes)
            VALUES (?, ?, ?, ?)
        ''', (vm_name, 'unknown', 'manual_restart', f"Riavvio manuale: {message}"))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success' if success else 'error', 
            'message': message
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vm/<vm_name>/start', methods=['POST'])
@login_required
@admin_required
def api_start_vm(vm_name):
    """API per avviare una VM Azure MANUALMENTE"""
    if not AZURE_MONITOR_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Sistema Azure non disponibile'}), 500
    
    try:
        success, message = start_vm(vm_name)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO monitoring_log (node_id, status, action_taken, notes)
            VALUES (?, ?, ?, ?)
        ''', (vm_name, 'unknown', 'manual_start', f"Avvio manuale: {message}"))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success' if success else 'error', 
            'message': message
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vm/<vm_name>/stop', methods=['POST'])
@login_required
@admin_required
def api_stop_vm(vm_name):
    """API per arrestare una VM Azure MANUALMENTE"""
    if not AZURE_MONITOR_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Sistema Azure non disponibile'}), 500
    
    try:
        success, message = stop_vm(vm_name)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO monitoring_log (node_id, status, action_taken, notes)
            VALUES (?, ?, ?, ?)
        ''', (vm_name, 'unknown', 'manual_stop', f"Arresto manuale: {message}"))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success' if success else 'error', 
            'message': message
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vm/<vm_name>/manual_operations')
@login_required
def api_manual_operations(vm_name):
    """API per le operazioni manuali di una VM"""
    if not AZURE_MONITOR_AVAILABLE:
        return jsonify({'operations': []})
    
    try:
        operations = get_manual_operations(vm_name)
        
        # Converti datetime a string per JSON
        serializable_ops = []
        for op_id, op_data in operations.items():
            serializable_op = op_data.copy()
            if 'start_time' in op_data and op_data['start_time']:
                serializable_op['start_time'] = op_data['start_time'].isoformat()
            if 'end_time' in op_data and op_data['end_time']:
                serializable_op['end_time'] = op_data['end_time'].isoformat()
            serializable_op['id'] = op_id
            serializable_ops.append(serializable_op)
        
        # Ordina per data (più recente prima)
        serializable_ops.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        return jsonify({'operations': serializable_ops})
    except Exception as e:
        return jsonify({'operations': [], 'error': str(e)})

@app.route('/api/vm/states')
@login_required
def api_vm_states():
    """API per gli stati correnti delle VM"""
    if not AZURE_MONITOR_AVAILABLE:
        return jsonify({'states': {}})
    
    try:
        states = get_vm_states()
        return jsonify({'states': states})
    except Exception as e:
        return jsonify({'states': {}, 'error': str(e)})

@app.route('/api/vm/list')
@login_required
def api_vm_list():
    """API per la lista delle VM Azure"""
    try:
        vms = get_azure_vms()
        
        # Aggiungi stato corrente per ogni VM
        conn = get_db_connection()
        cursor = conn.cursor()
        
        vm_list_with_status = []
        for vm in vms:
            cursor.execute('''
                SELECT status, timestamp 
                FROM monitoring_log 
                WHERE node_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (vm["name"],))
            
            result = cursor.fetchone()
            status = result[0] if result else 'unknown'
            timestamp = result[1] if result else None
            
            vm_list_with_status.append({
                'name': vm["name"],
                'display_name': vm["display_name"],
                'resource_group': vm["resource_group"],
                'status': status,
                'last_check': timestamp
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'vms': vm_list_with_status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== API PER STATISTICHE ==========

@app.route('/api/stats/overview')
@login_required
def api_stats_overview():
    """API per statistiche generali"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Statistiche generali
    cursor.execute('''
        SELECT 
            COUNT(*) as total_events,
            COUNT(DISTINCT node_id) as unique_vms,
            SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_events,
            SUM(CASE WHEN status = 'stopped' THEN 1 ELSE 0 END) as stopped_events,
            SUM(CASE WHEN action_taken LIKE '%restart%' THEN 1 ELSE 0 END) as restart_attempts
        FROM monitoring_log 
        WHERE timestamp > datetime('now', '-1 day')
    ''')
    
    stats = cursor.fetchone()
    
    # Eventi recenti per tipo
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM monitoring_log 
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY status
    ''')
    
    recent_stats = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'total_events_24h': stats[0],
        'unique_vms': stats[1],
        'running_events': stats[2],
        'stopped_events': stats[3],
        'restart_attempts': stats[4],
        'recent_stats': dict(recent_stats)
    })

# ========== GESTIONE ERRORI ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Risorsa non trovata'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Errore interno del server'}), 500

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Accesso negato'}), 403

# ========== AVVIO APPLICAZIONE ==========

if __name__ == '__main__':
    # Inizializza il database
    init_database()
    
    print("🚀 Avvio Web App VeloCloudiX con Azure VM...")
    print("📍 Accesso: http://localhost:5000")
    print("👤 Credenziali: admin / admin123  oppure  operatore / operatore123")
    
    if AZURE_MONITOR_AVAILABLE:
        print("✅ Sistema Azure VM ATTIVO - Monitoraggio VM reali disponibile")
    else:
        print("⚠️  Sistema Azure NON disponibile - Usando modalità simulazione")
    
    print("💡 Funzionalità disponibili:")
    print("   • Monitoraggio VM Azure in tempo reale")
    print("   • Riavvio/Start/Stop VM da interfaccia web")
    print("   • Tracking operazioni in tempo reale")
    print("   • Log completo e statistiche")
    
    app.run(debug=True, host='0.0.0.0', port=5000)