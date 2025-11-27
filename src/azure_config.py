from azure.identity import AzureCliCredential

# Linea 3-18: CONFIGURAZIONE AZURE
AZURE_CONFIG = {
    "subscription_id": "9cf5c793-e6a4-4118-95dd-f0584e1c421f",  # ID sottoscrizione Azure
    "resource_group": "VeloCloudix",  # Gruppo di risorse
    
    # Lista delle VM da monitorare
    "vms": [
        {
            "name": "vm-web-server-01",      # Nome tecnico della VM
            "display_name": "Web Server",    # Nome visualizzato
            "resource_group": "VeloCloudix"  # Gruppo risorse
        },
        {
            "name": "vm-database-01", 
            "display_name": "Database Server", 
            "resource_group": "VeloCloudix"
        }
    ]
}

# Linea 21-23: FUNZIONE PER OTTENERE CREDENZIALI AZURE
def get_azure_credentials():
    return AzureCliCredential()  # Usa Azure CLI per autenticazione