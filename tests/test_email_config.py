from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Configuración desde .env
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

print("🔧 Configuración cargada:")
print(f"   Server: {app.config['MAIL_SERVER']}")
print(f"   Port: {app.config['MAIL_PORT']}")
print(f"   TLS: {app.config['MAIL_USE_TLS']}")
print(f"   SSL: {app.config['MAIL_USE_SSL']}")
print(f"   Username: {app.config['MAIL_USERNAME']}")
print(f"   Password: {'*' * len(app.config['MAIL_PASSWORD']) if app.config['MAIL_PASSWORD'] else 'NO CONFIGURADO'}")

mail = Mail(app)

try:
    with app.app_context():
        msg = Message(
            subject='✅ Test Email - Rifa System',
            recipients=['yeyvercury@gmail.com'],  # Enviar a ti mismo
            body='Este es un email de prueba desde Flask-Mail.'
        )
        mail.send(msg)
        print("\n✅ Email enviado exitosamente!")
        print("   Revisa tu bandeja de entrada.")
except Exception as e:
    print(f"\n❌ Error enviando email:")
    print(f"   {str(e)}")
