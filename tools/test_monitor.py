# UTILE per testare il sistema di monitoraggio
from src.azure_monitor import start_monitoring, stop_monitoring
import time

def test_monitor():
    print("🧪 Test sistema monitoraggio...")
    start_monitoring()
    
    # Test per 2 minuti
    time.sleep(120)
    
    stop_monitoring()
    print(" Test completato")

if __name__ == "__main__":
    test_monitor()