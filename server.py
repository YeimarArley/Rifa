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


# ========== AGREGAR ESTA FUNCIÓN EN server.py (después de la configuración de Mail) ==========

def send_purchase_confirmation_email(customer_email, customer_name, numbers, amount, invoice_id):
    """
    Envía email de confirmación de compra con los números asignados
    """
    try:
        logger.info(f"📧 Preparando email para {customer_email}...")
        
        # Verificar configuración
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            logger.warning("⚠️ Credenciales de email no configuradas")
            return False
        
        # Crear mensaje
        msg = Message(
            subject='✅ ¡Confirmación de Compra - Rifa 5 Millones! 🎉',
            recipients=[customer_email],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Formatear los números
        numbers_formatted = ', '.join([str(num) for num in numbers])
        
        # Crear el cuerpo del email en HTML
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
        
        # Versión de texto plano (fallback)
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
        
        # Enviar el email
        mail.send(msg)
        logger.info(f"✅ Email enviado exitosamente a {customer_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email a {customer_email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production-super-secret-key')

# Clave simple para admin de simulación
ADMIN_SIM_KEY = os.getenv('ADMIN_SIM_KEY', 'CLAVEADMIN')

# Use centralized DB module
from app import db as app_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
try:
    app_db.init_db()
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    import traceback
    traceback.print_exc()

# ePayco configuration
EPAYCO_PUBLIC_KEY = os.getenv('EPAYCO_PUBLIC_KEY', '70b19a05a3f3374085061d1bfd386a8b')
EPAYCO_PRIVATE_KEY = os.getenv('EPAYCO_PRIVATE_KEY', 'your_private_key_here')

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))  # 587 por defecto
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Validar configuración
if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    logger.warning("⚠️ Credenciales de email no configuradas")

# Inicializar Mail
mail = Mail(app)

# URLs
BASE_URL = os.getenv('BASE_URL', 'https://k-psico.com')
RESPONSE_URL = os.getenv('RESPONSE_URL', 'https://familiones.com/confirmation')
CONFIRMATION_URL = os.getenv('CONFIRMATION_URL', 'https://familiones.com/confirmation')

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', hashlib.sha256('admin123'.encode()).hexdigest())


# ==================== AUTHENTICATION ====================

def login_required(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def hash_password(password):
    """Hashea una contraseña con SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login de administrador"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        password_hash = hash_password(password)
        
        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            logger.info(f"Admin login successful: {username}")
            return redirect('/database')
        else:
            logger.warning(f"Failed admin login attempt: {username}")
            return render_template('admin_login.html', error="Credenciales incorrectas")
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Logout de administrador"""
    session.clear()
    return redirect('/')


# ==================== BLESSED NUMBERS MANAGEMENT ====================

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


@app.route('/api/blessed_numbers_status')
def api_blessed_numbers_status():
    """API mejorada para obtener el estado de los números benditos"""
    try:
        config = get_blessed_numbers_config()
        
        # Verificar si es una fecha programada
        now = datetime.now()
        visible = config['visible']
        show_date = None
        
        if config['scheduled_date'] and not visible:
            try:
                scheduled = datetime.fromisoformat(config['scheduled_date'])
                if now >= scheduled:
                    visible = True
                    # Actualizar visibilidad automáticamente
                    save_blessed_numbers_config(True, config['scheduled_date'], config['numbers'])
                else:
                    # Calcular tiempo restante
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


@app.route('/admin/blessed_numbers', methods=['GET', 'POST'])
@login_required
def admin_blessed_numbers():
    """Panel de administración de números benditos mejorado"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save':
            # Guardar configuración completa
            visible = request.form.get('visible') == 'on'
            scheduled_date = request.form.get('scheduled_date') or None
            number1 = request.form.get('number1', '').strip()
            number2 = request.form.get('number2', '').strip()
            
            # Validar números
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
            
            # Guardar configuración
            save_blessed_numbers_config(visible, scheduled_date, numbers if numbers else None)
            
            return redirect('/admin/blessed_numbers?success=1')
        
        elif action == 'delete':
            # Eliminar configuración
            save_blessed_numbers_config(False, None, None)
            return redirect('/admin/blessed_numbers?deleted=1')
    
    # GET request
    config = get_blessed_numbers_config()
    success = request.args.get('success')
    deleted = request.args.get('deleted')
    
    return render_template('admin_blessed_numbers.html', 
                         config=config, 
                         success=success,
                         deleted=deleted)


# ==================== METRICS CALCULATION ====================

def calculate_metrics(date_from=None, date_to=None):
    """Calcula métricas del sistema"""
    try:
        metrics = {}
        
        # Construir condición de fecha
        date_condition = "WHERE status = 'confirmed'"
        params = []
        
        if date_from:
            date_condition += " AND created_at >= %s"
            params.append(date_from)
        if date_to:
            date_condition += " AND created_at <= %s"
            params.append(date_to)
        
        # Total de compras
        result = app_db.run_query(
            f"SELECT COUNT(*) FROM purchases {date_condition}",
            params=tuple(params) if params else None,
            fetchone=True
        )
        metrics['total_purchases'] = result[0] if result else 0
        
        # Ingresos totales
        result = app_db.run_query(
            f"SELECT SUM(amount) FROM purchases {date_condition}",
            params=tuple(params) if params else None,
            fetchone=True
        )
        metrics['total_revenue'] = float(result[0]) if result and result[0] else 0.0
        
        # Números vendidos
        metrics['numbers_sold'] = app_db.count_assigned_numbers()
        metrics['numbers_available'] = 2000 - metrics['numbers_sold']
        metrics['percentage_sold'] = (metrics['numbers_sold'] / 2000) * 100
        
        # Ventas por día (últimos 7 días)
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
        
        # Promedio por compra
        if metrics['total_purchases'] > 0:
            metrics['average_purchase'] = metrics['total_revenue'] / metrics['total_purchases']
        else:
            metrics['average_purchase'] = 0.0
        
        # Paquete más vendido
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
            # Extraer datos de manera segura
            p_id = p[0] if len(p) > 0 else 'N/A'
            p_invoice = p[1] if len(p) > 1 else 'N/A'
            p_amount = p[2] if len(p) > 2 else 0
            p_email = p[3] if len(p) > 3 else 'N/A'
            p_numbers = p[4] if len(p) > 4 else ''
            p_status = p[5] if len(p) > 5 else 'pending'
            
            # Nuevos campos
            p_full_name = p[10] if len(p) > 10 and p[10] else 'No especificado'
            p_document = p[12] if len(p) > 12 and p[12] else 'N/A'
            p_phone = p[13] if len(p) > 13 and p[13] else 'N/A'
            
            # Estilos por estado - TEMA OSCURO
            status_styles = {
                'confirmed': 'background: linear-gradient(135deg, #4CAF50, #45a049); color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 700; box-shadow: 0 0 15px rgba(76, 175, 80, 0.5);',
                'pending': 'background: linear-gradient(135deg, #FFA500, #FF8C00); color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 700; box-shadow: 0 0 15px rgba(255, 165, 0, 0.5);',
                'cancelled': 'background: linear-gradient(135deg, #f44336, #d32f2f); color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: 700; box-shadow: 0 0 15px rgba(244, 67, 54, 0.5);'
            }
            status_style = status_styles.get(p_status, '')
            
            # Truncar números si son muchos
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


# ==================== EMAIL FUNCTIONS ====================

def send_email(to_email, subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        server.quit()
        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


# ==================== NUMBERS ASSIGNMENT ====================

def assign_numbers(count):
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
        
        # Extraer información adicional
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

        # Insertar números asignados
        for number in numbers:
            app_db.run_query(
                "INSERT INTO assigned_numbers (number, invoice_id, is_confirmed) VALUES (%s, %s, TRUE)", 
                params=(number, invoice_id), commit=True
            )
        
        logger.info(f"✅ Compra guardada exitosamente: {invoice_id}")
        return True  # ← IMPORTANTE: Devolver True si todo salió bien
        
    except Exception as e:
        logger.error(f"❌ Error guardando compra {invoice_id}: {e}")
        import traceback
        traceback.print_exc()
        return False  # ← IMPORTANTE: Devolver False si falló



def verify_signature(data, signature):
    if not EPAYCO_PRIVATE_KEY or not signature:
        return False

    sig_str = f"{data.get('x_ref_payco', '')}{data.get('x_transaction_id', '')}{data.get('x_amount', '')}{data.get('x_currency', '')}"
    expected_sig = hmac.new(EPAYCO_PRIVATE_KEY.encode(), sig_str.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_sig)


# ==================== ROUTES ====================

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index.html: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading page: {str(e)}", 500


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


@app.route('/response')
def response():
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

            numbers_str = ', '.join(map(str, numbers))
            email_body = f"""
            <h2>¡Felicitaciones! Tu compra ha sido confirmada</h2>
            <p>Referencia de pago: {ref_payco}</p>
            <p>Monto: ${amount} {currency}</p>
            <p>Números asignados: {numbers_str}</p>
            <p>¡Buena suerte en la rifa!</p>
            """
            send_email(customer_email, "Confirmación de compra - Rifa 5 Millones", email_body)

            logger.info(f"Purchase confirmed: {ref_payco}, numbers: {numbers}")
            return jsonify({'status': 'success'}), 200

        except Exception as e:
            logger.error(f"Error processing purchase: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        logger.info(f"Payment not accepted: {transaction_state}")
        return jsonify({'status': 'pending'}), 200


@app.route('/progress')
def progress():
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


@app.route('/database')
@login_required
def database():
    """Panel de administración mejorado con búsqueda y métricas"""
    try:
        # Obtener parámetros de búsqueda
        search_query = request.args.get('search', '').strip()
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        status_filter = request.args.get('status', '')
        
        # Construir query base
        query = "SELECT * FROM purchases WHERE 1=1"
        params = []
        
        # Aplicar filtros
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
        
        # Excluir eliminados
        query += " AND (status != 'deleted' OR status IS NULL)"
        query += " ORDER BY created_at DESC LIMIT 100"
        
        # Ejecutar query
        purchases = app_db.run_query(query, params=tuple(params) if params else None, fetchall=True) or []
        
        # Calcular métricas
        metrics = calculate_metrics(date_from, date_to)
        
        # Generar HTML de la tabla
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


@app.route('/edit_purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def edit_purchase(purchase_id):
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

        return redirect('/database')

    purchase = app_db.run_query("SELECT * FROM purchases WHERE id = %s", params=(purchase_id,), fetchone=True)

    if not purchase:
        return "Compra no encontrada", 404

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
    purchase = app_db.run_query("SELECT numbers FROM purchases WHERE id = %s", params=(purchase_id,), fetchone=True)

    if purchase:
        numbers_str = purchase[0] if isinstance(purchase, (list, tuple)) else purchase
        if numbers_str:
            numbers = [int(n.strip()) for n in numbers_str.split(',')]
            for number in numbers:
                app_db.run_query("DELETE FROM assigned_numbers WHERE number = %s", params=(number,), commit=True)

        app_db.run_query("DELETE FROM purchases WHERE id = %s", params=(purchase_id,), commit=True)
    return redirect('/database')


# ==================== ADMIN SIMULATION ====================

@app.route('/admin/simulate_purchase', methods=['POST'])
def simulate_purchase():
    """Simula una compra para testing - CON LOGS DETALLADOS"""
    key = request.form.get('key')
    
    logger.info(f"🔑 Clave recibida: {key}")
    logger.info(f"🔑 Clave esperada: {ADMIN_SIM_KEY}")
    
    if key != ADMIN_SIM_KEY:
        logger.warning("❌ Clave admin incorrecta")
        abort(403)
    
    try:
        amount = int(request.form.get('amount', 4))
        email = request.form.get('email', 'test@demo.com')
        customer_name = request.form.get('name', 'Cliente de Prueba')
        
        logger.info(f"📊 Parámetros: amount={amount}, email={email}, name={customer_name}")
        
        # 1. Asignar números
        logger.info("🎲 Asignando números...")
        numbers = assign_numbers(amount)
        
        if not numbers:
            logger.error("❌ No hay números disponibles")
            return jsonify({
                "status": "error",
                "message": "Not enough numbers available"
            }), 400
        
        logger.info(f"✅ Números asignados: {numbers}")
        
        # 2. Crear factura
        invoice_id = f"sim_{uuid.uuid4().hex[:12]}"
        amount_value = amount * 6250  # $6,250 por número
        
        logger.info(f"💰 Invoice: {invoice_id}, Amount: ${amount_value:,}")
        
        # 3. Guardar en base de datos
        logger.info("💾 Guardando en base de datos...")
        saved = save_purchase(
            invoice_id=invoice_id,
            amount=amount_value,
            email=email,
            numbers=numbers,
            full_name=customer_name  # ← Pasar el nombre
        )
        
        if not saved:
            logger.error("❌ Error guardando en base de datos")
            return jsonify({
                "status": "error",
                "message": "Database error - check server logs"
            }), 500
        
        logger.info("✅ Guardado en base de datos exitosamente")
        
        # 4. Enviar email
        logger.info("📧 Enviando email de confirmación...")
        try:
            email_sent = send_purchase_confirmation_email(
                customer_email=email,
                customer_name=customer_name,
                numbers=numbers,
                amount=amount_value,
                invoice_id=invoice_id
            )
            
            if email_sent:
                logger.info(f"✅ Email enviado a {email}")
            else:
                logger.warning(f"⚠️ Email no se pudo enviar a {email}")
        except Exception as email_error:
            logger.error(f"❌ Error enviando email: {email_error}")
            # No fallar la compra si el email falla
        
        # 5. Devolver respuesta exitosa
        logger.info("🎉 Compra simulada completada exitosamente")
        return jsonify({
            "status": "ok",
            "invoice_id": invoice_id,
            "numbers": numbers,
            "email_sent": email_sent if 'email_sent' in locals() else False
        })
            
    except Exception as e:
        logger.error(f"💥 Error crítico en simulate_purchase: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)