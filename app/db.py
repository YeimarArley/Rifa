import os
import psycopg 
import sqlite3
import logging
from psycopg.rows import dict_row
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Configuración de base de datos
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'rifa_db')
DB_USER = os.getenv('DB_USER', 'rifa_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rifa_password')


def get_postgres_connection():
    """Crea conexión a PostgreSQL con psycopg 3"""
    try:
        # Opción 1: Usar DATABASE_URL si está disponible
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # psycopg 3 acepta directamente la URL
            return psycopg.connect(database_url, autocommit=False)
        
        # Opción 2: Usar credenciales individuales
        conninfo = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} sslmode=require"
        return psycopg.connect(conninfo, autocommit=False)
        
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {e}")
        raise


def get_db_connection():
    """Retorna conexión a Postgres o SQLite como fallback"""
    try:
        conn = get_postgres_connection()
        logger.info("✅ Conectado a PostgreSQL")
        return conn
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL no disponible, usando SQLite: {e}")
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rifa.db')
        conn = sqlite3.connect(sqlite_path)
        return conn


def init_db():
    """Inicializa las tablas de la base de datos"""
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        
        # Tabla de compras
        cur.execute('''CREATE TABLE IF NOT EXISTS purchases
                     (id SERIAL PRIMARY KEY,
                      invoice_id VARCHAR(255) UNIQUE NOT NULL,
                      amount DECIMAL(10,2) NOT NULL,
                      email VARCHAR(255) NOT NULL,
                      numbers TEXT NOT NULL,
                      status VARCHAR(50) DEFAULT 'pending',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      deleted_at TIMESTAMP,
                      notes TEXT,
                      full_name VARCHAR(255),
                      document_type VARCHAR(50),
                      document_number VARCHAR(100),
                      phone VARCHAR(50),
                      address TEXT,
                      payment_method VARCHAR(100),
                      bank_name VARCHAR(100),
                      transaction_id VARCHAR(255),
                      franchise VARCHAR(100),
                      response_code VARCHAR(50),
                      confirmed_at TIMESTAMP)''')
        
        # Tabla de números asignados
        cur.execute('''CREATE TABLE IF NOT EXISTS assigned_numbers
                     (number INTEGER PRIMARY KEY,
                      invoice_id VARCHAR(255),
                      assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      reserved_until TIMESTAMP,
                      is_confirmed BOOLEAN DEFAULT FALSE)''')
        
        # Tabla de configuración de números benditos
        cur.execute('''CREATE TABLE IF NOT EXISTS blessed_numbers_config
                     (id SERIAL PRIMARY KEY,
                      visible BOOLEAN DEFAULT FALSE,
                      scheduled_date TIMESTAMP,
                      numbers TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabla de usuarios admin
        cur.execute('''CREATE TABLE IF NOT EXISTS admin_users
                     (id SERIAL PRIMARY KEY,
                      email VARCHAR(255) UNIQUE NOT NULL,
                      password_hash VARCHAR(255) NOT NULL,
                      is_active BOOLEAN DEFAULT TRUE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabla de auditoría
        cur.execute('''CREATE TABLE IF NOT EXISTS audit_log
                     (id SERIAL PRIMARY KEY,
                      admin_user_id INTEGER,
                      action VARCHAR(50),
                      table_name VARCHAR(100),
                      record_id INTEGER,
                      old_values JSONB,
                      new_values JSONB,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Crear índices
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases(email)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_assigned_invoice ON assigned_numbers(invoice_id)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_assigned_confirmed ON assigned_numbers(is_confirmed)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_users(email)''')
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info('✅ Tablas PostgreSQL inicializadas correctamente')
        return
        
    except Exception as e:
        logger.warning(f'⚠️ No se pudo inicializar PostgreSQL, usando SQLite: {e}')
        
        # Fallback a SQLite
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rifa.db')
        try:
            sconn = sqlite3.connect(sqlite_path)
            sc = sconn.cursor()
            
            # Tabla de compras
            sc.execute('''CREATE TABLE IF NOT EXISTS purchases
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           invoice_id TEXT UNIQUE NOT NULL,
                           amount REAL NOT NULL,
                           email TEXT NOT NULL,
                           numbers TEXT NOT NULL,
                           status TEXT DEFAULT 'pending',
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           deleted_at TIMESTAMP,
                           notes TEXT,
                           full_name TEXT,
                           document_type TEXT,
                           document_number TEXT,
                           phone TEXT,
                           address TEXT,
                           payment_method TEXT,
                           bank_name TEXT,
                           transaction_id TEXT,
                           franchise TEXT,
                           response_code TEXT,
                           confirmed_at TIMESTAMP)''')
            
            # Tabla de números asignados
            sc.execute('''CREATE TABLE IF NOT EXISTS assigned_numbers
                          (number INTEGER PRIMARY KEY,
                           invoice_id TEXT,
                           assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           reserved_until TIMESTAMP,
                           is_confirmed INTEGER DEFAULT 0)''')
            
            # Tabla de configuración de números benditos
            sc.execute('''CREATE TABLE IF NOT EXISTS blessed_numbers_config
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           visible INTEGER DEFAULT 0,
                           scheduled_date TEXT,
                           numbers TEXT,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Tabla de usuarios admin
            sc.execute('''CREATE TABLE IF NOT EXISTS admin_users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           email TEXT UNIQUE NOT NULL,
                           password_hash TEXT NOT NULL,
                           is_active INTEGER DEFAULT 1,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Tabla de auditoría
            sc.execute('''CREATE TABLE IF NOT EXISTS audit_log
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           admin_user_id INTEGER,
                           action TEXT,
                           table_name TEXT,
                           record_id INTEGER,
                           old_values TEXT,
                           new_values TEXT,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            sconn.commit()
            sconn.close()
            logger.info('✅ Base de datos SQLite inicializada en: %s', sqlite_path)
            
        except Exception as e2:
            logger.error(f'❌ Error inicializando SQLite: {e2}')


def _is_sqlite_conn(conn):
    """Detecta si la conexión es SQLite"""
    return isinstance(conn, sqlite3.Connection)


def run_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """Ejecuta una query SQL en Postgres o SQLite"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        q = query
        p = params or ()
        
        # psycopg 3 usa placeholders %s igual que psycopg2
        # Convertir solo para SQLite
        if _is_sqlite_conn(conn):
            q = query.replace('%s', '?')

        cur.execute(q, p)

        result = None
        if commit:
            conn.commit()
        if fetchone:
            result = cur.fetchone()
        elif fetchall:
            result = cur.fetchall()

        return result
        
    except Exception as e:
        logger.error(f"Error ejecutando query: {e}")
        if conn:
            conn.rollback()
        raise
        
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def count_assigned_numbers():
    """Cuenta números asignados confirmados"""
    try:
        conn = get_db_connection()
        
        if _is_sqlite_conn(conn):
            # SQLite usa INTEGER (0 o 1)
            row = run_query(
                "SELECT COUNT(*) FROM assigned_numbers WHERE is_confirmed = 1", 
                fetchone=True
            )
        else:
            # PostgreSQL usa BOOLEAN
            row = run_query(
                "SELECT COUNT(*) FROM assigned_numbers WHERE is_confirmed = TRUE", 
                fetchone=True
            )
        
        if not row:
            return 0
        
        return int(row[0])
        
    except Exception as e:
        logger.error(f"Error contando números asignados: {e}")
        return 0


def get_purchase_by_id(purchase_id):
    """Obtiene una compra por ID"""
    return run_query(
        "SELECT * FROM purchases WHERE id = %s", 
        params=(purchase_id,), 
        fetchone=True
    )


def update_purchase(purchase_id, invoice_id, amount, email, numbers, status, notes=None):
    """Actualiza una compra existente"""
    try:
        run_query(
            """UPDATE purchases 
               SET invoice_id = %s, amount = %s, email = %s, numbers = %s, 
                   status = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            params=(invoice_id, amount, email, numbers, status, notes, purchase_id),
            commit=True
        )
        return True
    except Exception as e:
        logger.error(f"Error actualizando compra {purchase_id}: {e}")
        return False


def delete_purchase(purchase_id):
    """Elimina una compra y sus números asignados"""
    try:
        purchase = get_purchase_by_id(purchase_id)
        if not purchase:
            return False
        
        invoice_id = purchase[1]
        
        # Eliminar números asignados
        run_query(
            "DELETE FROM assigned_numbers WHERE invoice_id = %s",
            params=(invoice_id,),
            commit=True
        )
        
        # Soft delete de la compra
        run_query(
            "UPDATE purchases SET status = 'deleted', deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
            params=(purchase_id,),
            commit=True
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error eliminando compra {purchase_id}: {e}")
        return False


def log_audit(admin_user_id, action, table_name, record_id, old_values=None, new_values=None):
    """Registra una acción en la auditoría"""
    try:
        import json
        old_json = json.dumps(old_values) if old_values else None
        new_json = json.dumps(new_values) if new_values else None
        
        run_query(
            """INSERT INTO audit_log (admin_user_id, action, table_name, record_id, old_values, new_values)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            params=(admin_user_id, action, table_name, record_id, old_json, new_json),
            commit=True
        )
        return True
        
    except Exception as e:
        logger.error(f"Error registrando auditoría: {e}")
        return False