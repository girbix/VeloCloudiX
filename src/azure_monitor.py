# src/azure_monitor.py
"""
Sistema di monitoraggio per Azure VM REALI con controlli manuali
"""

import time
import threading
from datetime import datetime
import sqlite3
import os
from azure.core.exceptions import ResourceNotFoundError

# Importa la configurazione
from azure_config import AZURE_CONFIG, get_azure_credentials

# Import Azure SDK
from azure.mgmt.compute import ComputeManagementClient

# Configurazione
class Config:
    POLLING_INTERVAL = 30  # secondi
    NODES = AZURE_CONFIG["vms"]
    ADMIN_EMAIL = "liman.mani@edu-its.it"

# Percorso database
DB_PATH = os.path.join(os.path.dirname(__file__), 'velocloudix.db')

class AzureVMController:
    """Controller per gestire Azure VM reali"""
    
    def __init__(self):
        print("🔧 Inizializzazione Azure VM Controller...")
        self.credentials = get_azure_credentials()
        self.compute_client = ComputeManagementClient(
            self.credentials, 
            AZURE_CONFIG["subscription_id"]
        )
        print("✅ Azure VM Controller pronto!")
    
    def get_vm_status(self, vm_config):
        """Ottiene lo stato REALE di una VM Azure"""
        try:
            # Ottieni l'istanza della VM
            vm = self.compute_client.virtual_machines.get(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            # Ottieni lo stato dell'istanza
            instance_view = self.compute_client.virtual_machines.instance_view(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            # Cerca lo stato di power
            for status in instance_view.statuses:
                if status.code.startswith('PowerState'):
                    power_state = status.code
                    if 'running' in power_state.lower():
                        return 'running'
                    elif 'stopped' in power_state.lower():
                        return 'stopped'
                    elif 'deallocated' in power_state.lower():
                        return 'stopped'
                    else:
                        return 'unknown'
            
            return 'unknown'
            
        except ResourceNotFoundError:
            return 'not_found'
        except Exception as e:
            print(f"❌ Errore controllo VM {vm_config['name']}: {e}")
            return 'error'
    
    def start_vm(self, vm_config):
        """Avvia una VM Azure"""
        try:
            print(f"🔄 Avvio VM: {vm_config['name']}")
            
            async_start = self.compute_client.virtual_machines.begin_start(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            async_start.wait()
            print(f"✅ VM avviata: {vm_config['name']}")
            return True, "VM avviata con successo"
            
        except Exception as e:
            error_msg = f"Errore avvio VM: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def restart_vm(self, vm_config):
        """Riavvia una VM Azure"""
        try:
            print(f"🔄 Riavvio VM: {vm_config['name']}")
            
            async_restart = self.compute_client.virtual_machines.begin_restart(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            async_restart.wait()
            print(f"✅ VM riavviata: {vm_config['name']}")
            return True, "VM riavviata con successo"
            
        except Exception as e:
            error_msg = f"Errore riavvio VM: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def stop_vm(self, vm_config):
        """Arresta una VM Azure"""
        try:
            print(f"🛑 Arresto VM: {vm_config['name']}")
            
            async_stop = self.compute_client.virtual_machines.begin_power_off(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            async_stop.wait()
            print(f"✅ VM arrestata: {vm_config['name']}")
            return True, "VM arrestata con successo"
            
        except Exception as e:
            error_msg = f"Errore arresto VM: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

class MonitorService:
    """Servizio di monitoraggio con controlli manuali"""
    
    def __init__(self):
        self.azure_controller = AzureVMController()
        self.is_monitoring = False
        self.monitor_thread = None
        self.manual_operations = {}  # Traccia operazioni manuali
        self.vm_states = {}  # Cache stati VM
    
    def start_monitoring(self):
        """Avvia il monitoraggio"""
        if self.is_monitoring:
            print("⚠️ Monitoraggio già in esecuzione")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✅ Servizio di monitoraggio AVVIATO")
        
        # Log iniziale
        self._log_event("system", "running", "monitoring_started", "Monitoraggio VM Azure avviato")
    
    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 Servizio di monitoraggio FERMATO")
        
        # Log finale
        self._log_event("system", "stopped", "monitoring_stopped", "Monitoraggio VM Azure fermato")
    
    # === CONTROLLI MANUALI ===
    
    def restart_vm(self, vm_name):
        """Riavvia una VM specifica (chiamata manuale)"""
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, f"VM {vm_name} non trovata"
        
        # Registra operazione manuale
        operation_id = f"manual_restart_{vm_name}_{int(time.time())}"
        self.manual_operations[operation_id] = {
            'type': 'restart',
            'vm_name': vm_name,
            'status': 'in_progress',
            'start_time': datetime.now(),
            'message': 'Riavvio manuale in corso...',
            'manual': True
        }
        
        # Esegui il riavvio
        success, message = self.azure_controller.restart_vm(vm_config)
        
        # Aggiorna stato operazione
        if success:
            self.manual_operations[operation_id].update({
                'status': 'completed',
                'message': 'Riavvio manuale completato',
                'end_time': datetime.now()
            })
            # Aggiorna cache stato
            self.vm_states[vm_name] = 'running'
        else:
            self.manual_operations[operation_id].update({
                'status': 'failed', 
                'message': message,
                'end_time': datetime.now()
            })
        
        return success, message
    
    def start_vm(self, vm_name):
        """Avvia una VM specifica (chiamata manuale)"""
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, f"VM {vm_name} non trovata"
        
        operation_id = f"manual_start_{vm_name}_{int(time.time())}"
        self.manual_operations[operation_id] = {
            'type': 'start',
            'vm_name': vm_name,
            'status': 'in_progress',
            'start_time': datetime.now(),
            'message': 'Avvio manuale in corso...',
            'manual': True
        }
        
        success, message = self.azure_controller.start_vm(vm_config)
        
        if success:
            self.manual_operations[operation_id].update({
                'status': 'completed',
                'message': 'Avvio manuale completato',
                'end_time': datetime.now()
            })
            self.vm_states[vm_name] = 'running'
        else:
            self.manual_operations[operation_id].update({
                'status': 'failed', 
                'message': message,
                'end_time': datetime.now()
            })
        
        return success, message
    
    def stop_vm(self, vm_name):
        """Arresta una VM specifica (chiamata manuale)"""
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, f"VM {vm_name} non trovata"
        
        operation_id = f"manual_stop_{vm_name}_{int(time.time())}"
        self.manual_operations[operation_id] = {
            'type': 'stop',
            'vm_name': vm_name,
            'status': 'in_progress',
            'start_time': datetime.now(),
            'message': 'Arresto manuale in corso...',
            'manual': True
        }
        
        success, message = self.azure_controller.stop_vm(vm_config)
        
        if success:
            self.manual_operations[operation_id].update({
                'status': 'completed',
                'message': 'Arresto manuale completato',
                'end_time': datetime.now()
            })
            self.vm_states[vm_name] = 'stopped'
        else:
            self.manual_operations[operation_id].update({
                'status': 'failed', 
                'message': message,
                'end_time': datetime.now()
            })
        
        return success, message
    
    def get_manual_operations(self, vm_name=None):
        """Ottiene le operazioni manuali"""
        if vm_name:
            return {k: v for k, v in self.manual_operations.items() 
                   if v['vm_name'] == vm_name and v.get('manual')}
        else:
            return {k: v for k, v in self.manual_operations.items() 
                   if v.get('manual')}
    
    def get_vm_states(self):
        """Ottiene gli stati correnti delle VM"""
        return self.vm_states.copy()
    
    # === METODI PRIVATI ===
    
    def _get_vm_config(self, vm_name):
        """Trova la configurazione di una VM per nome"""
        for vm in Config.NODES:
            if vm["name"] == vm_name:
                return vm
        return None
    
    def _monitor_loop(self):
        """Loop principale di monitoraggio"""
        cycle_count = 0
        
        while self.is_monitoring:
            try:
                cycle_count += 1
                print(f"\n🎯 CICLO DI MONITORAGGIO #{cycle_count}")
                self._check_all_vms()
                time.sleep(Config.POLLING_INTERVAL)
            except Exception as e:
                print(f"❌ Errore nel loop: {e}")
                time.sleep(5)
    
    def _check_all_vms(self):
        """Controlla tutte le VM Azure"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        for vm_config in Config.NODES:
            vm_name = vm_config["name"]
            display_name = vm_config["display_name"]
            
            try:
                # Controlla stato REALE della VM
                status = self.azure_controller.get_vm_status(vm_config)
                
                # Aggiorna cache
                self.vm_states[vm_name] = status
                
                # Log stato
                self._log_event(vm_name, status, "checked", f"VM: {display_name}")
                
                print(f"🔍 {display_name} ({vm_name}): {status.upper()}")
                
                # Gestione VM spenta (solo se non è un'operazione manuale recente)
                if status == 'stopped':
                    # Controlla se è un arresto manuale recente
                    recent_manual_stop = any(
                        op['type'] == 'stop' and op['status'] == 'completed' 
                        and (datetime.now() - op['end_time']).total_seconds() < 300
                        for op in self.get_manual_operations(vm_name).values()
                    )
                    
                    if not recent_manual_stop:
                        print(f"🚨 VM SPENTA NON PROGRAMMATA: {display_name}")
                        self._log_event(vm_name, status, "unexpected_stop", f"VM {display_name} spenta inaspettatamente")
                    else:
                        print(f"ℹ️  VM SPENTA (MANUALE): {display_name}")
                        
            except Exception as e:
                error_msg = f"Errore controllo {vm_name}: {str(e)}"
                print(f"❌ {error_msg}")
                self._log_event(vm_config["name"], "unknown", "check_failed", error_msg)
    
    def _log_event(self, vm_name, status, action_taken, notes=None):
        """Registra evento nel database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO monitoring_log (node_id, status, action_taken, notes)
                VALUES (?, ?, ?, ?)
            ''', (vm_name, status, action_taken, notes))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Errore DB: {e}")

# Istanza globale
monitor_service = MonitorService()

# Funzioni per web app
def start_monitoring():
    monitor_service.start_monitoring()

def stop_monitoring():
    monitor_service.stop_monitoring()

def get_monitoring_status():
    return monitor_service.is_monitoring

def restart_vm(vm_name):
    return monitor_service.restart_vm(vm_name)

def start_vm(vm_name):
    return monitor_service.start_vm(vm_name)

def stop_vm(vm_name):
    return monitor_service.stop_vm(vm_name)

def get_manual_operations(vm_name=None):
    return monitor_service.get_manual_operations(vm_name)

def get_vm_states():
    return monitor_service.get_vm_states()

# Test
if __name__ == "__main__":
    print("🧪 TEST - Sistema di monitoraggio con controlli manuali")
    
    # Test connessione Azure
    controller = AzureVMController()
    
    print("🔍 Controllo stato VM...")
    for vm in Config.NODES:
        status = controller.get_vm_status(vm)
        print(f"   {vm['display_name']}: {status}")
    
    start_monitoring()
    
    try:
        # Test per 2 minuti
        for i in range(4):
            if monitor_service.is_monitoring:
                print(f"⏱️  Ciclo {i+1}/4 - Controlla l'interfaccia web!")
                time.sleep(30)
            else:
                break
    except KeyboardInterrupt:
        pass
    finally:
        stop_monitoring()