# src/test_azure_connection.py
"""
Test CORRETTO della connessione alle VM Azure reali
"""

from azure_config import AZURE_CONFIG, get_azure_credentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.core.exceptions import ResourceNotFoundError

def test_azure_connection():
    print("🔍 TEST CORRETTO CONNESSIONE AZURE")
    print("=" * 50)
    
    try:
        # 1. Test autenticazione
        print("1. 🔑 Test autenticazione...")
        credential = get_azure_credentials()
        print("   ✅ Autenticazione riuscita!")
        
        # 2. Test subscription - USANDO SubscriptionClient CORRETTO
        print("2. 📋 Test subscription...")
        subscription_client = SubscriptionClient(credential)
        subscriptions = list(subscription_client.subscriptions.list())
        
        if subscriptions:
            sub = subscriptions[0]
            print(f"   ✅ Subscription: {sub.display_name}")
            print(f"   ✅ Subscription ID: {sub.subscription_id}")
        else:
            print("   ❌ Nessuna subscription trovata")
            return
        
        # 3. Test VM direttamente
        print("3. 🖥️  Test VM direttamente...")
        compute_client = ComputeManagementClient(credential, AZURE_CONFIG["subscription_id"])
        
        for vm_config in AZURE_CONFIG["vms"]:
            vm_name = vm_config["name"]
            resource_group = vm_config["resource_group"]
            
            print(f"   🔍 Test VM: {vm_name}")
            print(f"      Resource Group: {resource_group}")
            
            try:
                # Prova a ottenere la VM
                vm = compute_client.virtual_machines.get(resource_group, vm_name)
                print(f"      ✅ VM trovata: {vm.name}")
                
                # Prova a ottenere lo stato
                print(f"      ⚡ Ottenendo stato VM...")
                instance_view = compute_client.virtual_machines.instance_view(resource_group, vm_name)
                
                # Mostra lo stato
                power_state = "unknown"
                for status in instance_view.statuses:
                    if status.code.startswith('PowerState'):
                        power_state = status.code
                        break
                
                print(f"      ⚡ Stato: {power_state}")
                
                # Traduci in stato semplice
                if 'running' in power_state.lower():
                    print("      🟢 VM è RUNNING")
                elif 'stopped' in power_state.lower() or 'deallocated' in power_state.lower():
                    print("      🔴 VM è STOPPED")
                else:
                    print("      🟡 Stato sconosciuto")
                    
            except ResourceNotFoundError:
                print(f"      ❌ VM NON TROVATA: {vm_name}")
                print("      💡 Controlla che:")
                print("         - Il nome della VM sia ESATTO")
                print("         - La VM sia nello stesso Resource Group")
                print("         - La VM sia stata creata correttamente")
                
            except Exception as e:
                print(f"      ❌ Errore: {e}")
        
        print("\n🎉 TEST COMPLETATO!")
        
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        print("\n🔧 SOLUZIONE:")
        print("1. Verifica di aver eseguito: az login")
        print("2. Controlla i nomi delle VM nel Portale Azure")
        print("3. Assicurati che le VM siano nello stesso Resource Group")

if __name__ == "__main__":
    test_azure_connection()