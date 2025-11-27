import sqlite3
import os

DB_PATH = 'velocloudix.db'  # Nome file database

# Linea 6-25: INIZIALIZZAZIONE DATABASE
def init_database():
    conn = sqlite3.connect(DB_PATH)  # Crea/connette al database
    cursor = conn.cursor()           # Crea cursore per eseguire query
    
    # Crea tabella monitoring_log se non esiste
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  # ID autoincrementale
            node_id TEXT NOT NULL,                 # Nome della VM
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  # Data/ora automatica
            status TEXT NOT NULL,                  # Stato (running/stopped/ecc.)
            action_taken TEXT                      # Azione eseguita
        )
    ''')
    
    # Crea indice per velocizzare le query per node_id e timestamp
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_node_time ON monitoring_log (node_id, timestamp DESC)')
    conn.commit()  # Salva le modifiche
    conn.close()   # Chiude connessione
    print("✅ Database inizializzato")