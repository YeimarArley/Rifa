#!/usr/bin/env python3
"""
Script directo para limpiar y recrear base de datos en Neon
"""
import sys
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Conexión directa
DATABASE_URL = os.getenv('DATABASE_URL', 
    'postgresql://neondb_owner:npg_j7im9lcwxGBM@ep-dark-feather-adbcf7hh-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require')

print("="*70)
print("  RESET DE BASE DE DATOS PARA SISTEMA DE RIFAS")
print("="*70)
print("\n⚠️  Este script eliminará todas las tablas existentes")
print("y creará una estructura limpia para el sistema de rifas.\n")

response = input("¿Continuar? (escribe 'SI' para confirmar): ")
if response.strip().upper() != 'SI':
    print("❌ Operación cancelada")
    sys.exit(0)

try:
    print("\n🔌 Conectando a Neon PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✓ Conectado exitosamente")
    
    # Paso 1: Listar tablas existentes
    print("\n📋 Verificando tablas existentes...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    
    if tables:
        print(f"   Encontradas {len(tables)} tablas:")
        for t in tables:
            print(f"     - {t[0]}")
        
        # Paso 2: Eliminar todas las tablas
        print("\n🗑️  Eliminando tablas...")
        for table in tables:
            table_name = table[0]
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"   ✓ {table_name} eliminada")
        conn.commit()
    else:
        print("   No hay tablas existentes")
    
    # Paso 3: Crear nueva estructura
    print("\n🏗️  Creando nueva estructura...")
    
    # Tabla purchases
    print("   Creando tabla 'purchases'...")
    cur.execute('''
        CREATE TABLE purchases (
            id SERIAL PRIMARY KEY,
            invoice_id VARCHAR(255) UNIQUE NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            email VARCHAR(255) NOT NULL,
            numbers TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("   ✓ Tabla 'purchases' creada")
    
    # Tabla assigned_numbers
    print("   Creando tabla 'assigned_numbers'...")
    cur.execute('''
        CREATE TABLE assigned_numbers (
            number INTEGER PRIMARY KEY,
            invoice_id VARCHAR(255) NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES purchases(invoice_id) ON DELETE CASCADE
        )
    ''')
    print("   ✓ Tabla 'assigned_numbers' creada")
    
    # Índices
    print("   Creando índices...")
    cur.execute('CREATE INDEX idx_purchases_email ON purchases(email)')
    cur.execute('CREATE INDEX idx_purchases_status ON purchases(status)')
    cur.execute('CREATE INDEX idx_purchases_created ON purchases(created_at)')
    cur.execute('CREATE INDEX idx_assigned_invoice ON assigned_numbers(invoice_id)')
    print("   ✓ Índices creados")
    
    conn.commit()
    
    # Paso 4: Verificar estructura
    print("\n🔍 Verificando estructura...")
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'purchases'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print("   Columnas en 'purchases':")
    for col in cols:
        print(f"     - {col[0]}: {col[1]}")
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'assigned_numbers'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print("   Columnas en 'assigned_numbers':")
    for col in cols:
        print(f"     - {col[0]}: {col[1]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*70)
    print("  ✅ BASE DE DATOS CONFIGURADA CORRECTAMENTE")
    print("="*70)
    print("\n📊 Estado actual:")
    print("  • Tabla 'purchases': 0 registros")
    print("  • Tabla 'assigned_numbers': 0 registros")
    print("  • Números disponibles: 2000 (del 1 al 2000)")
    print("\n🎯 Tu sistema de rifas está listo para recibir compras!")
    print("\n💡 Próximos pasos:")
    print("  1. Ejecuta: python server.py")
    print("  2. Abre: http://localhost:8080")
    print("  3. Prueba el endpoint: http://localhost:8080/progress")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)