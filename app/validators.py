"""
Funciones de validación para el sistema de rifas
"""
import re
import logging

logger = logging.getLogger(__name__)


def validate_email(email):
    """Valida que el email sea válido"""
    if not email or not isinstance(email, str):
        return False, "Email requerido"
    
    email = email.strip()
    
    # Validar formato básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    if len(email) > 255:
        return False, "Email demasiado largo"
    
    return True, email


def validate_amount(amount):
    """Valida que el monto sea válido"""
    try:
        amount_float = float(amount)
        
        if amount_float <= 0:
            return False, "El monto debe ser mayor a 0"
        
        if amount_float > 999999999.99:
            return False, "El monto es demasiado alto"
        
        return True, amount_float
        
    except (ValueError, TypeError):
        return False, "El monto debe ser un número válido"


def validate_invoice_id(invoice_id):
    """Valida la referencia de pago/invoice_id"""
    if not invoice_id or not isinstance(invoice_id, str):
        return False, "Referencia de pago requerida"
    
    invoice_id = invoice_id.strip()
    
    if len(invoice_id) < 3:
        return False, "La referencia debe tener al menos 3 caracteres"
    
    if len(invoice_id) > 255:
        return False, "La referencia es demasiado larga"
    
    # Permitir letras, números, guiones, guiones bajos
    if not re.match(r'^[a-zA-Z0-9\-_\.]+$', invoice_id):
        return False, "La referencia contiene caracteres inválidos"
    
    return True, invoice_id


def validate_numbers(numbers_str):
    """Valida la lista de números"""
    if not numbers_str or not isinstance(numbers_str, str):
        return False, "Números requeridos"
    
    numbers_str = numbers_str.strip()
    
    try:
        # Dividir por comas y validar cada número
        numbers = [int(n.strip()) for n in numbers_str.split(',')]
        
        # Validar que sean números entre 1 y 2000
        for num in numbers:
            if num < 1 or num > 2000:
                return False, f"Los números deben estar entre 1 y 2000 (recibido: {num})"
        
        # Verificar números duplicados
        if len(numbers) != len(set(numbers)):
            return False, "No se permiten números duplicados"
        
        return True, numbers
        
    except ValueError:
        return False, "Todos los números deben ser valores enteros válidos"


def validate_status(status):
    """Valida el estado de la compra"""
    valid_statuses = ['pending', 'confirmed', 'cancelled', 'deleted']
    
    if not status or status not in valid_statuses:
        return False, f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
    
    return True, status


def validate_purchase_data(invoice_id, amount, email, numbers, status, notes=None):
    """
    Valida todos los datos de una compra
    Retorna: (is_valid: bool, data: dict or error_message: str)
    """
    
    # Validar cada campo
    is_valid, invoice_id_clean = validate_invoice_id(invoice_id)
    if not is_valid:
        return False, f"Referencia inválida: {invoice_id_clean}"
    
    is_valid, amount_float = validate_amount(amount)
    if not is_valid:
        return False, f"Monto inválido: {amount_float}"
    
    is_valid, email_clean = validate_email(email)
    if not is_valid:
        return False, f"Email inválido: {email_clean}"
    
    is_valid, numbers_list = validate_numbers(numbers)
    if not is_valid:
        return False, f"Números inválidos: {numbers_list}"
    
    is_valid, status_clean = validate_status(status)
    if not is_valid:
        return False, f"Estado inválido: {status_clean}"
    
    # Validar notes (opcional)
    notes_clean = None
    if notes:
        notes_str = str(notes).strip()
        if len(notes_str) > 1000:
            return False, "Las notas son demasiado largas (máximo 1000 caracteres)"
        notes_clean = notes_str if notes_str else None
    
    return True, {
        'invoice_id': invoice_id_clean,
        'amount': amount_float,
        'email': email_clean,
        'numbers': ','.join(map(str, numbers_list)),
        'status': status_clean,
        'notes': notes_clean
    }


def validate_purchase_id(purchase_id):
    """Valida que el ID de compra sea válido"""
    try:
        id_int = int(purchase_id)
        if id_int <= 0:
            return False, "ID inválido"
        return True, id_int
    except (ValueError, TypeError):
        return False, "ID debe ser un número entero"
