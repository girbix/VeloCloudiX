# src/populate_sample_data.py
import sqlite3
import os
from datetime import datetime, timedelta
import random

def populate_sample_data():
    db_path = os.path.join(os.path.dirname(__file__), 'velocloudix.db')
    
    print("📊 Popolamento database con dati di esempio...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Conta log esistenti
        cursor.execute("SELECT COUNT(*) FROM monitoring_log")
        existing_logs = cursor.fetchone()[0]
        print(f"📝 Log esistenti: {existing_logs}")
        
        if existing_logs < 10:  # Solo se ci sono pochi dati
            print("➕ Aggiunta dati di esempio...")
            
            nodes = [
                'rg-prod/web-server-01',
                'rg-prod/db-server-01', 
                'rg-dev/test-server-01',
                'rg-staging/app-server-01'
            ]
            
            statuses = ['running', 'stopped', 'unknown']
            actions = ['checked', 'restart_attempted', 'alert_sent', 'monitored']
            
            # Crea dati per gli ultimi 2 giorni
            for days_ago in range(2, -1, -1):
                base_time = datetime.now() - timedelta(days=days_ago)
                
                for hour in range(0, 24, 4):  # Ogni 4 ore
                    timestamp = base_time.replace(hour=hour, minute=0, second=0)
                    
                    for node in nodes:
                        status = random.choice(statuses)
                        action = random.choice(actions)
                        
                        notes = None
                        if status == 'stopped':
                            notes = 'VM spenta - richiesto intervento'
                        elif status == 'unknown':
                            notes = 'Stato non determinabile'
                        
                        cursor.execute('''
                            INSERT INTO monitoring_log (node_id, timestamp, status, action_taken, notes)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (node, timestamp, status, action, notes))
            
            conn.commit()
            print("✅ Dati di esempio aggiunti!")
        
        # Statistiche finali
        cursor.execute("SELECT COUNT(*) FROM monitoring_log")
        total_logs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT node_id) FROM monitoring_log")
        unique_nodes = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM monitoring_log 
            GROUP BY status
        ''')
        status_stats = cursor.fetchall()
        
        print(f"\n📊 DATABASE COMPLETO:")
        print(f"   📝 Log totali: {total_logs}")
        print(f"   🔧 Nodi unici: {unique_nodes}")
        print(f"   📈 Statistiche stato:")
        for status, count in status_stats:
            print(f"      - {status}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    populate_sample_data()