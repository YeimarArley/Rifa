import os
import random
import logging
import hashlib
import hmac
import uuid
import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, abort, session
from dotenv import load_dotenv
from functools import wraps
from flask_mail import Mail, Message
import secrets

# ==================== CONFIGURACIÓN INICIAL ====================
load_dotenv()

# Create Flask app PRIMERO
app = Flask(__name__)

# ==================== CONFIGURACIÓN DE SEGURIDAD ====================
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# Clave de admin de simulación
ADMIN_SIM_KEY = os.getenv('ADMIN_SIM_KEY', secrets.token_urlsafe(32))

# ==================== CONFIGURACIÓN DE BASE DE DATOS ====================
from app import db as app_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    app_db.init_db()
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    import traceback
    traceback.print_exc()

# ==================== CONFIGURACIÓN DE PAGOS ====================
EPAYCO_PUBLIC_KEY = os.getenv('EPAYCO_PUBLIC_KEY', '70b19a05a3f3374085061d1bfd386a8b')
EPAYCO_PRIVATE_KEY = os.getenv('EPAYCO_PRIVATE_KEY', 'your_private_key_here')

# ==================== CONFIGURACIÓN DE EMAIL ====================
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    logger.warning("⚠️ Credenciales de email no configuradas")

mail = Mail(app)

# ==================== URLs ====================
BASE_URL = os.getenv('BASE_URL', 'https://familiones.com')
RESPONSE_URL = os.getenv('RESPONSE_URL', 'https://familiones.com/confirmation')
CONFIRMATION_URL = os.getenv('CONFIRMATION_URL', 'https://familiones.com/confirmation')

# ==================== ALMACENAMIENTO DE TOKENS ====================
password_reset_tokens = {}


# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def hash_password(password):
    """Hashea una contraseña con SHA256 + SALT"""
    salt = os.getenv('PASSWORD_SALT', 'rifa_salt_2025')
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password, password_hash):
    """Verifica una contraseña contra su hash"""
    return hash_password(password) == password_hash


def login_required(f):
    """Decorador para proteger rutas administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            logger.warning(f"⚠️ Intento de acceso no autorizado a: {request.path} desde IP: {request.remote_addr}")
            return redirect(url_for('admin_login', next=request.path))
        
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            if datetime.now() - last_activity_time > timedelta(hours=2):
                logger.info("⏰ Sesión expirada por inactividad")
                session.clear()
                return redirect(url_for('admin_login', next=request.path, expired='1'))
        
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function


def admin_api_key_required(f):
    """Decorador para proteger APIs administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Admin-Key')
        if not api_key:
            api_key = request.form.get('key')
        
        if not api_key or api_key != ADMIN_SIM_KEY:
            logger.warning(f"⚠️ Intento de acceso API no autorizado desde IP: {request.remote_addr}")
            abort(403, description="API key inválida o faltante")
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== FUNCIONES DE RECUPERACIÓN DE CONTRASEÑA ====================

def generate_reset_token():
    """Genera un token seguro de recuperación"""
    return secrets.token_urlsafe(32)


def send_password_reset_email(email, token, admin_id):
    """Envía email con link de recuperación de contraseña"""
    try:
        logger.info(f"📧 Enviando email de recuperación a {email}...")
        
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            logger.warning("⚠️ Credenciales de email no configuradas")
            return False
        
        reset_link = f"{BASE_URL}/admin/reset_password/{token}"
        
        msg = Message(
            subject='🔐 Recuperación de Contraseña - Rifa 5 Millones',
            recipients=[email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 30px;
                }}
                .alert-box {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                    font-size: 16px;
                }}
                .footer {{
                    background-color: #f8f8f8;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }}
                .security-note {{
                    background: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div style="font-size: 50px;">🔐</div>
                    <h1>Recuperación de Contraseña</h1>
                </div>
                
                <div class="content">
                    <p>Hola,</p>
                    
                    <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta de administrador.</p>
                    
                    <div class="alert-box">
                        <strong>⏰ Este enlace expira en 30 minutos</strong>
                    </div>
                    
                    <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                    
                    <center>
                        <a href="{reset_link}" class="button">Restablecer Contraseña</a>
                    </center>
                    
                    <p style="font-size: 12px; color: #666; margin-top: 20px;">
                        Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                        <a href="{reset_link}" style="color: #667eea; word-break: break-all;">{reset_link}</a>
                    </p>
                    
                    <div class="security-note">
                        <strong>🚨 ¿No solicitaste este cambio?</strong><br>
                        Si no fuiste tú quien solicitó este cambio, ignora este email. 
                        Tu contraseña permanecerá segura.
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Rifa 5 Millones - Panel Administrativo</strong></p>
                    <p>Este es un correo automático de seguridad, por favor no respondas a este mensaje.</p>
                    <p>© 2025 Rifa 5 Millones. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.body = f"""
        Recuperación de Contraseña - Rifa 5 Millones
        
        Hola,
        
        Hemos recibido una solicitud para restablecer tu contraseña.
        
        Haz clic en el siguiente enlace para crear una nueva contraseña:
        {reset_link}
        
        ⏰ Este enlace expira en 30 minutos.
        
        🚨 Si no solicitaste este cambio, ignora este email.
        
        Rifa 5 Millones - Panel Administrativo
        """
        
        mail.send(msg)
        logger.info(f"✅ Email de recuperación enviado a {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email de recuperación a {email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_expired_tokens():
    """Limpia tokens expirados"""
    now = datetime.now()
    expired_tokens = [
        token for token, data in password_reset_tokens.items()
        if now > data['expires_at']
    ]
    for token in expired_tokens:
        del password_reset_tokens[token]
        logger.info(f"🗑️ Token expirado eliminado")


# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login de administrador con EMAIL"""
    if session.get('admin_logged_in'):
        return redirect('/database')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Rate limiting básico
        failed_attempts = session.get('failed_login_attempts', 0)
        if failed_attempts >= 5:
            logger.warning(f"🚨 Cuenta bloqueada temporalmente: {email}")
            return render_template('admin_login.html', 
                                 error="Demasiados intentos fallidos. Espera 15 minutos.")
        
        # Buscar usuario por email en base de datos
        try:
            user = app_db.run_query(
                "SELECT id, email, password_hash, is_active FROM admin_users WHERE LOWER(email) = LOWER(%s)",
                params=(email,),
                fetchone=True
            )
            
            if user:
                user_id = user[0]
                db_password_hash = user[2]
                is_active = user[3]
                
                # Verificar si está activo
                if not is_active:
                    logger.warning(f"❌ Usuario inactivo intentó login: {email}")
                    return render_template('admin_login.html', 
                                         error="Cuenta desactivada. Contacta al administrador.")
                
                # Verificar contraseña
                if verify_password(password, db_password_hash):
                    # Login exitoso
                    session.clear()
                    session['admin_logged_in'] = True
                    session['admin_id'] = user_id
                    session['admin_email'] = email
                    session['last_activity'] = datetime.now().isoformat()
                    session['login_time'] = datetime.now().isoformat()
                    session.permanent = True
                    
                    logger.info(f"✅ Admin login exitoso: {email} desde IP: {request.remote_addr}")
                    
                    next_page = request.args.get('next', '/database')
                    return redirect(next_page)
            
            # Login fallido
            session['failed_login_attempts'] = failed_attempts + 1
            logger.warning(f"❌ Intento de login fallido: {email} desde IP: {request.remote_addr}")
            return render_template('admin_login.html', 
                                 error="Credenciales incorrectas")
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            import traceback
            traceback.print_exc()
            return render_template('admin_login.html', 
                                 error="Error del sistema. Intenta nuevamente.")
    
    # GET request
    expired = request.args.get('expired')
    error = "Tu sesión ha expirado. Por favor, inicia sesión nuevamente." if expired else None
    
    return render_template('admin_login.html', error=error)


@app.route('/admin/logout')
def admin_logout():
    """Logout de administrador"""
    email = session.get('admin_email', 'Desconocido')
    logger.info(f"👋 Admin logout: {email}")
    session.clear()
    return redirect('/')


@app.route('/admin/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Página de solicitud de recuperación de contraseña"""
    if session.get('admin_logged_in'):
        return redirect('/database')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Validar formato de email
        if not email or '@' not in email:
            return render_template('forgot_password.html', 
                                 error="Email inválido")
        
        # Buscar usuario por email
        try:
            user = app_db.run_query(
                "SELECT id, email FROM admin_users WHERE LOWER(email) = LOWER(%s) AND is_active = TRUE",
                params=(email,),
                fetchone=True
            )
            
            if user:
                user_id = user[0]
                
                # Generar token
                token = generate_reset_token()
                expires_at = datetime.now() + timedelta(minutes=30)
                
                # Almacenar token
                password_reset_tokens[token] = {
                    'user_id': user_id,
                    'email': email,
                    'created_at': datetime.now(),
                    'expires_at': expires_at,
                    'used': False
                }
                
                # Enviar email
                email_sent = send_password_reset_email(email, token, user_id)
                
                if email_sent:
                    logger.info(f"🔐 Token de recuperación generado para {email} - IP: {request.remote_addr}")
                else:
                    logger.error(f"❌ Error al enviar email de recuperación")
            else:
                logger.warning(f"⚠️ Intento de recuperación con email no registrado: {email}")
            
            # Por seguridad, siempre mostrar mensaje genérico
            return render_template('forgot_password.html', 
                                 success="Si el email está registrado, recibirás instrucciones para restablecer tu contraseña.")
            
        except Exception as e:
            logger.error(f"Error en forgot_password: {e}")
            return render_template('forgot_password.html', 
                                 error="Error del sistema. Intenta nuevamente.")
    
    # GET request
    return render_template('forgot_password.html')


@app.route('/admin/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página de reseteo de contraseña con token"""
    cleanup_expired_tokens()
    
    # Validar token
    if token not in password_reset_tokens:
        logger.warning(f"⚠️ Intento de uso de token inválido desde IP: {request.remote_addr}")
        return render_template('reset_password.html', 
                             error="Token inválido o expirado. Solicita un nuevo enlace de recuperación.",
                             token_invalid=True)
    
    token_data = password_reset_tokens[token]
    
    # Verificar expiración
    if datetime.now() > token_data['expires_at']:
        del password_reset_tokens[token]
        logger.warning(f"⏰ Token expirado usado desde IP: {request.remote_addr}")
        return render_template('reset_password.html', 
                             error="Este enlace ha expirado. Solicita un nuevo enlace de recuperación.",
                             token_invalid=True)
    
    # Verificar si ya fue usado
    if token_data['used']:
        logger.warning(f"⚠️ Intento de reutilizar token desde IP: {request.remote_addr}")
        return render_template('reset_password.html', 
                             error="Este enlace ya fue utilizado. Solicita un nuevo enlace si lo necesitas.",
                             token_invalid=True)
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validar contraseñas
        errors = []
        
        if not new_password:
            errors.append("La contraseña es obligatoria")
        
        if len(new_password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if new_password != confirm_password:
            errors.append("Las contraseñas no coinciden")
        
        if not any(c.isupper() for c in new_password):
            errors.append("La contraseña debe contener al menos una mayúscula")
        
        if not any(c.islower() for c in new_password):
            errors.append("La contraseña debe contener al menos una minúscula")
        
        if not any(c.isdigit() for c in new_password):
            errors.append("La contraseña debe contener al menos un número")
        
        if errors:
            return render_template('reset_password.html', 
                                 errors=errors, 
                                 token=token)
        
        # Hashear nueva contraseña
        new_password_hash = hash_password(new_password)
        
        # Actualizar en base de datos
        try:
            app_db.run_query(
                "UPDATE admin_users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                params=(new_password_hash, token_data['user_id']),
                commit=True
            )
            
            # Marcar token como usado
            password_reset_tokens[token]['used'] = True
            
            logger.info(f"✅ Contraseña actualizada exitosamente para {token_data['email']} - IP: {request.remote_addr}")
            
            # Limpiar sesiones activas
            session.clear()
            
            return render_template('reset_password.html', 
                                 success=True,
                                 token_invalid=True)
            
        except Exception as e:
            logger.error(f"❌ Error actualizando contraseña: {e}")
            import traceback
            traceback.print_exc()
            return render_template('reset_password.html', 
                                 error="Error al actualizar la contraseña. Intenta nuevamente.",
                                 token=token)
    
    # GET request
    return render_template('reset_password.html', token=token)


# ==================== RUTAS PÚBLICAS ====================

@app.route('/')
def index():
    """Página principal"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index.html: {e}")
        return f"Error loading page: {str(e)}", 500


@app.route('/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos"""
    return send_from_directory('.', filename)


@app.route('/progress')
def progress():
    """API de progreso"""
    total_numbers = 2000
    assigned_count = 0
    try:
        assigned_count = app_db.count_assigned_numbers()
    except Exception as e:
        logger.error(f"Error counting assigned numbers: {e}")

    percentage = 0.0
    try:
        percentage = (assigned_count / total_numbers) * 100
    except Exception:
        percentage = 0.0

    return jsonify({
        'assigned': int(assigned_count or 0),
        'total': total_numbers,
        'percentage': round(percentage, 1)
    })


@app.route('/api/blessed_numbers_status')
def api_blessed_numbers_status():
    """API de números benditos"""
    try:
        config = get_blessed_numbers_config()
        
        now = datetime.now()
        visible = config['visible']
        show_date = None
        
        if config['scheduled_date'] and not visible:
            try:
                scheduled = datetime.fromisoformat(config['scheduled_date'])
                if now >= scheduled:
                    visible = True
                    save_blessed_numbers_config(True, config['scheduled_date'], config['numbers'])
                else:
                    show_date = scheduled.strftime('%d/%m/%Y %H:%M')
            except Exception as e:
                logger.error(f"Error parsing scheduled date: {e}")
        
        return jsonify({
            'visible': visible,
            'scheduled_date': config['scheduled_date'],
            'show_date': show_date,
            'numbers': config['numbers'] if (visible and config['numbers']) else [],
            'has_numbers': bool(config['numbers'])
        })
    except Exception as e:
        logger.error(f"Error in blessed numbers status: {e}")
        return jsonify({
            'visible': False, 
            'numbers': [], 
            'has_numbers': False
        })


# ==================== RUTAS PROTEGIDAS ====================

@app.route('/database')
@login_required
def database():
    """Panel de administración"""
    try:
        search_query = request.args.get('search', '').strip()
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        status_filter = request.args.get('status', '')
        
        query = "SELECT * FROM purchases WHERE 1=1"
        params = []
        
        if search_query:
            query += """ AND (
                LOWER(full_name) LIKE LOWER(%s) OR 
                LOWER(email) LIKE LOWER(%s) OR 
                LOWER(phone) LIKE LOWER(%s) OR 
                LOWER(document_number) LIKE LOWER(%s)
            )"""
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        if date_from:
            query += " AND created_at >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND created_at <= %s"
            params.append(date_to)
        
        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)
        
        query += " AND (status != 'deleted' OR status IS NULL)"
        query += " ORDER BY created_at DESC LIMIT 100"
        
        purchases = app_db.run_query(query, params=tuple(params) if params else None, fetchall=True) or []
        metrics = calculate_metrics(date_from, date_to)
        table_rows = generate_table_rows(purchases)
        
        return render_template('admin_database.html',
                             purchases=purchases,
                             table_rows=table_rows,
                             metrics=metrics,
                             search_query=search_query,
                             date_from=date_from,
                             date_to=date_to,
                             status_filter=status_filter)
    
    except Exception as e:
        logger.error(f"Error en endpoint /database: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error en Base de Datos</h1><pre>{str(e)}</pre>", 500


@app.route('/admin/blessed_numbers', methods=['GET', 'POST'])
@login_required
def admin_blessed_numbers():
    """Panel de números benditos"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save':
            visible = request.form.get('visible') == 'on'
            scheduled_date = request.form.get('scheduled_date') or None
            number1 = request.form.get('number1', '').strip()
            number2 = request.form.get('number2', '').strip()
            
            errors = []
            numbers = []
            
            if number1:
                try:
                    num1 = int(number1)
                    if 1 <= num1 <= 2000:
                        numbers.append(num1)
                    else:
                        errors.append("El número 1 debe estar entre 1 y 2000")
                except ValueError:
                    errors.append("El número 1 debe ser un entero válido")
            
            if number2:
                try:
                    num2 = int(number2)
                    if 1 <= num2 <= 2000:
                        if num2 not in numbers:
                            numbers.append(num2)
                        else:
                            errors.append("Los números no pueden ser iguales")
                    else:
                        errors.append("El número 2 debe estar entre 1 y 2000")
                except ValueError:
                    errors.append("El número 2 debe ser un entero válido")
            
            if errors:
                config = get_blessed_numbers_config()
                return render_template('admin_blessed_numbers.html', 
                                     config=config, 
                                     errors=errors)
            
            save_blessed_numbers_config(visible, scheduled_date, numbers if numbers else None)
            return redirect('/admin/blessed_numbers?success=1')
        
        elif action == 'delete':
            save_blessed_numbers_config(False, None, None)
            return redirect('/admin/blessed_numbers?deleted=1')
    
    config = get_blessed_numbers_config()
    success = request.args.get('success')
    deleted = request.args.get('deleted')
    
    return render_template('admin_blessed_numbers.html', 
                         config=config, 
                         success=success,
                         deleted=deleted)


@app.route('/edit_purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def edit_purchase(purchase_id):
    """Editar compra"""
    if request.method == 'POST':
        invoice_id = request.form['invoice_id']
        amount = request.form['amount']
        email = request.form['email']
        numbers = request.form['numbers']
        status = request.form['status']

        conn = app_db.get_db_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE purchases
            SET invoice_id = %s, amount = %s, email = %s, numbers = %s, status = %s
            WHERE id = %s
        """, (invoice_id, amount, email, numbers, status, purchase_id))
        conn.commit()
        conn.close()

        logger.info(f"✏️ Compra {purchase_id} editada por {session.get('admin_email')}")
        return redirect('/database')

    purchase = app_db.run_query("SELECT * FROM purchases WHERE id = %s", params=(purchase_id,), fetchone=True)

    if not purchase:
        abort(404, description="Compra no encontrada")

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Editar Compra - Rifa</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
            .btn {{ padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
            .btn-save {{ background-color: #4CAF50; color: white; }}
            .btn-cancel {{ background-color: #f44336; color: white; text-decoration: none; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✏️ Editar Compra</h1>
            <form method="POST">
                <div class="form-group">
                    <label>Referencia:</label>
                    <input type="text" name="invoice_id" value="{purchase[1]}" required>
                </div>
                <div class="form-group">
                    <label>Monto:</label>
                    <input type="number" name="amount" value="{purchase[2]}" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" name="email" value="{purchase[3]}" required>
                </div>
                <div class="form-group">
                    <label>Números:</label>
                    <input type="text" name="numbers" value="{purchase[4]}" required>
                </div>
                <div class="form-group">
                    <label>Estado:</label>
                    <select name="status">
                        <option value="pending" {'selected' if purchase[5] == 'pending' else ''}>Pendiente</option>
                        <option value="confirmed" {'selected' if purchase[5] == 'confirmed' else ''}>Confirmado</option>
                        <option value="cancelled" {'selected' if purchase[5] == 'cancelled' else ''}>Cancelado</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-save">Guardar</button>
                <a href="/database" class="btn btn-cancel">Cancelar</a>
            </form>
        </div>
    </body>
    </html>
    """


@app.route('/delete_purchase/<int:purchase_id>')
@login_required
def delete_purchase(purchase_id):
    """Eliminar compra"""
    purchase = app_db.run_query("SELECT numbers FROM purchases WHERE id = %s", params=(purchase_id,), fetchone=True)

    if purchase:
        numbers_str = purchase[0] if isinstance(purchase, (list, tuple)) else purchase
        if numbers_str:
            numbers = [int(n.strip()) for n in numbers_str.split(',')]
            for number in numbers:
                app_db.run_query("DELETE FROM assigned_numbers WHERE number = %s", params=(number,), commit=True)

        app_db.run_query("DELETE FROM purchases WHERE id = %s", params=(purchase_id,), commit=True)
        logger.info(f"🗑️ Compra {purchase_id} eliminada por {session.get('admin_email')}")
    
    return redirect('/database')


@app.route('/admin/simulate_purchase', methods=['POST'])
@admin_api_key_required
def simulate_purchase():
    """Simular compra"""
    try:
        amount = int(request.form.get('amount', 4))
        email = request.form.get('email', 'test@demo.com')
        customer_name = request.form.get('name', 'Cliente de Prueba')
        
        logger.info(f"🎲 Simulación iniciada por: {request.remote_addr}")
        
        numbers = assign_numbers(amount)
        
        if not numbers:
            logger.error("❌ No hay números disponibles")
            return jsonify({
                "status": "error",
                "message": "Not enough numbers available"
            }), 400
        
        invoice_id = f"sim_{uuid.uuid4().hex[:12]}"
        amount_value = amount * 6250
        
        saved = save_purchase(
            invoice_id=invoice_id,
            amount=amount_value,
            email=email,
            numbers=numbers,
            full_name=customer_name
        )
        
        if not saved:
            logger.error("❌ Error guardando en base de datos")
            return jsonify({
                "status": "error",
                "message": "Database error - check server logs"
            }), 500
        
        try:
            email_sent = send_purchase_confirmation_email(
                customer_email=email,
                customer_name=customer_name,
                numbers=numbers,
                amount=amount_value,
                invoice_id=invoice_id
            )
        except Exception as email_error:
            logger.error(f"❌ Error enviando email: {email_error}")
            email_sent = False
        
        logger.info(f"✅ Simulación completada: {invoice_id}")
        return jsonify({
            "status": "ok",
            "invoice_id": invoice_id,
            "numbers": numbers,
            "email_sent": email_sent
        })
            
    except Exception as e:
        logger.error(f"💥 Error en simulate_purchase: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500


# ==================== FUNCIONES AUXILIARES ====================

def send_purchase_confirmation_email(customer_email, customer_name, numbers, amount, invoice_id):
    """Envía email de confirmación de compra"""
    try:
        logger.info(f"📧 Preparando email para {customer_email}...")
        
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            logger.warning("⚠️ Credenciales de email no configuradas")
            return False
        
        msg = Message(
            subject='✅ ¡Confirmación de Compra - Rifa 5 Millones! 🎉',
            recipients=[customer_email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        numbers_formatted = ', '.join([str(num) for num in numbers])
        
        msg.html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .content {{
                    padding: 30px;
                }}
                .numbers-box {{
                    background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
                    border-left: 4px solid #4CAF50;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .numbers {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #4CAF50;
                    text-align: center;
                    margin: 10px 0;
                    word-wrap: break-word;
                }}
                .info-row {{
                    margin: 15px 0;
                    padding: 10px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #333;
                }}
                .info-value {{
                    color: #666;
                }}
                .footer {{
                    background-color: #f8f8f8;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .emoji {{
                    font-size: 40px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="emoji">🎉</div>
                    <h1>¡Compra Confirmada!</h1>
                    <p>Rifa 5 Millones</p>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{customer_name or 'Cliente'}</strong>,</p>
                    
                    <p>¡Gracias por participar en nuestra rifa! Tu compra ha sido confirmada exitosamente.</p>
                    
                    <div class="numbers-box">
                        <h3 style="margin-top: 0; color: #333;">🎫 Tus Números de la Suerte:</h3>
                        <div class="numbers">{numbers_formatted}</div>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">📋 Referencia:</span>
                        <span class="info-value">{invoice_id}</span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">💰 Monto:</span>
                        <span class="info-value">${amount:,.0f} COP</span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">📧 Email:</span>
                        <span class="info-value">{customer_email}</span>
                    </div>
                    
                    <div class="info-row">
                        <span class="info-label">🎯 Cantidad de números:</span>
                        <span class="info-value">{len(numbers)} números</span>
                    </div>
                    
                    <p style="margin-top: 30px; color: #666;">
                        Guarda este email como comprobante de tu participación. 
                        ¡Mucha suerte! 🍀
                    </p>
                    
                    <center>
                        <a href="https://familiones.com" class="button">Ver Sitio Web</a>
                    </center>
                </div>
                
                <div class="footer">
                    <p><strong>Rifa 5 Millones</strong></p>
                    <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                    <p>© 2025 Rifa 5 Millones. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.body = f"""
        ¡Compra Confirmada!
        
        Hola {customer_name or 'Cliente'},
        
        Gracias por participar en nuestra Rifa 5 Millones.
        
        Tus números de la suerte son: {numbers_formatted}
        
        Detalles de la compra:
        - Referencia: {invoice_id}
        - Monto: ${amount:,.0f} COP
        - Email: {customer_email}
        - Cantidad de números: {len(numbers)}
        
        Guarda este email como comprobante.
        ¡Mucha suerte!
        
        Rifa 5 Millones
        """
        
        mail.send(msg)
        logger.info(f"✅ Email enviado exitosamente a {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email a {customer_email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_blessed_numbers_config():
    """Obtiene la configuración de números benditos"""
    try:
        config = app_db.run_query(
            "SELECT * FROM blessed_numbers_config ORDER BY id DESC LIMIT 1",
            fetchone=True
        )
        if config:
            return {
                'visible': config[1],
                'scheduled_date': config[2],
                'numbers': json.loads(config[3]) if config[3] else []
            }
        return {'visible': False, 'scheduled_date': None, 'numbers': []}
    except Exception as e:
        logger.error(f"Error getting blessed numbers config: {e}")
        return {'visible': False, 'scheduled_date': None, 'numbers': []}


def save_blessed_numbers_config(visible, scheduled_date=None, numbers=None):
    """Guarda la configuración de números benditos"""
    try:
        numbers_json = json.dumps(numbers) if numbers else json.dumps([])
        app_db.run_query("""
            INSERT INTO blessed_numbers_config (visible, scheduled_date, numbers)
            VALUES (%s, %s, %s)
        """, params=(visible, scheduled_date, numbers_json), commit=True)
        logger.info(f"Blessed numbers config saved: visible={visible}")
        return True
    except Exception as e:
        logger.error(f"Error saving blessed numbers config: {e}")
        return False


def calculate_metrics(date_from=None, date_to=None):
    """Calcula métricas del sistema"""
    try:
        metrics = {}
        
        date_condition = "WHERE status = 'confirmed'"
        params = []
        
        if date_from:
            date_condition += " AND created_at >= %s"
            params.append(date_from)
        if date_to:
            date_condition += " AND created_at <= %s"
            params.append(date_to)
        
        result = app_db.run_query(
            f"SELECT COUNT(*) FROM purchases {date_condition}",
            params=tuple(params) if params else None,
            fetchone=True
        )
        metrics['total_purchases'] = result[0] if result else 0
        
        result = app_db.run_query(
            f"SELECT SUM(amount) FROM purchases {date_condition}",
            params=tuple(params) if params else None,
            fetchone=True
        )
        metrics['total_revenue'] = float(result[0]) if result and result[0] else 0.0
        
        metrics['numbers_sold'] = app_db.count_assigned_numbers()
        metrics['numbers_available'] = 2000 - metrics['numbers_sold']
        metrics['percentage_sold'] = (metrics['numbers_sold'] / 2000) * 100
        
        result = app_db.run_query("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count,
                SUM(amount) as revenue
            FROM purchases 
            WHERE status = 'confirmed' 
            AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, fetchall=True)
        
        metrics['daily_sales'] = []
        if result:
            for row in result:
                metrics['daily_sales'].append({
                    'date': str(row[0]),
                    'count': row[1],
                    'revenue': float(row[2])
                })
        
        if metrics['total_purchases'] > 0:
            metrics['average_purchase'] = metrics['total_revenue'] / metrics['total_purchases']
        else:
            metrics['average_purchase'] = 0.0
        
        result = app_db.run_query("""
            SELECT amount, COUNT(*) as count
            FROM purchases 
            WHERE status = 'confirmed'
            GROUP BY amount
            ORDER BY count DESC
            LIMIT 1
        """, fetchone=True)
        
        if result:
            amount_map = {
                25000: '4 números',
                53000: '8 números',
                81000: '12 números',
                109000: '16 números',
                137000: '20 números'
            }
            metrics['most_popular_package'] = amount_map.get(int(result[0]), f'${result[0]:,.0f}')
        else:
            metrics['most_popular_package'] = 'N/A'
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculando métricas: {e}")
        return {
            'total_purchases': 0,
            'total_revenue': 0.0,
            'numbers_sold': 0,
            'numbers_available': 2000,
            'percentage_sold': 0.0,
            'daily_sales': [],
            'average_purchase': 0.0,
            'most_popular_package': 'N/A'
        }


def generate_table_rows(purchases):
    """Genera las filas HTML de la tabla con tema oscuro"""
    if not purchases:
        return '''
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #b0b0b0;">
                    <div style="font-size: 3em; margin-bottom: 1rem;">📭</div>
                    <div style="font-size: 1.2em;">No hay compras registradas</div>
                </td>
            </tr>
        '''
    
    table_rows = ""
    for p in purchases:
        try:
            p_id = p[0] if len(p) > 0 else 'N/A'
            p_invoice = p[1] if len(p) > 1 else 'N/A'
            p_amount = p[2] if len(p) > 2 else 0
            p_email = p[3] if len(p) > 3 else 'N/A'
            p_numbers = p[4] if len(p) > 4 else ''
            p_status = p[5] if len(p) > 5 else 'pending'
            
            p_full_name = p[10] if len(p) > 10 and p[10] else 'No especificado'
            p_document = p[12] if len(p) > 12 and p[12] else 'N/A'
            p_phone = p[13] if len(p) > 13 and p[13] else 'N/A'
            
            status_styles = {
                'confirmed': 'background: linear-gradient(135deg, #4CAF50, #45a049); color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 700; box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);',
                'pending': 'background: linear-gradient(135deg, #FFA500, #FF8C00); color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 700; box-shadow: 0 0 15px rgba(255, 165, 0, 0.5);',
                'cancelled': 'background: linear-gradient(135deg, #f44336, #d32f2f); color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 700; box-shadow: 0 0 15px rgba(244, 67, 54, 0.5);'
            }
            status_style = status_styles.get(p_status, '')
            
            numbers_display = p_numbers
            if len(p_numbers) > 50:
                num_count = len(p_numbers.split(','))
                numbers_display = f"{p_numbers[:50]}... ({num_count} números)"
            
            table_rows += f'''
            <tr style="border-bottom: 1px solid rgba(76, 175, 80, 0.1);">
                <td style="padding: 12px; color: #e0e0e0; font-weight: 600;">{p_id}</td>
                <td style="padding: 12px; color: #e0e0e0;">{p_invoice}</td>
                <td style="padding: 12px; font-weight: 700; color: #4CAF50;">${float(p_amount):,.0f}</td>
                <td style="padding: 12px;">
                    <div style="margin-bottom: 5px; font-weight: 600; color: #ffffff;">{p_full_name}</div>
                    <div style="font-size: 0.85em; color: #b0b0b0;">{p_email}</div>
                </td>
                <td style="padding: 12px;">
                    <div style="color: #e0e0e0;">📱 {p_phone}</div>
                    <div style="font-size: 0.85em; color: #b0b0b0;">📄 {p_document}</div>
                </td>
                <td style="padding: 12px; max-width: 200px; word-wrap: break-word; color: #e0e0e0;">{numbers_display}</td>
                <td style="padding: 12px;"><span style="{status_style}">{p_status.upper()}</span></td>
                <td class="actions" style="padding: 12px;">
                    <a href="/edit_purchase/{p_id}" style="text-decoration: none; padding: 8px 12px; background: linear-gradient(135deg, #2196F3, #1976D2); color: white; border-radius: 6px; margin-right: 5px; display: inline-block; font-weight: 600; box-shadow: 0 0 10px rgba(33, 150, 243, 0.5);">✏️ Editar</a>
                    <a href="/delete_purchase/{p_id}" style="text-decoration: none; padding: 8px 12px; background: linear-gradient(135deg, #f44336, #d32f2f); color: white; border-radius: 6px; display: inline-block; font-weight: 600; box-shadow: 0 0 10px rgba(244, 67, 54, 0.5);" onclick="return confirm('¿Estás seguro de eliminar esta compra?')">🗑️ Eliminar</a>
                </td>
            </tr>
            '''
        except Exception as e:
            logger.error(f"Error procesando fila: {e}")
            continue
    
    return table_rows


def assign_numbers(count):
    """Asigna números aleatorios disponibles"""
    rows = app_db.run_query("SELECT number FROM assigned_numbers", fetchall=True) or []
    assigned = set()
    for r in rows:
        try:
            assigned.add(int(r[0]))
        except Exception:
            try:
                assigned.add(int(r))
            except Exception:
                pass

    available = [n for n in range(1, 2001) if n not in assigned]

    if len(available) < count:
        raise ValueError("Not enough numbers available")

    selected = random.sample(available, count)
    selected.sort()
    return selected


def save_purchase(invoice_id, amount, email, numbers, **kwargs):
    """Guarda una compra con información adicional del cliente"""
    try:
        numbers_str = ','.join(map(str, numbers))
        
        full_name = kwargs.get('full_name')
        document_type = kwargs.get('document_type')
        document_number = kwargs.get('document_number')
        phone = kwargs.get('phone')
        address = kwargs.get('address')
        payment_method = kwargs.get('payment_method')
        bank_name = kwargs.get('bank_name')
        transaction_id = kwargs.get('transaction_id')
        franchise = kwargs.get('franchise')
        response_code = kwargs.get('response_code')

        try:
            app_db.run_query("""
                INSERT INTO purchases 
                (invoice_id, amount, email, numbers, status, full_name, document_type, 
                 document_number, phone, address, payment_method, bank_name, 
                 transaction_id, franchise, response_code, confirmed_at)
                VALUES (%s, %s, %s, %s, 'confirmed', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, params=(
                invoice_id, amount, email, numbers_str,
                full_name, document_type, document_number, phone, address,
                payment_method, bank_name, transaction_id, franchise, response_code,
                datetime.now()
            ), commit=True)
        except Exception as e:
            logger.warning(f"Trying fallback insert: {e}")
            app_db.run_query(
                "INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')",
                params=(invoice_id, amount, email, numbers_str), commit=True
            )

        for number in numbers:
            app_db.run_query(
                "INSERT INTO assigned_numbers (number, invoice_id, is_confirmed) VALUES (%s, %s, TRUE)", 
                params=(number, invoice_id), commit=True
            )
        
        logger.info(f"✅ Compra guardada exitosamente: {invoice_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error guardando compra {invoice_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_signature(data, signature):
    """Verifica la firma de ePayco"""
    if not EPAYCO_PRIVATE_KEY or not signature:
        return False

    sig_str = f"{data.get('x_ref_payco', '')}{data.get('x_transaction_id', '')}{data.get('x_amount', '')}{data.get('x_currency', '')}"
    expected_sig = hmac.new(EPAYCO_PRIVATE_KEY.encode(), sig_str.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_sig)


@app.route('/response')
def response():
    """Página de respuesta de ePayco"""
    ref_payco = request.args.get('ref_payco')
    transaction_id = request.args.get('transactionId')

    if not ref_payco:
        return "Error: No reference provided", 400

    purchase = app_db.run_query("SELECT * FROM purchases WHERE invoice_id = %s", params=(ref_payco,), fetchone=True)

    if purchase:
        numbers = purchase[4].split(',') if purchase[4] else []
        return send_from_directory('.', 'response.html')
    else:
        return send_from_directory('.', 'response.html')


@app.route('/confirmation', methods=['POST'])
def confirmation():
    """Confirmación de pago de ePayco"""
    data = request.form.to_dict()
    logger.info(f"Confirmation received: {data}")

    signature = request.headers.get('X-Signature')
    if not verify_signature(data, signature):
        logger.warning("Invalid signature")
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

    ref_payco = data.get('x_ref_payco')
    transaction_state = data.get('x_transaction_state')
    amount = data.get('x_amount')
    currency = data.get('x_currency')
    customer_email = data.get('x_customer_email')

    if transaction_state == 'Aceptada':
        try:
            amount_float = float(amount)
            num_tickets_map = {
                25000: 4,
                53000: 8,
                81000: 12,
                109000: 16,
                137000: 20
            }
            num_tickets = num_tickets_map.get(int(amount_float), 4)

            numbers = assign_numbers(num_tickets)
            
            client_info = {
                'full_name': data.get('x_customer_name', ''),
                'document_type': data.get('x_customer_doctype', ''),
                'document_number': data.get('x_customer_document', ''),
                'phone': data.get('x_customer_phone', '') or data.get('x_customer_mobile', ''),
                'address': data.get('x_customer_address', ''),
                'transaction_id': data.get('x_transaction_id', ''),
                'payment_method': data.get('x_type_payment', ''),
                'bank_name': data.get('x_bank_name', ''),
                'franchise': data.get('x_franchise', ''),
                'response_code': data.get('x_response', '')
            }
            
            save_purchase(ref_payco, amount_float, customer_email, numbers, **client_info)

            logger.info(f"Purchase confirmed: {ref_payco}, numbers: {numbers}")
            return jsonify({'status': 'success'}), 200

        except Exception as e:
            logger.error(f"Error processing purchase: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        logger.info(f"Payment not accepted: {transaction_state}")
        return jsonify({'status': 'pending'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)