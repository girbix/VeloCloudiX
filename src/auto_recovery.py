"""
Sistema di ripristino automatico per VM spente
Gestisce riavvii automatici e notifiche email
"""

from src.email_notifier import send_vm_stopped_alert, send_restart_failed_alert, send_restart_success_alert

class AutoRecoverySystem:
    """Sistema di ripristino automatico per VM spente non programmate"""
    
    def __init__(self, azure_controller, status_manager, operation_tracker):
        self.azure_controller = azure_controller  # Controller Azure
        self.status_manager = status_manager      # Gestore stati
        self.operation_tracker = operation_tracker # Tracker operazioni
    
    def handle_stopped_vm(self, vm_config, previous_status):
        """Gestisce una VM spenta non programmata"""
        vm_name = vm_config["name"]
        display_name = vm_config["display_name"]
        
        print(f"Gestione VM spenta: {display_name}")
        
        # 1. Log evento di allerta nel database
        self.status_manager.log_event(vm_name, 'stopped', 'unexpected_stop', 
                                    f"VM {display_name} spenta inaspettatamente")
        
        # 2. Invia email di allerta all'admin
        print(f"Invio email allerta per: {display_name}")
        email_sent = send_vm_stopped_alert(vm_name, display_name, 'stopped')
        
        if email_sent:
            self.status_manager.log_event(vm_name, 'stopped', 'email_alert_sent', 
                                        "Email di allerta inviata all'admin")
        else:
            self.status_manager.log_event(vm_name, 'stopped', 'email_alert_failed', 
                                        "Invio email di allerta fallito")
        
        # 3. Tentativo di riavvio automatico
        print(f"Tentativo riavvio automatico: {display_name}")
        restart_success, restart_message = self.azure_controller.restart_vm(vm_config)
        
        if restart_success:
            self._handle_restart_success(vm_name, display_name, previous_status)
        else:
            self._handle_restart_failure(vm_name, display_name, restart_message)
        
        return restart_success
    
    def _handle_restart_success(self, vm_name, display_name, previous_status):
        """Gestisce riavvio automatico riuscito"""
        print(f"Riavvio automatico riuscito: {display_name}")
        
        # Invia email di successo all'admin
        send_restart_success_alert(vm_name, display_name, previous_status)
        
        # Aggiorna cache e log
        self.status_manager.update_vm_status(vm_name, 'running')
        self.status_manager.log_auto_restart_attempt(vm_name, display_name, True)
    
    def _handle_restart_failure(self, vm_name, display_name, error_message):
        """Gestisce riavvio automatico fallito"""
        print(f"Riavvio automatico fallito: {display_name}")
        
        # Invia email di errore all'admin
        send_restart_failed_alert(vm_name, display_name, error_message)
        
        # Log dell'errore nel database
        self.status_manager.log_auto_restart_attempt(vm_name, display_name, False, error_message)
    
    def should_handle_stopped_vm(self, vm_name):
        """Determina se gestire una VM spenta (esclude arresti manuali recenti)"""
        return not self.operation_tracker.has_recent_manual_stop(vm_name)  # True se non è arresto manuale recente