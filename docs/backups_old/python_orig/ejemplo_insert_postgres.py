
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuración de conexión
DB_PARAMS = {
    'dbname': 'tu_db',
    'user': 'tu_usuario',
    'password': 'tu_password',
    'host': 'localhost',
    'port': 5432
}

def get_conn():
    return psycopg2.connect(**DB_PARAMS)

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.json
    nombre = data['name']
    email = data['email']
    phone = data['phone']
    amount = data['amount']
    quantity = data['quantity']
    numbers = data['numbers']  # lista de números
    invoice_id = data['invoice_id']
    try:
        conn = get_conn()
        cur = conn.cursor()
        # Insertar participante (si no existe)
        cur.execute('''
            INSERT INTO participants (name, email, phone)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name, phone=EXCLUDED.phone
            RETURNING id;
        ''', (nombre, email, phone))
        participant_id = cur.fetchone()[0]
        # Insertar compra
        cur.execute('''
            INSERT INTO purchases (invoice_id, participant_id, amount, email, quantity, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        ''', (invoice_id, participant_id, amount, email, quantity, 'pending'))
        purchase_id = cur.fetchone()[0]
        # Insertar números asignados
        for num in numbers:
            cur.execute('''
                INSERT INTO assigned_numbers (number, purchase_id, participant_id)
                VALUES (%s, %s, %s)
            ''', (num, purchase_id, participant_id))
        conn.commit()
        return jsonify({'status': 'ok', 'msg': 'Registro exitoso'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
