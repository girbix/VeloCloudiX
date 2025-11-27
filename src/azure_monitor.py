import time
import threading
from datetime import datetime
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError

from .azure_config import AZURE_CONFIG, get_azure_credentials

class AzureVMController:
    def __init__(self):
        self.credentials = get_azure_credentials()
        self.compute_client = ComputeManagementClient(self.credentials, AZURE_CONFIG["subscription_id"])
    
    def get_vm_status(self, vm_config):
        try:
            instance_view = self.compute_client.virtual_machines.instance_view(
                vm_config["resource_group"], vm_config["name"]
            )
            for status in instance_view.statuses:
                if status.code.startswith('PowerState'):
                    if 'running' in status.code.lower():
                        return 'running'
                    elif 'stopped' in status.code.lower():
                        return 'stopped'
            return 'unknown'
        except ResourceNotFoundError:
            return 'not_found'
        except Exception as e:
            print(f" Errore VM {vm_config['name']}: {e}")
            return 'error'
    
    def restart_vm(self, vm_config):
        try:
            async_op = self.compute_client.virtual_machines.begin_restart(
                vm_config["resource_group"], vm_config["name"]
            )
            async_op.wait()
            return True, "VM riavviata"
        except Exception as e:
            return False, f"Errore: {str(e)}"
    
    def start_vm(self, vm_config):
        try:
            async_op = self.compute_client.virtual_machines.begin_start(
                vm_config["resource_group"], vm_config["name"]
            )
            async_op.wait()
            return True, "VM avviata"
        except Exception as e:
            return False, f"Errore: {str(e)}"
    
    def stop_vm(self, vm_config):
        try:
            async_op = self.compute_client.virtual_machines.begin_power_off(
                vm_config["resource_group"], vm_config["name"]
            )
            async_op.wait()
            return True, "VM arrestata"
        except Exception as e:
            return False, f"Errore: {str(e)}"

class MonitorService:
    def __init__(self):
        self.azure_controller = AzureVMController()
        self.is_monitoring = False
        self.monitor_thread = None
        self.manual_operations = {}
        self.vm_states = {}
    
    def start_monitoring(self):
        if self.is_monitoring:
            return
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(" Monitoraggio avviato")
    
    def stop_monitoring(self):
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print(" Monitoraggio fermato")
    
    def restart_vm(self, vm_name):
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, "VM non trovata"
        
        op_id = f"restart_{vm_name}_{int(time.time())}"
        self.manual_operations[op_id] = {
            'type': 'restart', 'vm_name': vm_name, 'status': 'in_progress',
            'start_time': datetime.now(), 'message': 'Riavvio in corso...'
        }
        
        success, message = self.azure_controller.restart_vm(vm_config)
        
        if success:
            self.manual_operations[op_id].update({'status': 'completed', 'message': 'Completato'})
            self.vm_states[vm_name] = 'running'
        else:
            self.manual_operations[op_id].update({'status': 'failed', 'message': message})
        
        return success, message
    
    def start_vm(self, vm_name):
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, "VM non trovata"
        
        success, message = self.azure_controller.start_vm(vm_config)
        if success:
            self.vm_states[vm_name] = 'running'
        return success, message
    
    def stop_vm(self, vm_name):
        vm_config = self._get_vm_config(vm_name)
        if not vm_config:
            return False, "VM non trovata"
        
        success, message = self.azure_controller.stop_vm(vm_config)
        if success:
            self.vm_states[vm_name] = 'stopped'
        return success, message
    
    def get_manual_operations(self, vm_name=None):
        if vm_name:
            return {k: v for k, v in self.manual_operations.items() if v['vm_name'] == vm_name}
        return self.manual_operations
    
    def get_vm_states(self):
        return self.vm_states.copy()
    
    def _get_vm_config(self, vm_name):
        for vm in AZURE_CONFIG["vms"]:
            if vm["name"] == vm_name:
                return vm
        return None
    
    def _monitor_loop(self):
        while self.is_monitoring:
            for vm_config in AZURE_CONFIG["vms"]:
                try:
                    status = self.azure_controller.get_vm_status(vm_config)
                    self.vm_states[vm_config["name"]] = status
                    print(f" {vm_config['display_name']}: {status}")
                except Exception as e:
                    print(f" Errore monitoraggio {vm_config['name']}: {e}")
            time.sleep(30)

# Istanza globale
monitor_service = MonitorService()

# Funzioni esportate
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