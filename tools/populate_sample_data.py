# UTILE per demo quando Azure non è disponibile
import sqlite3
from datetime import datetime, timedelta
import random

def create_sample_data():
    conn = sqlite3.connect('velocloudix.db')
    cursor = conn.cursor()
    
    # Crea dati di esempio per testing
    nodes = ['vm-web-server-01', 'vm-database-01']
    for i in range(20):
        node = random.choice(nodes)
        status = random.choice(['running', 'stopped', 'unknown'])
        cursor.execute('''
            INSERT INTO monitoring_log (node_id, status, action_taken)
            VALUES (?, ?, ?)
        ''', (node, status, 'sample_data'))
    
    conn.commit()
    conn.close()
    print(" Dati demo creati")

if __name__ == "__main__":
    create_sample_data()