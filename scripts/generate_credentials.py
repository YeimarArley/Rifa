#!/usr/bin/env python3
"""
Script para generar credenciales seguras para la aplicación de Rifa
Ejecutar: python generate_credentials.py
"""

import hashlib
import secrets
import os

def generate_secret_key():
    """Genera una SECRET_KEY fuerte para Flask"""
    return secrets.token_hex(32)

def generate_password_salt():
    """Genera un salt aleatorio para hashear contraseñas"""
    return f"rifa_salt_{secrets.token_urlsafe(16)}"

def generate_admin_sim_key():
    """Genera una clave API para simulaciones admin"""
    return secrets.token_urlsafe(32)

def hash_password_with_salt(password, salt):
    """Hashea una contraseña con un salt específico"""
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def main():
    print("=" * 60)
    print("🔐 GENERADOR DE CREDENCIALES SEGURAS - RIFA 5 MILLONES")
    print("=" * 60)
    print()
    
    # 1. SECRET_KEY
    secret_key = generate_secret_key()
    print("1️⃣  SECRET_KEY (Flask session)")
    print(f"   SECRET_KEY={secret_key}")
    print()
    
    # 2. PASSWORD_SALT
    password_salt = generate_password_salt()
    print("2️⃣  PASSWORD_SALT (para hashear contraseñas)")
    print(f"   PASSWORD_SALT={password_salt}")
    print()
    
    # 3. ADMIN_SIM_KEY
    admin_sim_key = generate_admin_sim_key()
    print("3️⃣  ADMIN_SIM_KEY (API simulaciones)")
    print(f"   ADMIN_SIM_KEY={admin_sim_key}")
    print()
    
    # 4. Admin Credentials
    print("4️⃣  ADMIN CREDENTIALS")
    admin_username = input("   Ingresa el nombre de usuario admin (default: admin_production): ").strip()
    if not admin_username:
        admin_username = "admin_production"
    
    admin_password = input("   Ingresa la contraseña admin (mínimo 8 caracteres): ").strip()
    while len(admin_password) < 8:
        print("   ⚠️  La contraseña debe tener al menos 8 caracteres")
        admin_password = input("   Ingresa la contraseña admin: ").strip()
    
    # Hashear con el salt generado
    admin_password_hash = hash_password_with_salt(admin_password, password_salt)
    
    print(f"   ADMIN_USERNAME={admin_username}")
    print(f"   ADMIN_PASSWORD_HASH={admin_password_hash}")
    print()
    
    # Resumen
    print("=" * 60)
    print("📋 RESUMEN - Copia estas líneas a tu .env:")
    print("=" * 60)
    print()
    print("# 🔐 SEGURIDAD - Generado automáticamente")
    print(f"SECRET_KEY={secret_key}")
    print(f"PASSWORD_SALT={password_salt}")
    print(f"ADMIN_USERNAME={admin_username}")
    print(f"ADMIN_PASSWORD_HASH={admin_password_hash}")
    print(f"ADMIN_SIM_KEY={admin_sim_key}")
    print()
    
    # Guardar en archivo
    save = input("¿Deseas guardar en un archivo 'credentials.txt'? (s/n): ").strip().lower()
    if save == 's':
        with open('credentials.txt', 'w') as f:
            f.write("# 🔐 CREDENCIALES GENERADAS\n")
            f.write("# ⚠️  IMPORTANTE: Guarda este archivo en un lugar seguro y elimínalo después\n\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write(f"PASSWORD_SALT={password_salt}\n")
            f.write(f"ADMIN_USERNAME={admin_username}\n")
            f.write(f"ADMIN_PASSWORD_HASH={admin_password_hash}\n")
            f.write(f"ADMIN_SIM_KEY={admin_sim_key}\n")
            f.write(f"\n# Contraseña en texto plano (solo para referencia - ELIMINAR):\n")
            f.write(f"# {admin_password}\n")
        
        print("✅ Credenciales guardadas en 'credentials.txt'")
        print("⚠️  IMPORTANTE: Elimina este archivo después de copiar las credenciales")
    
    print()
    print("=" * 60)
    print("🎯 PRÓXIMOS PASOS:")
    print("=" * 60)
    print("1. Copia las credenciales a tu archivo .env")
    print("2. Reinicia tu aplicación Flask")
    print("3. Prueba el login con las nuevas credenciales")
    print("4. Elimina el archivo credentials.txt si lo creaste")
    print()
    print("🔒 Tu aplicación ahora está más segura!")
    print()

if __name__ == "__main__":
    main()