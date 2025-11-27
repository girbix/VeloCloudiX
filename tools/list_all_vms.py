# src/list_all_vms.py
"""
Lista TUTTE le VM nella subscription per vedere i nomi esatti
"""

from azure_config import get_azure_credentials
from azure.mgmt.compute import ComputeManagementClient

def list_all_vms_in_subscription():
    print(" LISTA DI TUTTE LE VM NELLA SUBSCRIPTION")
    print("=" * 50)
    
    try:
        credential = get_azure_credentials()
        compute_client = ComputeManagementClient(credential, "9cf5c793-e6a4-4118-95dd-f0584e1c421f")
        
        # Lista tutte le VM in TUTTA la subscription
        print("🔍 Scansionando tutte le VM...")
        vms_list = list(compute_client.virtual_machines.list_all())
        
        print(f" Trovate {len(vms_list)} VM in totale:")
        print("-" * 40)
        
        for i, vm in enumerate(vms_list, 1):
            # Estrai resource group dal ID
            rg_name = vm.id.split('/')[4]
            
            print(f"{i}.   Nome VM: {vm.name}")
            print(f"    Resource Group: {rg_name}")
            print(f"    Location: {vm.location}")
            print(f"    Tipo: {vm.hardware_profile.vm_size}")
            
            try:
                # Prova a ottenere lo stato
                instance_view = compute_client.virtual_machines.instance_view(rg_name, vm.name)
                power_state = "unknown"
                for status in instance_view.statuses:
                    if status.code.startswith('PowerState'):
                        power_state = status.code
                        break
                print(f" Stato: {power_state}")
            except:
                print(f"Stato: Non disponibile")
            
            print("   " + "─" * 30)
        
        if not vms_list:
            print(" Nessuna VM trovata nella subscription")
            print(" Le VM potrebbero non essere state create correttamente")
        
        print("\N COPIA i nomi ESATTI delle VM e modifica azure_config.py")
        
    except Exception as e:
        print(f" Errore: {e}")

if __name__ == "__main__":
    list_all_vms_in_subscription()