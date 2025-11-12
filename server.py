import os
import random
import logging
import hashlib
import hmac
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, abort, session
from dotenv import load_dotenv
from functools import wraps
import csv
from io import StringIO
from datetime import datetime, timedelta

# Importar módulos locales
from app import db as app_db
from app import validators

# Load environment variables
load_dotenv()

# Create Flask app early so routes can be registered
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Clave simple para admin de simulación (usa env var si está disponible)
ADMIN_SIM_KEY = os.getenv('ADMIN_SIM_KEY', 'CLAVEADMIN')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Decorador para requerir login en rutas admin
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Endpoint admin para simular compras y probar progreso ---
@app.route('/admin/simulate_purchase', methods=['POST'])
def admin_simulate_purchase():
    key = request.form.get('key')
    amount = int(request.form.get('amount', 4))
    email = request.form.get('email', 'test@demo.com')
    if key != ADMIN_SIM_KEY:
        abort(403)
    # Simula una compra con la cantidad indicada
    import uuid
    invoice_id = f"sim_{uuid.uuid4().hex[:10]}"
    try:
        numbers = assign_numbers(amount)
        save_purchase(invoice_id, amount*1000, email, numbers)
        return jsonify({
            'status': 'ok',
            'invoice_id': invoice_id,
            'numbers': numbers
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 400

# --- Rutas de autenticación admin ---
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('administrador'))
        else:
            return render_template('login.html', error='Contraseña incorrecta')
    return render_template('login.html')

@app.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

# Use centralized DB module
from app import db as app_db

# app ya fue creado arriba para permitir registros de rutas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database using app.db module (handles Postgres or sqlite fallback)
app_db.init_db()

# ePayco configuration
EPAYCO_PUBLIC_KEY = os.getenv('EPAYCO_PUBLIC_KEY', '70b19a05a3f3374085061d1bfd386a8b')
EPAYCO_PRIVATE_KEY = os.getenv('EPAYCO_PRIVATE_KEY', 'your_private_key_here')

# Email configuration
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))

# URLs
BASE_URL = os.getenv('BASE_URL', 'https://k-psico.com')
RESPONSE_URL = os.getenv('RESPONSE_URL', 'https://familiones.com/confirmation')
CONFIRMATION_URL = os.getenv('CONFIRMATION_URL', 'https://familiones.com/confirmation')

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

def assign_numbers(count):
    # Get assigned numbers using run_query
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

def save_purchase(invoice_id, amount, email, numbers):
    numbers_str = ','.join(map(str, numbers))

    # Insert purchase
    app_db.run_query("INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')",
                     params=(invoice_id, amount, email, numbers_str), commit=True)

    # Insert assigned numbers
    for number in numbers:
        app_db.run_query("INSERT INTO assigned_numbers (number, invoice_id) VALUES (%s, %s)", params=(number, invoice_id), commit=True)

def verify_signature(data, signature):
    if not EPAYCO_PRIVATE_KEY or not signature:
        return False

    # Create signature string
    sig_str = f"{data.get('x_ref_payco', '')}{data.get('x_transaction_id', '')}{data.get('x_amount', '')}{data.get('x_currency', '')}"

    # Calculate expected signature
    expected_sig = hmac.new(EPAYCO_PRIVATE_KEY.encode(), sig_str.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_sig)

@app.route('/')
def index():
    return render_template('index.html')

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

    # Log the incoming request
    logger.info(f"Confirmation received: {data}")

    # Verify signature
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
            # Determine number of tickets based on amount
            amount_float = float(amount)
            if amount_float == 25000:
                num_tickets = 4
            elif amount_float == 53000:
                num_tickets = 8
            elif amount_float == 81000:
                num_tickets = 12
            elif amount_float == 109000:
                num_tickets = 16
            elif amount_float == 137000:
                num_tickets = 20
            else:
                num_tickets = 4  # default

            numbers = assign_numbers(num_tickets)
            save_purchase(ref_payco, amount_float, customer_email, numbers)

            # Send confirmation email
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
def database():
    purchases = app_db.run_query("SELECT * FROM purchases ORDER BY created_at DESC LIMIT 50", fetchall=True) or []
    assigned_count = app_db.count_assigned_numbers()

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Administración de Base de Datos - Rifa</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }}
            .stats {{
                display: flex;
                justify-content: space-around;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
            }}
            .stat {{
                text-align: center;
            }}
            .stat h3 {{
                margin: 0;
                font-size: 2em;
            }}
            .stat p {{
                margin: 5px 0 0 0;
                opacity: 0.9;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .actions {{
                display: flex;
                gap: 10px;
            }}
            .btn {{
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                font-size: 0.9em;
            }}
            .btn-edit {{
                background-color: #2196F3;
                color: white;
            }}
            .btn-delete {{
                background-color: #f44336;
                color: white;
            }}
            .btn:hover {{
                opacity: 0.8;
            }}
            .back-link {{
                display: inline-block;
                margin-bottom: 20px;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
            .back-link:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Volver al Inicio</a>
            <h1>🗄️ Administración de Base de Datos - Rifa 5 Millones</h1>

            <div class="stats">
                <div class="stat">
                    <h3>{assigned_count}</h3>
                    <p>Números Asignados</p>
                </div>
                <div class="stat">
                    <h3>{2000 - assigned_count}</h3>
                    <p>Números Disponibles</p>
                </div>
                <div class="stat">
                    <h3>{len(purchases)}</h3>
                    <p>Total Compras</p>
                </div>
            </div>

            <h2>📋 Compras Recientes</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Referencia</th>
                        <th>Monto</th>
                        <th>Email</th>
                        <th>Números</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f'''
                    <tr>
                        <td>{p[0]}</td>
                        <td>{p[1]}</td>
                        <td>${p[2]:,.0f}</td>
                        <td>{p[3]}</td>
                        <td>{p[4]}</td>
                        <td>{p[5]}</td>
                        <td class="actions">
                            <a href="/edit_purchase/{p[0]}" class="btn btn-edit">Editar</a>
                            <a href="/delete_purchase/{p[0]}" class="btn btn-delete" onclick="return confirm('¿Estás seguro de eliminar esta compra?')">Eliminar</a>
                        </td>
                    </tr>
                    ''' for p in purchases)}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """


@app.route('/administrador')
@login_required
def administrador():
    # Parámetros de paginación y filtros
    page = request.args.get('page', 1, type=int)
    per_page = 15
    status_filter = request.args.get('status', '', type=str).strip()
    email_filter = request.args.get('email', '', type=str).strip()
    date_from = request.args.get('date_from', '', type=str).strip()
    date_to = request.args.get('date_to', '', type=str).strip()
    
    # Gather metrics
    total_numbers = 2000
    try:
        assigned_count = app_db.count_assigned_numbers() or 0
    except Exception:
        assigned_count = 0

    available_count = max(0, total_numbers - int(assigned_count))

    # Build WHERE clause for filters
    where_clause = "1=1"
    params = []
    if status_filter:
        where_clause += " AND status = %s"
        params.append(status_filter)
    if email_filter:
        where_clause += " AND email LIKE %s"
        params.append(f"%{email_filter}%")
    if date_from:
        where_clause += " AND DATE(created_at) >= %s"
        params.append(date_from)
    if date_to:
        where_clause += " AND DATE(created_at) <= %s"
        params.append(date_to)
    
    # Fetch total count for pagination
    total_query = f"SELECT COUNT(*) FROM purchases WHERE {where_clause}"
    total_result = app_db.run_query(total_query, params=tuple(params), fetchone=True)
    total_count = int(total_result[0]) if total_result else 0
    total_pages = (total_count + per_page - 1) // per_page
    
    # Ensure page is valid
    if page < 1:
        page = 1
    elif page > max(1, total_pages):
        page = max(1, total_pages)
    
    offset = (page - 1) * per_page
    
    # Fetch paginated purchases
    query = f"SELECT id, invoice_id, amount, email, numbers, status, created_at FROM purchases WHERE {where_clause} ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.append(per_page)
    params.append(offset)
    raw = app_db.run_query(query, params=tuple(params), fetchall=True) or []

    # Normalize rows to objects the template can use
    purchases = []
    for r in raw:
        try:
            if isinstance(r, dict):
                purchases.append(r)
            else:
                purchases.append({
                    'id': r[0],
                    'invoice_id': r[1],
                    'amount': r[2],
                    'email': r[3],
                    'numbers': r[4],
                    'status': r[5],
                    'created_at': r[6],
                })
        except Exception:
            purchases.append({'id': None, 'invoice_id': str(r), 'amount': '', 'email': '', 'numbers': '', 'status': '', 'created_at': ''})

    return render_template('administrador.html',
                           assigned_count=int(assigned_count),
                           available_count=int(available_count),
                           total_purchases=total_count,
                           purchases=purchases,
                           page=page,
                           total_pages=total_pages,
                           status_filter=status_filter,
                           email_filter=email_filter,
                           date_from=date_from,
                           date_to=date_to,
                           admin_key=ADMIN_SIM_KEY)

@app.route('/administrador/export_csv')
@login_required
def export_csv():
    """Exporta todas las compras a CSV"""
    try:
        # Obtener todas las compras
        raw = app_db.run_query("SELECT id, invoice_id, amount, email, numbers, status, created_at FROM purchases ORDER BY created_at DESC", fetchall=True) or []
        
        # Crear CSV en memoria
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Referencia', 'Monto', 'Email', 'Números', 'Estado', 'Fecha'])
        
        for r in raw:
            try:
                if isinstance(r, dict):
                    writer.writerow([r.get('id'), r.get('invoice_id'), r.get('amount'), r.get('email'), r.get('numbers'), r.get('status'), r.get('created_at')])
                else:
                    writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6]])
            except Exception:
                pass
        
        # Retornar como descarga
        from flask import Response
        csv_data = output.getvalue()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=compras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/administrador/stats')
@login_required
def admin_stats():
    """Retorna estadísticas en JSON para los gráficos con timeline y ingresos"""
    try:
        total_numbers = 2000
        assigned_count = app_db.count_assigned_numbers() or 0
        available_count = max(0, total_numbers - int(assigned_count))
        
        # Contar por estado
        confirmed = app_db.run_query("SELECT COUNT(*) FROM purchases WHERE status = %s", params=('confirmed',), fetchone=True)
        pending = app_db.run_query("SELECT COUNT(*) FROM purchases WHERE status = %s", params=('pending',), fetchone=True)
        cancelled = app_db.run_query("SELECT COUNT(*) FROM purchases WHERE status = %s", params=('cancelled',), fetchone=True)
        
        confirmed_count = int(confirmed[0]) if confirmed else 0
        pending_count = int(pending[0]) if pending else 0
        cancelled_count = int(cancelled[0]) if cancelled else 0
        
        # Ingresos totales (solo confirmed)
        revenue_result = app_db.run_query("SELECT SUM(amount) FROM purchases WHERE status = %s", params=('confirmed',), fetchone=True)
        total_revenue = float(revenue_result[0]) if revenue_result and revenue_result[0] else 0.0
        
        # Ingresos últimos 7 días
        seven_days_ago = datetime.now() - timedelta(days=7)
        revenue_7d = app_db.run_query(
            "SELECT SUM(amount) FROM purchases WHERE status = %s AND created_at >= %s",
            params=('confirmed', seven_days_ago),
            fetchone=True
        )
        revenue_7d_value = float(revenue_7d[0]) if revenue_7d and revenue_7d[0] else 0.0
        
        # Promedio por compra
        avg_revenue = total_revenue / confirmed_count if confirmed_count > 0 else 0.0
        
        # Top 5 emails por ingresos
        top_emails = app_db.run_query(
            "SELECT email, COUNT(*) as count, SUM(amount) as total FROM purchases WHERE status = %s GROUP BY email ORDER BY total DESC LIMIT 5",
            params=('confirmed',),
            fetchall=True
        ) or []
        
        top_customers = []
        for row in top_emails:
            try:
                if isinstance(row, dict):
                    top_customers.append({'email': row.get('email'), 'purchases': row.get('count'), 'total': row.get('total')})
                else:
                    top_customers.append({'email': row[0], 'purchases': int(row[1]), 'total': float(row[2])})
            except Exception:
                pass
        
        return jsonify({
            'assigned': assigned_count,
            'available': available_count,
            'total': total_numbers,
            'percentage': round((assigned_count / total_numbers) * 100, 1),
            'statuses': {
                'confirmed': confirmed_count,
                'pending': pending_count,
                'cancelled': cancelled_count
            },
            'revenue': {
                'total': round(total_revenue, 2),
                'last_7_days': round(revenue_7d_value, 2),
                'average_per_sale': round(avg_revenue, 2),
                'confirmed_count': confirmed_count
            },
            'top_customers': top_customers
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/administrador/stats_timeline')
@login_required
def admin_stats_timeline():
    """Retorna datos de ventas por día (últimos 7 días) para gráfico de línea"""
    try:
        timeline_data = {}
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).date()
            date_str = date.strftime('%Y-%m-%d')
            
            result = app_db.run_query(
                "SELECT COUNT(*), SUM(amount) FROM purchases WHERE status = %s AND DATE(created_at) = %s",
                params=('confirmed', date_str),
                fetchone=True
            )
            
            count = int(result[0]) if result and result[0] else 0
            amount = float(result[1]) if result and result[1] else 0.0
            
            timeline_data[date_str] = {'count': count, 'amount': amount}
        
        return jsonify({
            'timeline': timeline_data,
            'dates': sorted(timeline_data.keys()),
            'counts': [timeline_data[d]['count'] for d in sorted(timeline_data.keys())],
            'amounts': [round(timeline_data[d]['amount'], 2) for d in sorted(timeline_data.keys())]
        })
    except Exception as e:
        logger.error(f"Error fetching timeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/edit_purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def edit_purchase(purchase_id):
    """Edita una compra existente"""
    # Validar ID
    is_valid, purchase_id_clean = validators.validate_purchase_id(purchase_id)
    if not is_valid:
        return render_template('error.html', message='ID de compra inválido'), 400
    
    if request.method == 'POST':
        try:
            invoice_id = request.form.get('invoice_id', '').strip()
            amount = request.form.get('amount', '')
            email = request.form.get('email', '').strip()
            numbers = request.form.get('numbers', '').strip()
            status = request.form.get('status', 'pending').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validar todos los datos
            is_valid, result = validators.validate_purchase_data(invoice_id, amount, email, numbers, status, notes)
            
            if not is_valid:
                purchase = app_db.get_purchase_by_id(purchase_id_clean)
                return render_template('edit_purchase.html',
                                     error=result,
                                     purchase_id=purchase_id_clean,
                                     purchase=purchase), 400
            
            # Actualizar compra
            if app_db.update_purchase(purchase_id_clean, result['invoice_id'], result['amount'],
                                     result['email'], result['numbers'], result['status'], result['notes']):
                logger.info(f"Purchase {purchase_id_clean} updated by admin. Invoice: {result['invoice_id']}")
                return redirect(url_for('administrador'))
            else:
                return render_template('edit_purchase.html',
                                     error='Error al actualizar la compra',
                                     purchase_id=purchase_id_clean), 500
                                     
        except Exception as e:
            logger.error(f"Error in edit_purchase POST: {e}")
            return render_template('edit_purchase.html',
                                 error=f'Error: {str(e)}',
                                 purchase_id=purchase_id_clean), 500
    
    # GET request - mostrar formulario de edición
    try:
        purchase = app_db.get_purchase_by_id(purchase_id_clean)
        
        if not purchase:
            return render_template('error.html', message='Compra no encontrada'), 404
        
        # Normalizar data
        if isinstance(purchase, dict):
            purchase_data = {
                'id': purchase.get('id'),
                'invoice_id': purchase.get('invoice_id'),
                'amount': purchase.get('amount'),
                'email': purchase.get('email'),
                'numbers': purchase.get('numbers'),
                'status': purchase.get('status'),
                'notes': purchase.get('notes', ''),
                'created_at': purchase.get('created_at'),
            }
        else:
            purchase_data = {
                'id': purchase[0],
                'invoice_id': purchase[1],
                'amount': purchase[2],
                'email': purchase[3],
                'numbers': purchase[4],
                'status': purchase[5],
                'notes': purchase[9] if len(purchase) > 9 else '',
                'created_at': purchase[6],
            }
        
        return render_template('edit_purchase.html', purchase=purchase_data)
        
    except Exception as e:
        logger.error(f"Error in edit_purchase GET: {e}")
        return render_template('error.html', message=f'Error: {str(e)}'), 500

@app.route('/delete_purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
def delete_purchase(purchase_id):
    """Elimina una compra (soft delete o hard delete)"""
    # Validar ID
    is_valid, purchase_id_clean = validators.validate_purchase_id(purchase_id)
    if not is_valid:
        return render_template('error.html', message='ID de compra inválido'), 400
    
    try:
        if request.method == 'POST':
            force_delete = request.form.get('force_delete', 'false').lower() == 'true'
            
            if force_delete:
                # Hard delete - eliminar permanentemente
                if app_db.force_delete_purchase(purchase_id_clean):
                    logger.warning(f"Purchase {purchase_id_clean} PERMANENTLY DELETED by admin")
                else:
                    return render_template('delete_purchase.html',
                                         purchase_id=purchase_id_clean,
                                         error='Error al eliminar la compra'), 500
            else:
                # Soft delete - marcar como eliminada
                if app_db.delete_purchase(purchase_id_clean):
                    logger.info(f"Purchase {purchase_id_clean} marked as deleted by admin")
                else:
                    return render_template('delete_purchase.html',
                                         purchase_id=purchase_id_clean,
                                         error='Error al eliminar la compra'), 500
            
            return redirect(url_for('administrador'))
        
        # GET request - mostrar confirmación
        purchase = app_db.get_purchase_by_id(purchase_id_clean)
        
        if not purchase:
            return render_template('error.html', message='Compra no encontrada'), 404
        
        # Normalizar data
        if isinstance(purchase, dict):
            purchase_data = {
                'id': purchase.get('id'),
                'invoice_id': purchase.get('invoice_id'),
                'amount': purchase.get('amount'),
                'email': purchase.get('email'),
                'numbers': purchase.get('numbers'),
            }
        else:
            purchase_data = {
                'id': purchase[0],
                'invoice_id': purchase[1],
                'amount': purchase[2],
                'email': purchase[3],
                'numbers': purchase[4],
            }
        
        return render_template('delete_purchase.html', purchase=purchase_data)
        
    except Exception as e:
        logger.error(f"Error in delete_purchase: {e}")
        return render_template('error.html', message=f'Error: {str(e)}'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
