# src/azure_config.py
"""
Configurazione per Azure VM reali - Versione che forza Azure CLI
"""

import os
from azure.identity import AzureCliCredential

AZURE_CONFIG = {
    "subscription_id": "9cf5c793-e6a4-4118-95dd-f0584e1c421f",
    "resource_group": "VeloCloudix", 
    "location": "West Europe",
    
    "vms": [
        {
            "name": "vm-web-server-01",
            "display_name": "Web Server",
            "resource_group": "VeloCloudix",
            "owner_email": "liman.mani@edu-its.it"
        },
        {
            "name": "vm-database-01", 
            "display_name": "Database Server", 
            "resource_group": "VeloCloudix",
            "owner_email": "liman.mani@edu-its.it"
        }
    ]
}

def get_azure_credentials():
    """FORZA l'uso di Azure CLI Credential"""
    print("🔑 Utilizzo Azure CLI Credential...")
    try:
        credential = AzureCliCredential()
        
        # Test immediato delle credenziali
        from azure.mgmt.resource import SubscriptionClient
        client = SubscriptionClient(credential)
        subscriptions = list(client.subscriptions.list())
        
        print(f"✅ Autenticazione Azure CLI riuscita!")
        print(f"📋 Subscription: {subscriptions[0].display_name if subscriptions else 'N/A'}")
        return credential
        
    except Exception as e:
        print(f"❌ Errore autenticazione Azure CLI: {e}")
        print("\n💡 SOLUZIONE RAPIDA:")
        print("1. Assicurati di aver eseguito: az login")
        print("2. Prova a riavviare il terminale")
        print("3. Esegui di nuovo: az login")
        raise