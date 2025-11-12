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
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, abort
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app early so routes can be registered
app = Flask(__name__)

# Clave simple para admin de simulación (usa env var si está disponible)
ADMIN_SIM_KEY = os.getenv('ADMIN_SIM_KEY', 'CLAVEADMIN')

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

# Use centralized DB module
from app import db as app_db

# app ya fue creado arriba para permitir registros de rutas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database using app.db module (handles Postgres or sqlite fallback)
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
    """Panel de administración de la base de datos con manejo de errores mejorado."""
    try:
        # Obtener compras con manejo de errores
        try:
            purchases = app_db.run_query(
                "SELECT * FROM purchases ORDER BY created_at DESC LIMIT 50", 
                fetchall=True
            ) or []
        except Exception as e:
            logger.error(f"Error obteniendo compras: {e}")
            purchases = []
        
        # Contar números asignados con manejo de errores
        try:
            assigned_count = app_db.count_assigned_numbers()
        except Exception as e:
            logger.error(f"Error contando números: {e}")
            assigned_count = 0
        
        # Generar filas de la tabla de manera segura
        table_rows = ""
        if purchases:
            for p in purchases:
                try:
                    # Asegurar que todos los valores existan
                    p_id = p[0] if len(p) > 0 else 'N/A'
                    p_invoice = p[1] if len(p) > 1 else 'N/A'
                    p_amount = p[2] if len(p) > 2 else 0
                    p_email = p[3] if len(p) > 3 else 'N/A'
                    p_numbers = p[4] if len(p) > 4 else ''
                    p_status = p[5] if len(p) > 5 else 'pending'
                    
                    table_rows += f'''
                    <tr>
                        <td>{p_id}</td>
                        <td>{p_invoice}</td>
                        <td>${float(p_amount):,.0f}</td>
                        <td>{p_email}</td>
                        <td>{p_numbers}</td>
                        <td>{p_status}</td>
                        <td class="actions">
                            <a href="/edit_purchase/{p_id}" class="btn btn-edit">Editar</a>
                            <a href="/delete_purchase/{p_id}" class="btn btn-delete" onclick="return confirm('¿Estás seguro de eliminar esta compra?')">Eliminar</a>
                        </td>
                    </tr>
                    '''
                except Exception as e:
                    logger.error(f"Error procesando fila: {e}")
                    continue
        else:
            table_rows = '''
                <tr>
                    <td colspan="7" style="text-align: center; padding: 20px; color: #666;">
                        No hay compras registradas aún
                    </td>
                </tr>
            '''

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
                .db-info {{
                    background: #e3f2fd;
                    padding: 10px 15px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                    border-left: 4px solid #2196F3;
                }}
                .db-info strong {{
                    color: #1976d2;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-link">← Volver al Inicio</a>
                
                <div class="db-info">
                    <strong>✓ Conectado a PostgreSQL en Neon</strong> - Base de datos en la nube
                </div>
                
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
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error crítico en endpoint /database: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Error - Base de Datos</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 40px;
                    background: #f5f5f5;
                }}
                .error-box {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    max-width: 800px;
                    margin: 0 auto;
                    border-left: 4px solid #f44336;
                }}
                h1 {{
                    color: #f44336;
                }}
                pre {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 4px;
                    overflow-x: auto;
                }}
                .back-link {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>❌ Error en Base de Datos</h1>
                <p>No se pudo cargar el panel de administración.</p>
                <h3>Detalles del error:</h3>
                <pre>{str(e)}</pre>
                <p><strong>Posibles soluciones:</strong></p>
                <ul>
                    <li>Verifica que PostgreSQL en Neon esté accesible</li>
                    <li>Asegúrate de que las tablas existan: ejecuta <code>python reset_db_simple.py</code></li>
                    <li>Revisa los logs del servidor en la terminal</li>
                </ul>
                <a href="/" class="back-link">← Volver al Inicio</a>
            </div>
        </body>
        </html>
        """, 500

@app.route('/edit_purchase/<int:purchase_id>', methods=['GET', 'POST'])
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Compra - Rifa</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 600px;
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
            .form-group {{
                margin-bottom: 15px;
            }}
            label {{
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }}
            input, select {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 1em;
            }}
            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1em;
                margin-right: 10px;
            }}
            .btn-save {{
                background-color: #4CAF50;
                color: white;
            }}
            .btn-cancel {{
                background-color: #f44336;
                color: white;
            }}
            .btn:hover {{
                opacity: 0.8;
            }}
            .actions {{
                text-align: center;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✏️ Editar Compra</h1>
            <form method="POST">
                <div class="form-group">
                    <label for="invoice_id">Referencia de Pago:</label>
                    <input type="text" id="invoice_id" name="invoice_id" value="{purchase[1]}" required>
                </div>
                <div class="form-group">
                    <label for="amount">Monto:</label>
                    <input type="number" id="amount" name="amount" value="{purchase[2]}" step="0.01" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" value="{purchase[3]}" required>
                </div>
                <div class="form-group">
                    <label for="numbers">Números:</label>
                    <input type="text" id="numbers" name="numbers" value="{purchase[4]}" required>
                </div>
                <div class="form-group">
                    <label for="status">Estado:</label>
                    <select id="status" name="status">
                        <option value="pending" {'selected' if purchase[5] == 'pending' else ''}>Pendiente</option>
                        <option value="confirmed" {'selected' if purchase[5] == 'confirmed' else ''}>Confirmado</option>
                        <option value="cancelled" {'selected' if purchase[5] == 'cancelled' else ''}>Cancelado</option>
                    </select>
                </div>
                <div class="actions">
                    <button type="submit" class="btn btn-save">💾 Guardar Cambios</button>
                    <a href="/database" class="btn btn-cancel">❌ Cancelar</a>
                </div>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/delete_purchase/<int:purchase_id>')
def delete_purchase(purchase_id):
    purchase = app_db.run_query("SELECT numbers FROM purchases WHERE id = %s", params=(purchase_id,), fetchone=True)

    if purchase:
        numbers_str = purchase[0] if isinstance(purchase, (list, tuple)) else purchase
        if numbers_str:
            numbers = [int(n.strip()) for n in numbers_str.split(',')]
            # Remove from assigned_numbers
            for number in numbers:
                app_db.run_query("DELETE FROM assigned_numbers WHERE number = %s", params=(number,), commit=True)

        # Delete the purchase
        app_db.run_query("DELETE FROM purchases WHERE id = %s", params=(purchase_id,), commit=True)
    return redirect('/database')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
