"""
Gestione della cache degli stati VM e log nel database
"""

import sqlite3
import os
from datetime import datetime

class VMStatusManager:
    """Gestisce la cache degli stati VM e il logging nel database"""
    
    def __init__(self, db_path='velocloudix.db'):
        self.db_path = db_path
        self.vm_states = {}  # Cache stati VM per performance
    
    def update_vm_status(self, vm_name, status):
        """Aggiorna lo stato di una VM nella cache"""
        self.vm_states[vm_name] = status
        return status
    
    def get_vm_status(self, vm_name):
        """Ottiene lo stato di una VM dalla cache"""
        return self.vm_states.get(vm_name, 'unknown')  # Default 'unknown' se non trovato
    
    def get_all_states(self):
        """Ottiene tutti gli stati dalla cache"""
        return self.vm_states.copy()  # Restituisce copia per sicurezza
    
    def log_event(self, vm_name, status, action_taken, notes=None):
        """Registra un evento nel database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Inserisce record nel log monitoraggio
            cursor.execute('''
                INSERT INTO monitoring_log (node_id, status, action_taken, notes)
                VALUES (?, ?, ?, ?)
            ''', (vm_name, status, action_taken, notes))
            
            conn.commit()
            conn.close()
            print(f"Log registrato: {vm_name} - {action_taken}")
            
        except Exception as e:
            print(f"Errore DB durante log: {e}")
    
    def log_auto_restart_attempt(self, vm_name, display_name, success, error_message=None):
        """Log specializzato per tentativi di riavvio automatico"""
        if success:
            self.log_event(vm_name, 'running', 'auto_restart_success', 
                          f'Riavvio automatico riuscito per {display_name}')
        else:
            self.log_event(vm_name, 'stopped', 'auto_restart_failed', 
                          f'Riavvio automatico fallito: {error_message}')