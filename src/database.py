import sqlite3
import os

DB_PATH = 'velocloudix.db'

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            action_taken TEXT
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_node_time ON monitoring_log (node_id, timestamp DESC)')
    conn.commit()
    conn.close()
    print(" Database inizializzato")