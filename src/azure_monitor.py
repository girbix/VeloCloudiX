"""
Sistema di monitoraggio principale per Azure VM
Coordina tutti i componenti del monitoraggio
Versione semplificata e modulare
"""

import time
import threading
from datetime import datetime

# Import dei moduli separati
from src.azure_controller import AzureVMController
from src.operation_tracker import OperationTracker
from src.vm_status_manager import VMStatusManager
from src.auto_recovery import AutoRecoverySystem
from src.azure_config import AZURE_CONFIG

# Configurazione
class Config:
    POLLING_INTERVAL = 30  # secondi tra un controllo e l'altro
    NODES = AZURE_CONFIG["vms"]  # Lista VM da configurazione

class MonitorService:
    """Servizio di monitoraggio principale - Coordina tutti i componenti"""
    
    def __init__(self):
        # Inizializza tutti i componenti
        self.azure_controller = AzureVMController()           # Comunicazione con Azure
        self.operation_tracker = OperationTracker()           # Tracciamento operazioni
        self.status_manager = VMStatusManager()               # Gestione stati e log
        self.auto_recovery = AutoRecoverySystem(              # Ripristino automatico
            self.azure_controller, 
            self.status_manager, 
            self.operation_tracker
        )
        
        self.is_monitoring = False    # Flag stato monitoraggio
        self.monitor_thread = None    # Riferimento al thread di monitoraggio
    
    def start_monitoring(self):
        """Avvia il monitoraggio"""
        if self.is_monitoring:
            print("Monitoraggio già in esecuzione")
            return
        
        self.is_monitoring = True
        # Crea thread separato per non bloccare l'applicazione principale
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Servizio di monitoraggio AVVIATO")
        
        # Log iniziale nel database
        self.status_manager.log_event("system", "running", "monitoring_started", 
                                    "Monitoraggio VM Azure avviato")
    
    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        self.is_monitoring = False  # Cambia flag per fermare il loop
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)  # Aspetta il thread (max 5 secondi)
        print("Servizio di monitoraggio FERMATO")
        
        # Log finale nel database
        self.status_manager.log_event("system", "stopped", "monitoring_stopped", 
                                    "Monitoraggio VM Azure fermato")
    
    # === CONTROLLI MANUALI ===
    
    def restart_vm(self, vm_name):
        """Riavvia una VM specifica (chiamata manuale)"""
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, f"VM {vm_name} non trovata"
        
        # Registra operazione manuale nel tracker
        op_id = self.operation_tracker.start_manual_operation('restart', vm_name)
        
        # Esegui il riavvio tramite Azure controller
        success, message = self.azure_controller.restart_vm(vm_config)
        
        # Aggiorna stato operazione nel tracker
        self.operation_tracker.complete_operation(op_id, success, message)
        
        # Aggiorna cache stato se riavvio riuscito
        if success:
            self.status_manager.update_vm_status(vm_name, 'running')
        
        return success, message
    
    def start_vm(self, vm_name):
        """Avvia una VM specifica (chiamata manuale)"""
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, f"VM {vm_name} non trovata"
        
        op_id = self.operation_tracker.start_manual_operation('start', vm_name)
        success, message = self.azure_controller.start_vm(vm_config)
        self.operation_tracker.complete_operation(op_id, success, message)
        
        if success:
            self.status_manager.update_vm_status(vm_name, 'running')
        
        return success, message
    
    def stop_vm(self, vm_name):
        """Arresta una VM specifica (chiamata manuale)"""
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, f"VM {vm_name} non trovata"
        
        op_id = self.operation_tracker.start_manual_operation('stop', vm_name)
        success, message = self.azure_controller.stop_vm(vm_config)
        self.operation_tracker.complete_operation(op_id, success, message)
        
        if success:
            self.status_manager.update_vm_status(vm_name, 'stopped')
        
        return success, message
    
    # === METODI PUBBLICI PER WEB APP ===
    
    def get_manual_operations(self, vm_name=None):
        """Ottiene le operazioni manuali per la web app"""
        return self.operation_tracker.get_operations_for_vm(vm_name)
    
    def get_vm_states(self):
        """Ottiene gli stati correnti delle VM per la web app"""
        return self.status_manager.get_all_states()
    
    def get_monitoring_status(self):
        """Ottiene lo stato del monitoraggio per la web app"""
        return self.is_monitoring
    
    # === METODI PRIVATI ===
    
    def _get_vm_config(self, vm_name):
        """Trova la configurazione di una VM per nome"""
        for vm in Config.NODES:
            if vm["name"] == vm_name:
                return vm
        return None  # Se VM non trovata
    
    def _monitor_loop(self):
        """Loop principale di monitoraggio - eseguito in thread separato"""
        cycle_count = 0
        
        while self.is_monitoring:  # Continua finché il flag è True
            try:
                cycle_count += 1
                print(f"CICLO DI MONITORAGGIO #{cycle_count}")
                self._check_all_vms()  # Controlla tutte le VM
                time.sleep(Config.POLLING_INTERVAL)  # Aspetta prima del prossimo ciclo
            except Exception as e:
                print(f"Errore nel loop di monitoraggio: {e}")
                time.sleep(5)  # Aspetta breve in caso di errore
    
    def _check_all_vms(self):
        """Controlla tutte le VM Azure configurate"""
        for vm_config in Config.NODES:
            vm_name = vm_config["name"]
            display_name = vm_config["display_name"]
            
            try:
                # Controlla stato REALE della VM da Azure
                previous_status = self.status_manager.get_vm_status(vm_name)  # Stato precedente dalla cache
                current_status = self.azure_controller.get_vm_status(vm_config)  # Stato attuale da Azure
                
                # Aggiorna cache con stato attuale
                self.status_manager.update_vm_status(vm_name, current_status)
                
                # Log stato normale nel database
                self.status_manager.log_event(vm_name, current_status, "checked", 
                                            f"VM: {display_name}")
                
                print(f"{display_name} ({vm_name}): {current_status.upper()}")
                
                # Gestione VM spenta con ripristino automatico
                if (current_status == 'stopped' and 
                    self.auto_recovery.should_handle_stopped_vm(vm_name)):
                    # VM spenta non programmata - attiva ripristino automatico
                    self.auto_recovery.handle_stopped_vm(vm_config, previous_status)
                    
                elif current_status == 'stopped':
                    # VM spenta manualmente - solo log informativo
                    print(f"VM SPENTA (MANUALE): {display_name}")
                    self.status_manager.log_event(vm_name, current_status, "expected_stop", 
                                                f"VM {display_name} spenta manualmente")
                        
            except Exception as e:
                # Gestione errori durante il controllo della VM
                error_msg = f"Errore controllo {vm_name}: {str(e)}"
                print(f"{error_msg}")
                self.status_manager.log_event(vm_name, "unknown", "check_failed", error_msg)

# Istanza globale del servizio di monitoraggio
monitor_service = MonitorService()

# === INTERFACCIA PER WEB APP ===
# Le seguenti funzioni forniscono un'interfaccia semplice per la web app
# Mantenendo compatibilità con il codice esistente

def start_monitoring():
    """Avvia il monitoraggio - interfaccia per web app"""
    monitor_service.start_monitoring()

def stop_monitoring():
    """Ferma il monitoraggio - interfaccia per web app"""
    monitor_service.stop_monitoring()

def get_monitoring_status():
    """Restituisce stato monitoraggio - interfaccia per web app"""
    return monitor_service.is_monitoring

def restart_vm(vm_name):
    """Riavvia una VM - interfaccia per web app"""
    return monitor_service.restart_vm(vm_name)

def start_vm(vm_name):
    """Avvia una VM - interfaccia per web app"""
    return monitor_service.start_vm(vm_name)

def stop_vm(vm_name):
    """Arresta una VM - interfaccia per web app"""
    return monitor_service.stop_vm(vm_name)

def get_manual_operations(vm_name=None):
    """Ottiene operazioni manuali - interfaccia per web app"""
    return monitor_service.get_manual_operations(vm_name)

def get_vm_states():
    """Ottiene stati VM - interfaccia per web app"""
    return monitor_service.get_vm_states()

# Test del sistema
if __name__ == "__main__":
    print("TEST - Sistema di monitoraggio modulare")
    start_monitoring()
    
    try:
        time.sleep(120)  # Test per 2 minuti
    except KeyboardInterrupt:
        pass
    finally:
        stop_monitoring()