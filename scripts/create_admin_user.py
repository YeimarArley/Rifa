#!/usr/bin/env python3
"""
Script para crear usuario administrador
Ejecutar: python scripts/create_admin_user.py
"""

import sys
import os
import hashlib
import re

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db as app_db
from dotenv import load_dotenv

load_dotenv()

def hash_password(password):
    """Hashea una contraseña con SHA256 + SALT"""
    salt = os.getenv('PASSWORD_SALT', 'rifa_salt_2025')
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Valida requisitos de contraseña"""
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not any(c.isupper() for c in password):
        errors.append("La contraseña debe contener al menos una mayúscula")
    
    if not any(c.islower() for c in password):
        errors.append("La contraseña debe contener al menos una minúscula")
    
    if not any(c.isdigit() for c in password):
        errors.append("La contraseña debe contener al menos un número")
    
    return errors


def create_admin_user():
    """Crea un nuevo usuario administrador"""
    print("=" * 60)
    print("👤 CREAR USUARIO ADMINISTRADOR")
    print("=" * 60)
    print()
    
    # Solicitar email
    while True:
        email = input("📧 Email: ").strip().lower()
        
        if not email:
            print("❌ El email es obligatorio\n")
            continue
        
        if not validate_email(email):
            print("❌ Email inválido. Usa el formato: usuario@dominio.com\n")
            continue
        
        # Verificar si el email ya existe
        try:
            existing = app_db.run_query(
                "SELECT id FROM admin_users WHERE LOWER(email) = LOWER(%s)",
                params=(email,),
                fetchone=True
            )
            
            if existing:
                print(f"❌ El email {email} ya está registrado\n")
                continue
            
            break
        except Exception as e:
            print(f"⚠️ Error verificando email: {e}")
            break
    
    # Solicitar contraseña
    import getpass
    
    while True:
        password = getpass.getpass("🔒 Contraseña: ")
        
        if not password:
            print("❌ La contraseña es obligatoria\n")
            continue
        
        errors = validate_password(password)
        if errors:
            print("❌ La contraseña no cumple los requisitos:")
            for error in errors:
                print(f"   • {error}")
            print()
            continue
        
        confirm_password = getpass.getpass("🔒 Confirmar contraseña: ")
        
        if password != confirm_password:
            print("❌ Las contraseñas no coinciden\n")
            continue
        
        break
    
    # Hashear contraseña
    password_hash = hash_password(password)
    
    # Confirmar
    print("\n" + "=" * 60)
    print("📋 RESUMEN")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Contraseña: {'•' * len(password)}")
    print()
    
    confirm = input("¿Crear este usuario? (s/n): ").strip().lower()
    
    if confirm != 's':
        print("\n❌ Operación cancelada")
        return
    
    # Crear usuario
    try:
        app_db.run_query(
            """INSERT INTO admin_users (email, password_hash, is_active)
               VALUES (%s, %s, TRUE)""",
            params=(email, password_hash),
            commit=True
        )
        
        print("\n✅ Usuario administrador creado exitosamente!")
        print(f"\n🔑 Credenciales de acceso:")
        print(f"   Email: {email}")
        print(f"   Contraseña: {password}")
        print("\n⚠️  IMPORTANTE: Guarda estas credenciales en un lugar seguro")
        print()
        
    except Exception as e:
        print(f"\n❌ Error creando usuario: {e}")
        import traceback
        traceback.print_exc()


def list_admin_users():
    """Lista todos los usuarios administradores"""
    print("\n" + "=" * 60)
    print("📋 USUARIOS ADMINISTRADORES REGISTRADOS")
    print("=" * 60)
    print()
    
    try:
        users = app_db.run_query(
            "SELECT id, email, is_active, created_at FROM admin_users ORDER BY id",
            fetchall=True
        )
        
        if not users:
            print("No hay usuarios registrados")
            return
        
        for user in users:
            user_id = user[0]
            email = user[1]
            is_active = user[2]
            created_at = user[3]
            
            status = "✅ ACTIVO" if is_active else "❌ INACTIVO"
            
            print(f"ID: {user_id}")
            print(f"Email: {email}")
            print(f"Estado: {status}")
            print(f"Creado: {created_at}")
            print("-" * 60)
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║         GESTIÓN DE USUARIOS ADMINISTRADORES           ║
    ║                  Rifa 5 Millones                       ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar base de datos
    try:
        app_db.init_db()
        print("✅ Base de datos inicializada\n")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}\n")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("OPCIONES:")
        print("=" * 60)
        print("1. Crear nuevo usuario administrador")
        print("2. Listar usuarios existentes")
        print("3. Salir")
        print()
        
        opcion = input("Selecciona una opción (1-3): ").strip()
        
        if opcion == '1':
            create_admin_user()
        elif opcion == '2':
            list_admin_users()
        elif opcion == '3':
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("\n❌ Opción inválida")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Operación interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()