#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de la base de datos
CUIDADO: Este script elimina datos. Úsalo con precaución.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from . import db as app_db
from dotenv import load_dotenv

load_dotenv()

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def count_records():
    """Cuenta registros en la base de datos"""
    try:
        purchases = app_db.run_query("SELECT COUNT(*) FROM purchases", fetchone=True)
        assigned = app_db.run_query("SELECT COUNT(*) FROM assigned_numbers", fetchone=True)
        
        return {
            'purchases': purchases[0] if purchases else 0,
            'assigned_numbers': assigned[0] if assigned else 0
        }
    except Exception as e:
        print(f"❌ Error contando registros: {e}")
        return None

def show_test_purchases():
    """Muestra compras de prueba"""
    try:
        # Compras de prueba (montos menores a 25000 o con invoice_id test/sim)
        test_purchases = app_db.run_query("""
            SELECT id, invoice_id, amount, email, numbers, created_at 
            FROM purchases 
            WHERE amount < 25000 
               OR invoice_id LIKE 'test_%' 
               OR invoice_id LIKE 'sim_%'
            ORDER BY created_at DESC
        """, fetchall=True)
        
        if test_purchases:
            print(f"\n📋 Compras de prueba encontradas: {len(test_purchases)}")
            print("-" * 70)
            for p in test_purchases:
                print(f"ID: {p[0]} | Ref: {p[1]} | Monto: ${p[2]} | Email: {p[3]}")
                print(f"    Números: {p[4]}")
                print(f"    Fecha: {p[5]}")
                print("-" * 70)
        else:
            print("\n✅ No se encontraron compras de prueba")
        
        return test_purchases
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def delete_test_purchases():
    """Elimina compras de prueba"""
    try:
        # Obtener IDs de compras de prueba
        test_purchases = app_db.run_query("""
            SELECT invoice_id FROM purchases 
            WHERE amount < 25000 
               OR invoice_id LIKE 'test_%' 
               OR invoice_id LIKE 'sim_%'
        """, fetchall=True)
        
        if not test_purchases:
            print("✅ No hay compras de prueba para eliminar")
            return True
        
        # Eliminar números asignados
        for purchase in test_purchases:
            invoice_id = purchase[0]
            app_db.run_query(
                "DELETE FROM assigned_numbers WHERE invoice_id = %s",
                params=(invoice_id,),
                commit=True
            )
        
        # Eliminar compras
        deleted = app_db.run_query("""
            DELETE FROM purchases 
            WHERE amount < 25000 
               OR invoice_id LIKE 'test_%' 
               OR invoice_id LIKE 'sim_%'
        """, commit=True)
        
        print(f"✅ Eliminadas {len(test_purchases)} compras de prueba")
        return True
        
    except Exception as e:
        print(f"❌ Error eliminando: {e}")
        return False

def delete_all_data():
    """Elimina TODOS los datos (usar con extremo cuidado)"""
    try:
        app_db.run_query("DELETE FROM assigned_numbers", commit=True)
        app_db.run_query("DELETE FROM purchases", commit=True)
        app_db.run_query("DELETE FROM blessed_numbers_config", commit=True)
        
        print("✅ Todos los datos eliminados")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def reset_sequences():
    """Reinicia las secuencias de IDs (PostgreSQL)"""
    try:
        app_db.run_query("ALTER SEQUENCE purchases_id_seq RESTART WITH 1", commit=True)
        app_db.run_query("ALTER SEQUENCE blessed_numbers_config_id_seq RESTART WITH 1", commit=True)
        print("✅ Secuencias reiniciadas")
        return True
    except Exception as e:
        print(f"⚠️ No se pudieron reiniciar secuencias (puede ser SQLite): {e}")
        return False

def backup_database():
    """Crea un respaldo antes de limpiar"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        purchases = app_db.run_query("SELECT * FROM purchases", fetchall=True)
        assigned = app_db.run_query("SELECT * FROM assigned_numbers", fetchall=True)
        
        backup_file = f"backup_{timestamp}.txt"
        
        with open(backup_file, 'w') as f:
            f.write(f"Backup creado: {datetime.now()}\n\n")
            f.write(f"Compras: {len(purchases) if purchases else 0}\n")
            f.write(f"Números asignados: {len(assigned) if assigned else 0}\n")
        
        print(f"✅ Backup creado: {backup_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return False

def main():
    print_header("🧹 LIMPIEZA DE BASE DE DATOS - RIFA 5 MILLONES")
    
    # Conectar a base de datos
    try:
        app_db.init_db()
        print("\n✅ Conectado a base de datos")
    except Exception as e:
        print(f"\n❌ Error conectando: {e}")
        return
    
    # Mostrar estado actual
    counts = count_records()
    if counts:
        print(f"\n📊 Estado actual:")
        print(f"   Compras: {counts['purchases']}")
        print(f"   Números asignados: {counts['assigned_numbers']}")
    
    # Menú
    while True:
        print("\n" + "=" * 70)
        print("OPCIONES:")
        print("=" * 70)
        print("1. Ver compras de prueba")
        print("2. Eliminar SOLO compras de prueba (< $25,000)")
        print("3. ⚠️  ELIMINAR TODOS LOS DATOS (reseteo completo)")
        print("4. Crear backup antes de limpiar")
        print("5. Salir")
        print()
        
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion == '1':
            show_test_purchases()
            
        elif opcion == '2':
            print_header("ELIMINAR COMPRAS DE PRUEBA")
            test_purchases = show_test_purchases()
            
            if test_purchases:
                confirm = input("\n¿Eliminar estas compras de prueba? (escribe 'SI' para confirmar): ").strip()
                
                if confirm == 'SI':
                    if delete_test_purchases():
                        print("\n✅ Compras de prueba eliminadas exitosamente")
                        counts = count_records()
                        if counts:
                            print(f"\n📊 Estado después de limpieza:")
                            print(f"   Compras restantes: {counts['purchases']}")
                            print(f"   Números asignados: {counts['assigned_numbers']}")
                else:
                    print("\n❌ Operación cancelada")
                    
        elif opcion == '3':
            print_header("⚠️  ELIMINAR TODOS LOS DATOS")
            print("\n🚨 ADVERTENCIA: Esto eliminará:")
            print("   • TODAS las compras")
            print("   • TODOS los números asignados")
            print("   • TODA la configuración de números benditos")
            print("\n   NO SE PUEDE DESHACER")
            
            confirm1 = input("\n¿Estás SEGURO? (escribe 'ELIMINAR TODO'): ").strip()
            
            if confirm1 == 'ELIMINAR TODO':
                confirm2 = input("Confirma nuevamente (escribe 'CONFIRMO'): ").strip()
                
                if confirm2 == 'CONFIRMO':
                    if delete_all_data():
                        reset_sequences()
                        print("\n✅ Base de datos limpiada completamente")
                        print("   La base de datos está como nueva")
                else:
                    print("\n❌ Operación cancelada")
            else:
                print("\n❌ Operación cancelada")
                
        elif opcion == '4':
            print_header("CREAR BACKUP")
            backup_database()
            
        elif opcion == '5':
            print("\n👋 ¡Hasta luego!")
            break
            
        else:
            print("\n❌ Opción inválida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Operación interrumpida")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()