"""
Sistema di notifica email per VeloCloudiX
Gestisce l'invio di email per:
1. VM spente non programmate
2. Riavvii automatici falliti
3. Notifiche all'admin
"""

import smtplib
from email.mime.text import MIMEText  # CORRETTO: MIMEText invece di MimeText
from email.mime.multipart import MIMEMultipart  # CORRETTO: MIMEMultipart invece di MimeMultipart
from datetime import datetime
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Gestore per l'invio di notifiche email via SMTP
    """
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        """
        Inizializza il notificatore email
        
        Args:
            smtp_server (str): Server SMTP (default: Gmail)
            smtp_port (int): Porta SMTP (default: 587 per TLS)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Configurazione SMTP (da personalizzare con i tuoi dati)
        self.smtp_config = {
            'email': 'tua.email@gmail.com',      # MODIFICARE
            'password': 'tua_password_app',      # MODIFICARE
            'admin_email': 'admin@azienda.com'   # MODIFICARE
        }
        
        # Template per le email
        self.email_templates = {
            'vm_stopped': {
                'subject': 'VeloCloudiX - VM Spenta Rilevata',
                'template': '''
                <h2>Allerta VM Spenta</h2>
                <p><strong>VM:</strong> {vm_name}</p>
                <p><strong>Display Name:</strong> {display_name}</p>
                <p><strong>Ora rilevamento:</strong> {timestamp}</p>
                <p><strong>Stato:</strong> {status}</p>
                <p><strong>Azione intrapresa:</strong> Tentativo di riavvio automatico</p>
                <hr>
                <p><em>Questo è un messaggio automatico da VeloCloudiX</em></p>
                '''
            },
            'restart_failed': {
                'subject': 'VeloCloudiX - Riavvio Automatico Fallito',
                'template': '''
                <h2>Riavvio Automatico Fallito</h2>
                <p><strong>VM:</strong> {vm_name}</p>
                <p><strong>Display Name:</strong> {display_name}</p>
                <p><strong>Ora tentativo:</strong> {timestamp}</p>
                <p><strong>Errore:</strong> {error_message}</p>
                <p><strong>Azione richiesta:</strong> Intervento manuale necessario</p>
                <hr>
                <p><em>Questo è un messaggio automatico da VeloCloudiX</em></p>
                '''
            },
            'restart_success': {
                'subject': 'VeloCloudiX - VM Riavviata Automaticamente',
                'template': '''
                <h2>VM Riavviata con Successo</h2>
                <p><strong>VM:</strong> {vm_name}</p>
                <p><strong>Display Name:</strong> {display_name}</p>
                <p><strong>Ora riavvio:</strong> {timestamp}</p>
                <p><strong>Stato precedente:</strong> {previous_status}</p>
                <p><strong>Stato attuale:</strong> running</p>
                <hr>
                <p><em>Questo è un messaggio automatico da VeloCloudiX</em></p>
                '''
            }
        }
    
    def send_email(self, to_email, subject, html_content):
        """
        Invia un'email via SMTP
        
        Args:
            to_email (str): Email del destinatario
            subject (str): Oggetto dell'email
            html_content (str): Contenuto HTML dell'email
            
        Returns:
            bool: True se invio riuscito, False altrimenti
        """
        try:
            # Crea il messaggio - CORRETTO: MIMEMultipart invece di MimeMultipart
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Aggiungi il corpo HTML - CORRETTO: MIMEText invece di MimeText
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connetti al server SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Abilita TLS
            server.login(self.smtp_config['email'], self.smtp_config['password'])
            
            # Invia l'email
            text = msg.as_string()
            server.sendmail(self.smtp_config['email'], to_email, text)
            server.quit()
            
            logger.info(f"Email inviata a {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Errore invio email a {to_email}: {e}")
            return False
    
    def notify_vm_stopped(self, vm_name, display_name, status="stopped"):
        """
        Notifica che una VM è stata trovata spenta
        
        Args:
            vm_name (str): Nome tecnico della VM
            display_name (str): Nome visualizzato
            status (str): Stato della VM
        """
        template = self.email_templates['vm_stopped']
        html_content = template['template'].format(
            vm_name=vm_name,
            display_name=display_name,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status=status
        )
        
        return self.send_email(
            self.smtp_config['admin_email'],
            template['subject'],
            html_content
        )
    
    def notify_restart_failed(self, vm_name, display_name, error_message):
        """
        Notifica che il riavvio automatico è fallito
        
        Args:
            vm_name (str): Nome tecnico della VM
            display_name (str): Nome visualizzato
            error_message (str): Messaggio di errore
        """
        template = self.email_templates['restart_failed']
        html_content = template['template'].format(
            vm_name=vm_name,
            display_name=display_name,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            error_message=error_message
        )
        
        return self.send_email(
            self.smtp_config['admin_email'],
            template['subject'],
            html_content
        )
    
    def notify_restart_success(self, vm_name, display_name, previous_status):
        """
        Notifica che il riavvio automatico è riuscito
        
        Args:
            vm_name (str): Nome tecnico della VM
            display_name (str): Nome visualizzato
            previous_status (str): Stato precedente al riavvio
        """
        template = self.email_templates['restart_success']
        html_content = template['template'].format(
            vm_name=vm_name,
            display_name=display_name,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            previous_status=previous_status
        )
        
        return self.send_email(
            self.smtp_config['admin_email'],
            template['subject'],
            html_content
        )

# Istanza globale del notificatore
email_notifier = EmailNotifier()

# Funzioni di utilità per uso diretto
def send_vm_stopped_alert(vm_name, display_name, status="stopped"):
    """Invio rapido alert VM spenta"""
    return email_notifier.notify_vm_stopped(vm_name, display_name, status)

def send_restart_failed_alert(vm_name, display_name, error_message):
    """Invio rapido alert riavvio fallito"""
    return email_notifier.notify_restart_failed(vm_name, display_name, error_message)

def send_restart_success_alert(vm_name, display_name, previous_status):
    """Invio rapido notifica riavvio riuscito"""
    return email_notifier.notify_restart_success(vm_name, display_name, previous_status)

# Test del modulo
if __name__ == "__main__":
    print("Test sistema notifiche email...")
    
    # Test invio email
    success = email_notifier.notify_vm_stopped(
        vm_name="vm-web-server-01",
        display_name="Web Server",
        status="stopped"
    )
    
    if success:
        print("Test email riuscito!")
    else:
        print("Test email fallito - controlla configurazione SMTP")