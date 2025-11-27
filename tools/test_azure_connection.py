# PERFETTO per troubleshooting
from src.azure_config import AZURE_CONFIG, get_azure_credentials
from azure.mgmt.compute import ComputeManagementClient

def test_connection():
    print("🧪 Test connessione Azure...")
    credential = get_azure_credentials()
    
    for vm_config in AZURE_CONFIG["vms"]:
        try:
            compute_client = ComputeManagementClient(credential, AZURE_CONFIG["subscription_id"])
            vm = compute_client.virtual_machines.get(vm_config["resource_group"], vm_config["name"])
            print(f" {vm_config['name']}: TROVATA")
        except Exception as e:
            print(f" {vm_config['name']}: ERRORE - {e}")

if __name__ == "__main__":
    test_connection()