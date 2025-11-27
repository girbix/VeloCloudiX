# cleanup_database.py
"""
Script per pulire e ricreare il database in caso di errori
"""

import os
import sqlite3

def cleanup_database():
    db_path = 'velocloudix.db'
    
    # Rimuovi il file database esistente
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Database esistente rimosso")
    
    # Ricrea il database
    from src.database import init_database
    init_database()
    print("Nuovo database creato con successo")

if __name__ == "__main__":
    cleanup_database()