from azure.identity import AzureCliCredential

AZURE_CONFIG = {
    "subscription_id": "9cf5c793-e6a4-4118-95dd-f0584e1c421f",
    "resource_group": "VeloCloudix",
    
    "vms": [
        {
            "name": "vm-web-server-01",
            "display_name": "Web Server",
            "resource_group": "VeloCloudix"
        },
        {
            "name": "vm-database-01", 
            "display_name": "Database Server", 
            "resource_group": "VeloCloudix"
        }
    ]
}

def get_azure_credentials():
    return AzureCliCredential()