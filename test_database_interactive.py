#!/usr/bin/env python3
"""
Script interactivo para probar la base de datos manualmente.
Ejecuta: python test_database_interactive.py
"""
import os
from dotenv import load_dotenv
from app import db
import uuid

load_dotenv()

def print_menu():
    print("\n" + "="*60)
    print("  MENÚ DE PRUEBAS DE BASE DE DATOS")
    print("="*60)
    print("1. Verificar conexión")
    print("2. Ver estado de la base de datos")
    print("3. Insertar compra de prueba")
    print("4. Ver todas las compras")
    print("5. Ver números asignados")
    print("6. Contar números asignados")
    print("7. Simular asignación de números")
    print("8. Limpiar datos de prueba")
    print("9. Salir")
    print("="*60)

def test_connection():
    try:
        conn = db.get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"✓ Conexión exitosa a: {db_name[0]}")
        print(f"  Versión: {version[0][:60]}...")
        return True
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        return False

def show_database_status():
    try:
        # Contar compras
        purchases = db.run_query("SELECT COUNT(*) FROM purchases", fetchone=True)
        purchase_count = purchases[0] if purchases else 0
        
        # Contar números asignados
        assigned_count = db.count_assigned_numbers()
        
        # Últimas compras
        recent = db.run_query(
            "SELECT invoice_id, amount, email, status FROM purchases ORDER BY created_at DESC LIMIT 5",
            fetchall=True
        ) or []
        
        print(f"\n📊 Estado de la Base de Datos:")
        print(f"  - Total de compras: {purchase_count}")
        print(f"  - Números asignados: {assigned_count}")
        print(f"  - Números disponibles: {2000 - assigned_count}")
        
        if recent:
            print(f"\n  Últimas 5 compras:")
            for i, row in enumerate(recent, 1):
                print(f"    {i}. {row[0]} - ${row[1]} - {row[2]} ({row[3]})")
        else:
            print("\n  No hay compras registradas")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def insert_test_purchase():
    try:
        invoice_id = f"test_{uuid.uuid4().hex[:10]}"
        amount = float(input("Ingresa el monto (ej: 25000): ") or "25000")
        email = input("Ingresa el email (ej: test@example.com): ") or "test@example.com"
        numbers_input = input("Ingresa los números separados por coma (ej: 1,2,3,4): ") or "1,2,3,4"
        numbers = numbers_input.replace(" ", "")
        
        # Insertar compra
        db.run_query(
            "INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')",
            params=(invoice_id, amount, email, numbers),
            commit=True
        )
        
        # Insertar números asignados
        for num in numbers.split(','):
            try:
                db.run_query(
                    "INSERT INTO assigned_numbers (number, invoice_id) VALUES (%s, %s)",
                    params=(int(num.strip()), invoice_id),
                    commit=True
                )
            except Exception as e:
                print(f"  ⚠ Número {num} ya estaba asignado o error: {e}")
        
        print(f"✓ Compra insertada: {invoice_id}")
        print(f"  Monto: ${amount}")
        print(f"  Email: {email}")
        print(f"  Números: {numbers}")
        return invoice_id
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_all_purchases():
    try:
        purchases = db.run_query(
            "SELECT id, invoice_id, amount, email, numbers, status, created_at FROM purchases ORDER BY created_at DESC",
            fetchall=True
        ) or []
        
        if not purchases:
            print("No hay compras en la base de datos")
            return
        
        print(f"\n📋 Total de compras: {len(purchases)}\n")
        for p in purchases:
            print(f"ID: {p[0]}")
            print(f"  Invoice ID: {p[1]}")
            print(f"  Monto: ${p[2]}")
            print(f"  Email: {p[3]}")
            print(f"  Números: {p[4]}")
            print(f"  Estado: {p[5]}")
            print(f"  Fecha: {p[6]}")
            print("-" * 40)
    except Exception as e:
        print(f"✗ Error: {e}")

def show_assigned_numbers():
    try:
        numbers = db.run_query(
            "SELECT number, invoice_id, assigned_at FROM assigned_numbers ORDER BY number",
            fetchall=True
        ) or []
        
        if not numbers:
            print("No hay números asignados")
            return
        
        print(f"\n🔢 Total de números asignados: {len(numbers)}\n")
        # Mostrar primeros 20
        for n in numbers[:20]:
            print(f"  Número {n[0]}: {n[1]} (asignado: {n[2]})")
        
        if len(numbers) > 20:
            print(f"\n  ... y {len(numbers) - 20} más")
    except Exception as e:
        print(f"✗ Error: {e}")

def simulate_number_assignment():
    try:
        count = int(input("¿Cuántos números quieres asignar? (ej: 4): ") or "4")
        
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
        
        if len(available) < count:
            print(f"✗ Solo hay {len(available)} números disponibles")
            return
        
        import random
        selected = random.sample(available, count)
        selected.sort()
        
        print(f"✓ Números disponibles para asignar: {selected}")
        print(f"  Total disponible: {len(available)}")
        print(f"  Total asignado: {len(assigned)}")
    except Exception as e:
        print(f"✗ Error: {e}")

def cleanup_test_data():
    try:
        confirm = input("¿Eliminar todas las compras de prueba? (test_*) [s/N]: ").lower()
        if confirm != 's':
            print("Operación cancelada")
            return
        
        result = db.run_query(
            "DELETE FROM purchases WHERE invoice_id LIKE 'test_%'",
            commit=True
        )
        
        result2 = db.run_query(
            "DELETE FROM assigned_numbers WHERE invoice_id LIKE 'test_%'",
            commit=True
        )
        
        print("✓ Datos de prueba eliminados")
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    print("Script Interactivo de Pruebas de Base de Datos")
    print("Presiona Ctrl+C para salir en cualquier momento\n")
    
    while True:
        try:
            print_menu()
            choice = input("\nSelecciona una opción (1-9): ").strip()
            
            if choice == '1':
                test_connection()
            elif choice == '2':
                show_database_status()
            elif choice == '3':
                insert_test_purchase()
            elif choice == '4':
                show_all_purchases()
            elif choice == '5':
                show_assigned_numbers()
            elif choice == '6':
                count = db.count_assigned_numbers()
                print(f"\n🔢 Total de números asignados: {count}")
                print(f"   Números disponibles: {2000 - count}")
            elif choice == '7':
                simulate_number_assignment()
            elif choice == '8':
                cleanup_test_data()
            elif choice == '9':
                print("¡Hasta luego!")
                break
            else:
                print("Opción inválida. Intenta de nuevo.")
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()

