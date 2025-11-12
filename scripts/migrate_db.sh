#!/bin/bash

# Script de Migración de Base de Datos - Sistema de Rifas
# Este script actualiza la estructura de la BD para incluir las nuevas tablas y campos

echo "=========================================="
echo "Migración de Base de Datos - Rifa System"
echo "=========================================="
echo ""

# Detectar si estamos usando PostgreSQL o SQLite
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL detectado"
    echo ""
    echo "Ejecutando migraciones de PostgreSQL..."
    echo ""
    
    # Comandos SQL para PostgreSQL
    psql -U $DB_USER -d $DB_NAME -c "
    -- Agregar campos nuevos a tabla purchases si no existen
    DO \$\$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='purchases' AND column_name='updated_at'
        ) THEN
            ALTER TABLE purchases ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        END IF;
        
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='purchases' AND column_name='deleted_at'
        ) THEN
            ALTER TABLE purchases ADD COLUMN deleted_at TIMESTAMP;
        END IF;
        
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='purchases' AND column_name='notes'
        ) THEN
            ALTER TABLE purchases ADD COLUMN notes TEXT;
        END IF;
    END \$\$;
    
    -- Crear tablas nuevas si no existen
    CREATE TABLE IF NOT EXISTS admin_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS audit_log (
        id SERIAL PRIMARY KEY,
        admin_user_id INTEGER,
        action VARCHAR(50),
        table_name VARCHAR(100),
        record_id INTEGER,
        old_values JSONB,
        new_values JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(admin_user_id) REFERENCES admin_users(id)
    );
    
    -- Crear índices si no existen
    CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
    CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases(email);
    CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at);
    CREATE INDEX IF NOT EXISTS idx_assigned_invoice ON assigned_numbers(invoice_id);
    "
    
    echo "✓ Migración de PostgreSQL completada"

else
    echo "✗ PostgreSQL no detectado"
    echo ""
    echo "Para SQLite, la base de datos se actualizará automáticamente"
    echo "al ejecutar el servidor (init_db se ejecuta automáticamente)"
    echo ""
    echo "Para actualizar manualmente SQLite, ejecuta:"
    echo "  python3 -c \"from app import db; db.init_db()\""
fi

echo ""
echo "=========================================="
echo "✓ Migración completada exitosamente"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo "1. Reiniciar el servidor: python server.py"
echo "2. Acceder a: http://localhost:8080/administrador"
echo "3. Probar funciones de edición y eliminación"
echo ""
