import os
import psycopg2
import sqlite3
import logging
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Cadena de conexión a Neon PostgreSQL
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_j7im9lcwxGBM@ep-dark-feather-adbcf7hh-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'
)

# Variables individuales como fallback
DB_HOST = os.getenv('DB_HOST', 'ep-dark-feather-adbcf7hh-pooler.c-2.us-east-1.aws.neon.tech')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'neondb')
DB_USER = os.getenv('DB_USER', 'neondb_owner')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'npg_j7im9lcwxGBM')


def get_postgres_connection():
    """Conecta a PostgreSQL usando DATABASE_URL o variables individuales."""
    try:
        if DATABASE_URL and DATABASE_URL.startswith('postgres'):
            logger.info("Conectando a PostgreSQL (Neon) usando DATABASE_URL")
            conn = psycopg2.connect(DATABASE_URL)
            logger.info("✓ Conexión exitosa a PostgreSQL en Neon")
            return conn
        else:
            logger.info("Conectando a PostgreSQL usando variables individuales")
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                sslmode='require'
            )
            logger.info("✓ Conexión exitosa a PostgreSQL")
            return conn
    except Exception as e:
        logger.error(f"✗ Error conectando a PostgreSQL: {e}")
        raise


def get_db_connection():
    """Retorna conexión a Postgres. NO usa SQLite como fallback en producción."""
    try:
        conn = get_postgres_connection()
        return conn
    except Exception as e:
        logger.critical(f"❌ PostgreSQL no disponible y NO hay fallback configurado: {e}")
        logger.critical("El sistema REQUIERE PostgreSQL para funcionar")
        raise Exception("No se puede conectar a PostgreSQL. Verifica tu conexión a Neon.") from e


def table_exists(table_name):
    """Verifica si una tabla existe en PostgreSQL."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else False
    except Exception as e:
        logger.error(f"Error verificando tabla {table_name}: {e}")
        return False


def get_table_columns(table_name):
    """Obtiene las columnas de una tabla."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cur.fetchall()
        cur.close()
        conn.close()
        return [col[0] for col in columns] if columns else []
    except Exception as e:
        logger.error(f"Error obteniendo columnas de {table_name}: {e}")
        return []


def init_db():
    """Inicializa las tablas en PostgreSQL."""
    try:
        conn = get_postgres_connection()
        c = conn.cursor()
        
        # Verificar si las tablas ya existen
        purchases_exists = table_exists('purchases')
        assigned_exists = table_exists('assigned_numbers')
        
        if purchases_exists and assigned_exists:
            logger.info('✓ Las tablas ya existen en PostgreSQL')
            
            # Verificar columnas de purchases
            purchases_cols = get_table_columns('purchases')
            logger.info(f'  Columnas en purchases: {", ".join(purchases_cols)}')
            
            # Verificar columnas de assigned_numbers
            assigned_cols = get_table_columns('assigned_numbers')
            logger.info(f'  Columnas en assigned_numbers: {", ".join(assigned_cols)}')
            
            conn.close()
            return True
        
        # Si no existen, crearlas
        logger.info('Creando tablas en PostgreSQL...')
        
        # Tabla de compras
        c.execute('''CREATE TABLE IF NOT EXISTS purchases
                     (id SERIAL PRIMARY KEY,
                      invoice_id VARCHAR(255) UNIQUE NOT NULL,
                      amount DECIMAL(10,2) NOT NULL,
                      email VARCHAR(255) NOT NULL,
                      numbers TEXT NOT NULL,
                      status VARCHAR(50) DEFAULT 'pending',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabla de números asignados
        c.execute('''CREATE TABLE IF NOT EXISTS assigned_numbers
                     (number INTEGER PRIMARY KEY,
                      invoice_id VARCHAR(255) NOT NULL,
                      assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Índices para mejorar rendimiento
        c.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases(email)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_assigned_invoice ON assigned_numbers(invoice_id)''')
        
        conn.commit()
        conn.close()
        logger.info('✓ Tablas creadas correctamente en PostgreSQL')
        return True
        
    except Exception as e:
        logger.error(f'✗ Error inicializando PostgreSQL: {e}')
        raise


def _is_sqlite_conn(conn):
    """Detecta si la conexión es SQLite - Ya no se usa."""
    return isinstance(conn, sqlite3.Connection)


def get_db_type():
    """Detecta el tipo de base de datos en uso."""
    try:
        conn = get_postgres_connection()
        conn.close()
        return 'postgresql'
    except Exception:
        return 'error'


def run_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """Ejecuta una consulta SQL en PostgreSQL.
    
    Args:
        query: Consulta SQL con placeholders %s
        params: Tupla de parámetros
        fetchone: Si debe retornar una fila
        fetchall: Si debe retornar todas las filas
        commit: Si debe hacer commit
    
    Returns:
        Resultado de la consulta o None
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(query, params or ())

        result = None
        if commit:
            conn.commit()
        if fetchone:
            result = cur.fetchone()
        elif fetchall:
            result = cur.fetchall()

        return result
        
    except Exception as e:
        logger.error(f"✗ Error en consulta SQL: {e}")
        logger.error(f"  Query: {query}")
        logger.error(f"  Params: {params}")
        if conn and commit:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


def count_assigned_numbers():
    """Cuenta el total de números asignados."""
    try:
        row = run_query("SELECT COUNT(*) FROM assigned_numbers", fetchone=True)
        if not row:
            return 0
        return int(row[0])
    except Exception as e:
        logger.error(f"✗ Error contando números asignados: {e}")
        return 0


def test_connection():
    """Prueba la conexión a la base de datos."""
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        logger.info(f"✓ Conexión exitosa a PostgreSQL")
        return True
    except Exception as e:
        logger.error(f"✗ Error de conexión: {e}")
        return False


def get_connection_info():
    """Retorna información sobre la conexión actual."""
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT current_database(), current_user, version();")
        db_name, user, version = cur.fetchone()
        cur.close()
        conn.close()
        return {
            'database': db_name,
            'user': user,
            'version': version.split(',')[0],  # Solo la primera parte de la versión
            'type': 'PostgreSQL (Neon)'
        }
    except Exception as e:
        logger.error(f"Error obteniendo información de conexión: {e}")
        return None


def verify_tables():
    """Verifica que las tablas necesarias existan."""
    try:
        purchases_exists = table_exists('purchases')
        assigned_exists = table_exists('assigned_numbers')
        
        if not purchases_exists or not assigned_exists:
            logger.error("❌ Faltan tablas requeridas en la base de datos")
            logger.error(f"  purchases existe: {purchases_exists}")
            logger.error(f"  assigned_numbers existe: {assigned_exists}")
            return False
        
        logger.info("✓ Todas las tablas requeridas existen")
        return True
    except Exception as e:
        logger.error(f"Error verificando tablas: {e}")
        return False