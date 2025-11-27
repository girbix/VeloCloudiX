"""
Controller per le operazioni dirette su Azure VM
Gestisce la comunicazione con le API Azure
"""

from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError
from src.azure_config import AZURE_CONFIG, get_azure_credentials

class AzureVMController:
    """Controller per gestire Azure VM reali"""
    
    def __init__(self):
        print("Inizializzazione Azure VM Controller...")
        self.credentials = get_azure_credentials()
        self.compute_client = ComputeManagementClient(
            self.credentials, 
            AZURE_CONFIG["subscription_id"]
        )
        print("Azure VM Controller pronto")
    
    def get_vm_status(self, vm_config):
        """Ottiene lo stato REALE di una VM Azure"""
        try:
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
            print(f"Errore controllo VM {vm_config['name']}: {e}")
            return 'error'
    
    def start_vm(self, vm_config):
        """Avvia una VM Azure"""
        try:
            print(f"Avvio VM: {vm_config['name']}")
            
            async_start = self.compute_client.virtual_machines.begin_start(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            async_start.wait()
            print(f"VM avviata: {vm_config['name']}")
            return True, "VM avviata con successo"
            
        except Exception as e:
            error_msg = f"Errore avvio VM: {str(e)}"
            print(f"{error_msg}")
            return False, error_msg
    
    def restart_vm(self, vm_config):
        """Riavvia una VM Azure"""
        try:
            print(f"Riavvio VM: {vm_config['name']}")
            
            async_restart = self.compute_client.virtual_machines.begin_restart(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            async_restart.wait()
            print(f"VM riavviata: {vm_config['name']}")
            return True, "VM riavviata con successo"
            
        except Exception as e:
            error_msg = f"Errore riavvio VM: {str(e)}"
            print(f"{error_msg}")
            return False, error_msg
    
    def stop_vm(self, vm_config):
        """Arresta una VM Azure"""
        try:
            print(f"Arresto VM: {vm_config['name']}")
            
            async_stop = self.compute_client.virtual_machines.begin_power_off(
                vm_config["resource_group"], 
                vm_config["name"]
            )
            
            async_stop.wait()
            print(f"VM arrestata: {vm_config['name']}")
            return True, "VM arrestata con successo"
            
        except Exception as e:
            error_msg = f"Errore arresto VM: {str(e)}"
            print(f"{error_msg}")
            return False, error_msg