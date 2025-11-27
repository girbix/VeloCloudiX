# src/test_monitor.py
"""
Script per testare il sistema di monitoraggio avanzato
"""

from local_monitor import monitor_service, Config
import time
import sqlite3
import os

def test_monitor_system():
    print(" TEST SISTEMA DI MONITORAGGIO AVANZATO")
    print("=" * 50)
    
    # 1. Test configurazione
    print("1.  Configurazione nodi:")
    for i, node in enumerate(Config.NODES, 1):
        print(f"   {i}. {node['resource_group']}/{node['vm_name']}")
        print(f"      Owner: {node['owner_email']}")
        print(f"      Auto-restart: {node['auto_restart']}")
    
    # 2. Avvia monitoraggio
    print("\n2. 🚀 Avvio monitoraggio...")
    monitor_service.start_monitoring()
    
    # 3. Monitora per 2 minuti
    print("\n3. ⏱️  Monitoraggio in corso (2 minuti)...")
    print("   Guarda i log sopra per eventi in tempo reale!")
    
    try:
        for minute in range(2):
            print(f"\n  Minuto {minute + 1}/2 - Controllo database...")
            
            # Controlla il database
            db_path = os.path.join(os.path.dirname(__file__), 'velocloudix.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM monitoring_log 
                WHERE timestamp > datetime('now', '-5 minutes')
                GROUP BY status
            ''')
            
            stats = cursor.fetchall()
            print("Eventi recenti:")
            for status, count in stats:
                print(f"      - {status}: {count}")
            
            cursor.execute('''
                SELECT node_id, status, action_taken, timestamp
                FROM monitoring_log 
                WHERE action_taken LIKE '%restart%' OR action_taken LIKE '%fail%'
                ORDER BY timestamp DESC 
                LIMIT 3
            ''')
            
            critical_events = cursor.fetchall()
            if critical_events:
                print(" Eventi critici recenti:")
                for event in critical_events:
                    print(f"      - {event[0]}: {event[1]} ({event[2]})")
            
            conn.close()
            
            time.sleep(60)  # Aspetta 1 minuto
            
    except KeyboardInterrupt:
        print("\n  Test interrotto dall'utente")
    
    finally:
        # 4. Ferma monitoraggio
        print("\n4. Arresto monitoraggio...")
        monitor_service.stop_monitoring()
        
        # Statistiche finali
        db_path = os.path.join(os.path.dirname(__file__), 'velocloudix.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                SUM(CASE WHEN status = 'stopped' THEN 1 ELSE 0 END) as stopped_events,
                SUM(CASE WHEN action_taken LIKE '%restart%' THEN 1 ELSE 0 END) as restart_attempts,
                SUM(CASE WHEN action_taken LIKE '%fail%' THEN 1 ELSE 0 END) as failed_actions
            FROM monitoring_log 
            WHERE timestamp > datetime('now', '-10 minutes')
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        print("\n STATISTICHE FINALI TEST:")
        print(f"    Eventi totali: {stats[0]}")
        print(f"    VM spente: {stats[1]}")
        print(f"    Tentativi riavvio: {stats[2]}")
        print(f"    Azioni fallite: {stats[3]}")

if __name__ == "__main__":
    test_monitor_system()