#!/usr/bin/env python3
"""
Script para verificar la conexión a PostgreSQL en Neon
"""
import os
import sys
from pathlib import Path

# Obtener el directorio raíz del proyecto
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent if current_dir.name == 'tests' else current_dir

# Agregar el directorio app al path
app_dir = project_root / 'app'
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(project_root))

# Cargar variables de entorno desde el directorio raíz
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Importar el módulo db desde app
try:
    from app import db
except ImportError:
    try:
        import db
    except ImportError:
        print("✗ Error: No se pudo importar el módulo db")
        print(f"  Directorio actual: {current_dir}")
        print(f"  Directorio raíz del proyecto: {project_root}")
        print(f"  Directorio app: {app_dir}")
        print(f"  ¿Existe app/db.py?: {(app_dir / 'db.py').exists()}")
        sys.exit(1)

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_info(text):
    print(f"ℹ {text}")

def main():
    print_header("VERIFICACIÓN DE CONEXIÓN A NEON POSTGRESQL")
    
    # Verificar variables de entorno
    print("=== 1. Verificación de Variables de Entorno ===")
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Ocultar contraseña para seguridad
        if '@' in database_url and 'neon.tech' in database_url:
            safe_url = database_url.split('@')[1] if '@' in database_url else database_url
            print_info(f"DATABASE_URL configurada: ...@{safe_url}")
            print_success("URL de Neon detectada correctamente")
        else:
            print_info(f"DATABASE_URL configurada")
    else:
        print_error("DATABASE_URL no configurada en .env")
        print_info("Usando credenciales por defecto del código")
        print_info("Esto es normal si las credenciales están hardcodeadas en db.py")
    
    # Probar conexión
    print("\n=== 2. Prueba de Conexión ===")
    try:
        if db.test_connection():
            print_success("Conexión exitosa a PostgreSQL")
        else:
            print_error("No se pudo conectar a PostgreSQL")
            return False
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        return False
    
    # Verificar tipo de base de datos
    print("\n=== 3. Verificación del Tipo de Base de Datos ===")
    db_type = db.get_db_type()
    if db_type == 'postgresql':
        print_success(f"Base de datos: {db_type.upper()}")
    else:
        print_error(f"Se está usando {db_type} en lugar de PostgreSQL")
        return False
    
    # Inicializar tablas
    print("\n=== 4. Inicialización de Tablas ===")
    try:
        db.init_db()
        print_success("Tablas creadas/verificadas correctamente")
    except Exception as e:
        print_error(f"Error inicializando tablas: {e}")
        return False
    
    # Verificar tablas
    print("\n=== 5. Verificación de Tablas ===")
    try:
        tables = db.run_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """, fetchall=True)
        
        table_names = [t[0] for t in tables]
        
        if 'purchases' in table_names:
            print_success("Tabla 'purchases' existe")
        else:
            print_error("Tabla 'purchases' no encontrada")
        
        if 'assigned_numbers' in table_names:
            print_success("Tabla 'assigned_numbers' existe")
        else:
            print_error("Tabla 'assigned_numbers' no encontrada")
            
    except Exception as e:
        print_error(f"Error verificando tablas: {e}")
        return False
    
    # Contar registros
    print("\n=== 6. Estadísticas Actuales ===")
    try:
        purchases = db.run_query("SELECT COUNT(*) FROM purchases", fetchone=True)
        assigned = db.count_assigned_numbers()
        
        print_info(f"Total de compras: {purchases[0]}")
        print_info(f"Números asignados: {assigned}")
        print_info(f"Números disponibles: {2000 - assigned}")
        
    except Exception as e:
        print_error(f"Error obteniendo estadísticas: {e}")
        return False
    
    # Resumen final
    print_header("RESUMEN")
    print_success("¡Conexión a Neon PostgreSQL configurada correctamente!")
    print_info("Tu sistema de rifas está listo para producción")
    print_info("Todos los registros se guardarán en PostgreSQL en Neon")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)