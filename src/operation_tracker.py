"""
Sistema di tracciamento per operazioni manuali e automatiche
Gestisce lo stato delle operazioni in corso
"""

import time
from datetime import datetime

class OperationTracker:
    """Traccia lo stato delle operazioni manuali e automatiche"""
    
    def __init__(self):
        self.manual_operations = {}  # Operazioni manuali utente
        self.auto_operations = {}    # Operazioni automatiche sistema
    
    def start_manual_operation(self, operation_type, vm_name):
        """Registra l'inizio di un'operazione manuale"""
        operation_id = f"manual_{operation_type}_{vm_name}_{int(time.time())}"
        
        self.manual_operations[operation_id] = {
            'type': operation_type,
            'vm_name': vm_name,
            'status': 'in_progress',      # Stato iniziale
            'start_time': datetime.now(), # Timestamp inizio
            'message': f'{operation_type.capitalize()} manuale in corso...',
            'manual': True                # Flag operazione manuale
        }
        
        return operation_id
    
    def complete_operation(self, operation_id, success, message):
        """Completa un'operazione con esito"""
        if operation_id in self.manual_operations:
            operation = self.manual_operations[operation_id]
            operation.update({
                'status': 'completed' if success else 'failed', # Aggiorna stato
                'message': message,                             # Messaggio risultato
                'end_time': datetime.now()                      # Timestamp fine
            })
    
    def get_operations_for_vm(self, vm_name=None):
        """Ottiene operazioni per una VM specifica o tutte"""
        if vm_name:
            # Filtra per VM specifica e solo operazioni manuali
            return {k: v for k, v in self.manual_operations.items() 
                   if v['vm_name'] == vm_name and v.get('manual')}
        else:
            # Restituisce tutte le operazioni manuali
            return {k: v for k, v in self.manual_operations.items() 
                   if v.get('manual')}
    
    def has_recent_manual_stop(self, vm_name, minutes=5):
        """Verifica se c'è stato un arresto manuale recente"""
        current_time = datetime.now()
        
        for op in self.manual_operations.values():
            # Controlla se è un arresto manuale completato recentemente
            if (op['vm_name'] == vm_name and 
                op['type'] == 'stop' and 
                op['status'] == 'completed' and
                'end_time' in op and
                (current_time - op['end_time']).total_seconds() < minutes * 60):
                return True
        return False