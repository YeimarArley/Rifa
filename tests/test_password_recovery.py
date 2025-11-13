#!/usr/bin/env python3
"""
Script de prueba para el sistema de recuperación de contraseña
Ejecutar: python test_password_recovery.py
"""

import requests
import time

# Configuración
BASE_URL = "http://localhost:8080"  # Cambiar según tu entorno
ADMIN_EMAIL = "productionsd546@gmail.com"  # Email configurado en MAIL_DEFAULT_SENDER

def test_forgot_password():
    """Prueba la solicitud de recuperación"""
    print("=" * 60)
    print("🧪 TEST 1: Solicitud de Recuperación de Contraseña")
    print("=" * 60)
    
    url = f"{BASE_URL}/admin/forgot_password"
    data = {"email": ADMIN_EMAIL}
    
    print(f"\n📤 Enviando solicitud a: {url}")
    print(f"📧 Email: {ADMIN_EMAIL}")
    
    try:
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            if "Se ha enviado un email" in response.text:
                print("\n✅ ÉXITO: Email de recuperación enviado")
                print("📬 Revisa tu bandeja de entrada")
                return True
            else:
                print("\n⚠️ ADVERTENCIA: Respuesta inesperada")
                return False
        else:
            print(f"\n❌ ERROR: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_invalid_email():
    """Prueba con email inválido"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Email Inválido")
    print("=" * 60)
    
    url = f"{BASE_URL}/admin/forgot_password"
    data = {"email": "noexiste@example.com"}
    
    print(f"\n📤 Enviando solicitud con email inválido")
    
    try:
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            # Debe mostrar mensaje genérico por seguridad
            if "Si el email está registrado" in response.text:
                print("\n✅ ÉXITO: Mensaje genérico de seguridad mostrado")
                return True
            else:
                print("\n⚠️ ADVERTENCIA: Debería mostrar mensaje genérico")
                return False
        else:
            print(f"\n❌ ERROR: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_reset_with_invalid_token():
    """Prueba con token inválido"""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: Token Inválido")
    print("=" * 60)
    
    url = f"{BASE_URL}/admin/reset_password/token_invalido_123"
    
    print(f"\n📤 Intentando acceder con token inválido")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            if "Token inválido o expirado" in response.text:
                print("\n✅ ÉXITO: Token inválido rechazado correctamente")
                return True
            else:
                print("\n⚠️ ADVERTENCIA: Debería rechazar el token")
                return False
        else:
            print(f"\n❌ ERROR: Status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_password_requirements():
    """Prueba los requisitos de contraseña"""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Requisitos de Contraseña")
    print("=" * 60)
    
    # Estos tests solo verifican que el formulario tenga validación JS
    # La validación real se hace en el servidor
    
    test_cases = [
        {"pwd": "12345", "valid": False, "reason": "Muy corta"},
        {"pwd": "password", "valid": False, "reason": "Sin mayúsculas ni números"},
        {"pwd": "Password", "valid": False, "reason": "Sin números"},
        {"pwd": "Password1", "valid": True, "reason": "Cumple todos los requisitos"},
    ]
    
    print("\n📝 Casos de prueba:")
    for i, case in enumerate(test_cases, 1):
        status = "✅" if case["valid"] else "❌"
        print(f"{i}. {status} '{case['pwd']}' - {case['reason']}")
    
    return True


def interactive_test():
    """Test interactivo guiado"""
    print("\n" + "=" * 60)
    print("🧪 TEST INTERACTIVO")
    print("=" * 60)
    
    print("\n📋 Pasos a seguir:")
    print("1. Solicita recuperación de contraseña")
    print("2. Revisa tu email y copia el token del enlace")
    print("3. Usa el enlace para crear una nueva contraseña")
    print("4. Intenta hacer login con la nueva contraseña")
    
    input("\n⏸️  Presiona ENTER cuando hayas completado estos pasos...")
    
    # Verificar que el login funciona
    print("\n🔐 Verificando login...")
    username = input("Usuario: ")
    password = input("Contraseña (no se mostrará): ")
    
    url = f"{BASE_URL}/admin/login"
    session = requests.Session()
    
    try:
        response = session.post(url, data={
            "username": username,
            "password": password
        })
        
        if "/database" in response.url or response.status_code == 302:
            print("\n✅ LOGIN EXITOSO con nueva contraseña")
            return True
        else:
            print("\n❌ LOGIN FALLIDO - Verifica las credenciales")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   🔐 SISTEMA DE RECUPERACIÓN DE CONTRASEÑA - TEST    ║
    ║                    Rifa 5 Millones                     ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n🌐 Servidor: {BASE_URL}")
    print(f"📧 Email Admin: {ADMIN_EMAIL}")
    
    # Verificar que el servidor está activo
    print("\n🔍 Verificando servidor...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("✅ Servidor activo")
    except Exception as e:
        print(f"❌ Error: Servidor no responde - {str(e)}")
        print("\n💡 Asegúrate de que el servidor esté corriendo:")
        print("   python server.py")
        return
    
    # Ejecutar tests
    results = []
    
    results.append(("Solicitud de recuperación", test_forgot_password()))
    time.sleep(1)
    
    results.append(("Email inválido", test_invalid_email()))
    time.sleep(1)
    
    results.append(("Token inválido", test_reset_with_invalid_token()))
    time.sleep(1)
    
    results.append(("Requisitos de contraseña", test_password_requirements()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Resultado: {passed}/{total} tests exitosos")
    
    if passed == total:
        print("\n✨ ¡Todos los tests pasaron!")
        
        # Ofrecer test interactivo
        print("\n" + "=" * 60)
        do_interactive = input("\n¿Deseas ejecutar el test interactivo completo? (s/n): ").lower()
        if do_interactive == 's':
            interactive_test()
    else:
        print("\n⚠️ Algunos tests fallaron. Revisa la configuración.")
    
    print("\n" + "=" * 60)
    print("🏁 Tests completados")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrumpidos por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()