"""
Configurazione per il sistema di notifica email
"""

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'tua.email@gmail.com',
    'password': 'tua_password_app',  # Password app per Gmail
    'admin_email': 'admin@azienda.com'
}

# Per Gmail, devi usare una "Password App":
# 1. Vai su Google Account → Sicurezza
# 2. Attiva la verifica in 2 passaggi
# 3. Cerca "Password app" e generane una
# 4. Usa quella password qui sopra