"""
Gestione database SQLite locale per VeloCloudiX
SQLite è perfetto per sviluppo: zero configurazione, file-based
"""

import sqlite3
import os
from datetime import datetime

# Percorso del database - lo salviamo nella cartella del progetto
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'velocloudix.db')

def init_database():
    """Inizializza il database e crea le tabelle se non esistono"""
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
            status TEXT CHECK(status IN ('running','stopped','unknown','not_found','error')) NOT NULL,
            action_taken TEXT,
            notes TEXT
        )
    ''')
    
    # Indice per performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_node_timestamp 
        ON monitoring_log (node_id, timestamp DESC)
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
        print("Utenti demo inseriti nel database")
    
    conn.commit()
    conn.close()
    print(f"Database inizializzato: {DB_PATH}")

def get_db_connection():
    """Restituisce una connessione al database SQLite"""
    return sqlite3.connect(DB_PATH)

def log_event(node_id, status, action_taken, notes=None):
    """Registra un evento nel database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO monitoring_log (node_id, status, action_taken, notes)
        VALUES (?, ?, ?, ?)
    ''', (node_id, status, action_taken, notes))
    
    conn.commit()
    conn.close()
    print(f"Evento registrato: {node_id} - {status}")

# Inizializza il database quando importi questo modulo
init_database()