import os
import psycopg2
import sqlite3
import logging
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'rifa_db')
DB_USER = os.getenv('DB_USER', 'rifa_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rifa_password')


def get_postgres_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def get_db_connection():
    """Return a connection to Postgres if available, otherwise a sqlite3 connection.

    The caller should be aware of the connection type (psycopg2 vs sqlite3) and use
    appropriate cursor methods. This helper tries Postgres first and falls back to sqlite.
    """
    try:
        conn = get_postgres_connection()
        return conn
    except Exception as e:
        logger.warning(f"Postgres connection failed, using sqlite fallback: {e}")
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rifa.db')
        conn = sqlite3.connect(sqlite_path)
        return conn


def init_db():
    """Initialize database tables in Postgres if available, otherwise in sqlite file."""
    # Try Postgres
    try:
        conn = get_postgres_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS purchases
                     (id SERIAL PRIMARY KEY,
                      invoice_id VARCHAR(255) UNIQUE,
                      amount DECIMAL(10,2),
                      email VARCHAR(255),
                      numbers TEXT,
                      status VARCHAR(50) DEFAULT 'pending',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS assigned_numbers
                     (number INTEGER PRIMARY KEY,
                      invoice_id VARCHAR(255),
                      assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        logger.info('Initialized Postgres tables')
        return
    except Exception as e:
        logger.warning(f'Could not initialize Postgres DB, falling back to sqlite: {e}')

    # Fallback to sqlite
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rifa.db')
    try:
        sconn = sqlite3.connect(sqlite_path)
        sc = sconn.cursor()
        sc.execute('''CREATE TABLE IF NOT EXISTS purchases
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       invoice_id TEXT UNIQUE,
                       amount REAL,
                       email TEXT,
                       numbers TEXT,
                       status TEXT DEFAULT 'pending',
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        sc.execute('''CREATE TABLE IF NOT EXISTS assigned_numbers
                      (number INTEGER PRIMARY KEY,
                       invoice_id TEXT,
                       assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        sconn.commit()
        sconn.close()
        logger.info('Initialized sqlite fallback database at %s', sqlite_path)
    except Exception as e2:
        logger.error(f'Failed to initialize sqlite fallback DB: {e2}')


def _is_sqlite_conn(conn):
    return isinstance(conn, sqlite3.Connection)


def run_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """Run a SQL query against Postgres or sqlite. Translates %s placeholders to ? for sqlite.

    Returns fetched data if requested. Closes the connection after running.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        q = query
        p = params or ()
        if _is_sqlite_conn(conn):
            # sqlite uses ? placeholders
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
    row = run_query("SELECT COUNT(*) FROM assigned_numbers", fetchone=True)
    if not row:
        return 0
    # row can be a tuple (count,) or a single value depending on driver
    try:
        return int(row[0])
    except Exception:
        return int(row)
