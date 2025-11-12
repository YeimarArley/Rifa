#!/usr/bin/env python3
"""
Script completo de pruebas para verificar que la base de datos funciona correctamente.
Ejecuta: python test_database.py
"""
import os
import sys
from dotenv import load_dotenv
from app import db
import uuid
import traceback

# Cargar variables de entorno con manejo de codificación
try:
    # Intentar cargar con encoding explícito
    load_dotenv(encoding='utf-8')
except Exception:
    # Si falla, intentar sin encoding (comportamiento por defecto)
    load_dotenv()

# Colores para la salida
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def test_connection():
    """Prueba 1: Verificar conexión a la base de datos"""
    print(f"\n{Colors.BOLD}=== PRUEBA 1: Conexión a la Base de Datos ==={Colors.RESET}")
    try:
        conn = db.get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print_success(f"Conexión exitosa a PostgreSQL")
        print_info(f"Versión: {version[0][:50]}...")
        
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()
        print_info(f"Base de datos: {db_name[0]}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        print_warning("Intentando con SQLite como fallback...")
        try:
            conn = db.get_db_connection()
            if hasattr(conn, 'execute'):
                print_success("Conexión a SQLite exitosa (fallback)")
            else:
                print_success("Conexión a base de datos exitosa")
            conn.close()
            return True
        except Exception as e2:
            print_error(f"Error en fallback: {e2}")
            return False

def test_tables_exist():
    """Prueba 2: Verificar que las tablas existen"""
    print(f"\n{Colors.BOLD}=== PRUEBA 2: Verificar Tablas ==={Colors.RESET}")
    try:
        # Detectar tipo de base de datos
        db_type = db.get_db_type()
        print_info(f"Tipo de base de datos detectado: {db_type}")
        
        if db_type == 'postgresql':
            # Usar sintaxis de PostgreSQL
            result = db.run_query("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'purchases'
                );
            """, fetchone=True)
            
            if result and (result[0] if isinstance(result, tuple) else result):
                print_success("Tabla 'purchases' existe (PostgreSQL)")
            else:
                print_error("Tabla 'purchases' NO existe")
                return False
            
            result = db.run_query("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'assigned_numbers'
                );
            """, fetchone=True)
            
            if result and (result[0] if isinstance(result, tuple) else result):
                print_success("Tabla 'assigned_numbers' existe (PostgreSQL)")
            else:
                print_error("Tabla 'assigned_numbers' NO existe")
                return False
        else:
            # Usar sintaxis de SQLite
            result = db.run_query("SELECT name FROM sqlite_master WHERE type='table' AND name='purchases';", fetchone=True)
            if result:
                print_success("Tabla 'purchases' existe (SQLite)")
            else:
                print_error("Tabla 'purchases' NO existe")
                return False
            
            result = db.run_query("SELECT name FROM sqlite_master WHERE type='table' AND name='assigned_numbers';", fetchone=True)
            if result:
                print_success("Tabla 'assigned_numbers' existe (SQLite)")
            else:
                print_error("Tabla 'assigned_numbers' NO existe")
                return False
        
        return True
    except Exception as e:
        print_error(f"Error verificando tablas: {e}")
        traceback.print_exc()
        return False

def test_insert_purchase():
    """Prueba 3: Insertar una compra de prueba"""
    print(f"\n{Colors.BOLD}=== PRUEBA 3: Insertar Compra ==={Colors.RESET}")
    try:
        test_invoice_id = f"test_{uuid.uuid4().hex[:10]}"
        test_amount = 25000.00
        test_email = "test@example.com"
        test_numbers = "100,101,102,103"
        
        db.run_query(
            "INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')",
            params=(test_invoice_id, test_amount, test_email, test_numbers),
            commit=True
        )
        print_success(f"Compra insertada: {test_invoice_id}")
        
        # Verificar que se insertó correctamente
        result = db.run_query(
            "SELECT invoice_id, amount, email, numbers, status FROM purchases WHERE invoice_id = %s",
            params=(test_invoice_id,),
            fetchone=True
        )
        
        if result:
            print_success("Compra verificada en la base de datos")
            print_info(f"  - Invoice ID: {result[0]}")
            print_info(f"  - Monto: ${result[1]}")
            print_info(f"  - Email: {result[2]}")
            print_info(f"  - Números: {result[3]}")
            print_info(f"  - Estado: {result[4]}")
            return test_invoice_id
        else:
            print_error("La compra no se encontró después de insertar")
            return None
    except Exception as e:
        print_error(f"Error insertando compra: {e}")
        traceback.print_exc()
        return None

def test_insert_assigned_numbers(invoice_id):
    """Prueba 4: Insertar números asignados"""
    print(f"\n{Colors.BOLD}=== PRUEBA 4: Insertar Números Asignados ==={Colors.RESET}")
    if not invoice_id:
        print_warning("Saltando prueba: no hay invoice_id de prueba")
        return False
    
    try:
        test_numbers = [100, 101, 102, 103]
        for number in test_numbers:
            db.run_query(
                "INSERT INTO assigned_numbers (number, invoice_id) VALUES (%s, %s)",
                params=(number, invoice_id),
                commit=True
            )
        print_success(f"Números asignados: {test_numbers}")
        
        # Verificar que se insertaron
        result = db.run_query(
            "SELECT number FROM assigned_numbers WHERE invoice_id = %s ORDER BY number",
            params=(invoice_id,),
            fetchall=True
        )
        
        if result and len(result) == len(test_numbers):
            print_success(f"Verificados {len(result)} números asignados")
            return True
        else:
            print_error(f"Se esperaban {len(test_numbers)} números, se encontraron {len(result) if result else 0}")
            return False
    except Exception as e:
        print_error(f"Error insertando números asignados: {e}")
        traceback.print_exc()
        return False

def test_count_assigned_numbers():
    """Prueba 5: Contar números asignados"""
    print(f"\n{Colors.BOLD}=== PRUEBA 5: Contar Números Asignados ==={Colors.RESET}")
    try:
        count = db.count_assigned_numbers()
        print_success(f"Total de números asignados: {count}")
        return True
    except Exception as e:
        print_error(f"Error contando números: {e}")
        traceback.print_exc()
        return False

def test_query_purchases():
    """Prueba 6: Consultar compras"""
    print(f"\n{Colors.BOLD}=== PRUEBA 6: Consultar Compras ==={Colors.RESET}")
    try:
        result = db.run_query(
            "SELECT invoice_id, amount, email, status FROM purchases ORDER BY created_at DESC LIMIT 5",
            fetchall=True
        )
        
        if result:
            print_success(f"Se encontraron {len(result)} compras")
            for i, row in enumerate(result[:3], 1):
                print_info(f"  {i}. {row[0]} - ${row[1]} - {row[2]} - {row[3]}")
            return True
        else:
            print_warning("No se encontraron compras en la base de datos")
            return True
    except Exception as e:
        print_error(f"Error consultando compras: {e}")
        traceback.print_exc()
        return False

def test_cleanup_test_data(invoice_id):
    """Prueba 7: Limpiar datos de prueba"""
    print(f"\n{Colors.BOLD}=== PRUEBA 7: Limpiar Datos de Prueba ==={Colors.RESET}")
    if not invoice_id:
        print_warning("No hay datos de prueba para limpiar")
        return True
    
    try:
        # Eliminar números asignados
        db.run_query(
            "DELETE FROM assigned_numbers WHERE invoice_id = %s",
            params=(invoice_id,),
            commit=True
        )
        print_success("Números asignados eliminados")
        
        # Eliminar compra
        db.run_query(
            "DELETE FROM purchases WHERE invoice_id = %s",
            params=(invoice_id,),
            commit=True
        )
        print_success("Compra de prueba eliminada")
        return True
    except Exception as e:
        print_error(f"Error limpiando datos: {e}")
        traceback.print_exc()
        return False

def test_assign_numbers_logic():
    """Prueba 8: Probar la lógica de asignación de números"""
    print(f"\n{Colors.BOLD}=== PRUEBA 8: Lógica de Asignación de Números ==={Colors.RESET}")
    try:
        # Obtener números asignados
        rows = db.run_query("SELECT number FROM assigned_numbers", fetchall=True) or []
        assigned = set()
        for r in rows:
            try:
                assigned.add(int(r[0]))
            except:
                try:
                    assigned.add(int(r))
                except:
                    pass
        
        available = [n for n in range(1, 2001) if n not in assigned]
        print_success(f"Números disponibles: {len(available)} de 2000")
        print_info(f"Números asignados: {len(assigned)}")
        
        if len(available) > 0:
            print_info(f"Ejemplo de números disponibles: {available[:10]}")
        
        return True
    except Exception as e:
        print_error(f"Error en lógica de asignación: {e}")
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("  SCRIPT DE PRUEBAS DE BASE DE DATOS - RIFA")
    print(f"{'='*60}{Colors.RESET}")
    
    results = []
    test_invoice_id = None
    
    # Ejecutar pruebas
    results.append(("Conexión", test_connection()))
    results.append(("Tablas", test_tables_exist()))
    
    test_invoice_id = test_insert_purchase()
    results.append(("Insertar Compra", test_invoice_id is not None))
    
    if test_invoice_id:
        results.append(("Insertar Números", test_insert_assigned_numbers(test_invoice_id)))
    
    results.append(("Contar Números", test_count_assigned_numbers()))
    results.append(("Consultar Compras", test_query_purchases()))
    results.append(("Lógica Asignación", test_assign_numbers_logic()))
    
    # Limpiar datos de prueba
    if test_invoice_id:
        results.append(("Limpieza", test_cleanup_test_data(test_invoice_id)))
    
    # Resumen
    print(f"\n{Colors.BOLD}{'='*60}")
    print("  RESUMEN DE PRUEBAS")
    print(f"{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASÓ")
        else:
            print_error(f"{test_name}: FALLÓ")
    
    print(f"\n{Colors.BOLD}Resultado Final: {passed}/{total} pruebas pasaron{Colors.RESET}")
    
    if passed == total:
        print_success("\n¡Todas las pruebas pasaron! La base de datos funciona correctamente.")
        return 0
    else:
        print_error(f"\n{total - passed} prueba(s) fallaron. Revisa los errores arriba.")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Pruebas interrumpidas por el usuario{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error fatal: {e}")
        traceback.print_exc()
        sys.exit(1)

