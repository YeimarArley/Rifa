# Documentación de Cambios - Sistema de Administración de Rifas

## 📋 Resumen de Cambios

Se han realizado mejoras significativas al sistema de administración de rifas, incluyendo:

1. **Reorganización de la Base de Datos**
2. **Implementación de Funciones de Edición y Eliminación**
3. **Mejora de la Interfaz de Usuario (UI)**
4. **Validación de Datos y Seguridad**
5. **Auditoría y Logging**

---

## 🗄️ Cambios en la Base de Datos

### Tablas Creadas/Modificadas

#### 1. **purchases** (mejorada)
- `id` - ID único (PRIMARY KEY)
- `invoice_id` - Referencia única de pago (VARCHAR/TEXT UNIQUE)
- `amount` - Monto de la compra (DECIMAL/REAL)
- `email` - Email del comprador (VARCHAR/TEXT)
- `numbers` - Números asignados (TEXT, separados por comas)
- `status` - Estado de la compra (VARCHAR/TEXT)
  - `pending`: Pendiente de confirmación
  - `confirmed`: Confirmada
  - `cancelled`: Cancelada
  - `deleted`: Marcada como eliminada
- `created_at` - Fecha de creación (TIMESTAMP)
- `updated_at` - Fecha de última actualización (TIMESTAMP) [NUEVO]
- `deleted_at` - Fecha de eliminación (TIMESTAMP) [NUEVO]
- `notes` - Notas administrativas (TEXT) [NUEVO]

#### 2. **assigned_numbers** (sin cambios relevantes)
- `number` - Número de la rifa (1-2000)
- `invoice_id` - Referencia de la compra
- `assigned_at` - Fecha de asignación
- Incluye índice para mejor rendimiento

#### 3. **admin_users** (NUEVA)
```sql
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 4. **audit_log** (NUEVA)
```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER,
    action VARCHAR(50),
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(admin_user_id) REFERENCES admin_users(id)
)
```

### Índices Creados
- `idx_purchases_status` - Para filtros rápidos por estado
- `idx_purchases_email` - Para búsquedas por email
- `idx_purchases_created_at` - Para ordenamiento por fecha
- `idx_assigned_invoice` - Para relaciones con compras

---

## 📁 Archivos Modificados

### 1. **app/db.py**
**Cambios:**
- Mejorada función `init_db()` con nuevas tablas
- Agregadas funciones:
  - `get_purchase_by_id(purchase_id)` - Obtener una compra
  - `update_purchase(...)` - Actualizar compra
  - `delete_purchase(purchase_id)` - Soft delete
  - `force_delete_purchase(purchase_id)` - Hard delete
  - `log_audit(...)` - Registrar cambios

**Notas:**
- Mantiene compatibilidad con SQLite y PostgreSQL
- Todas las funciones manejan ambas conexiones automáticamente

### 2. **app/validators.py** (NUEVO)
**Validaciones implementadas:**
- `validate_email()` - Valida formato de email
- `validate_amount()` - Valida monto (> 0, < 999999999.99)
- `validate_invoice_id()` - Valida referencia de pago
- `validate_numbers()` - Valida números (1-2000, sin duplicados)
- `validate_status()` - Valida estado de compra
- `validate_purchase_data()` - Validación completa
- `validate_purchase_id()` - Valida ID de compra

**Características:**
- Mensajes de error descriptivos
- Validación de rango y formato
- Prevención de inyección SQL
- Prevención de números duplicados

### 3. **server.py**
**Rutas modificadas:**

#### `/edit_purchase/<purchase_id>` (GET/POST)
- GET: Muestra formulario de edición
- POST: Procesa actualización con validaciones
- Usa nuevo template `edit_purchase.html`
- Require autenticación (`@login_required`)
- Valida todos los datos antes de actualizar

#### `/delete_purchase/<purchase_id>` (GET/POST)
- GET: Muestra confirmación con dos opciones
- POST: Procesa eliminación
- Usa nuevo template `delete_purchase.html`
- Require autenticación (`@login_required`)
- Opción de soft delete o hard delete

**Nuevas características:**
- Validación de datos con módulo `validators`
- Manejo robusto de errores
- Logging detallado de acciones
- Mensajes de error amigables

### 4. **templates/administrador.html**
**Cambios:**
- Agregada columna "Acciones" con botones:
  - ✏️ Editar - Enlaza a `/edit_purchase/{id}`
  - 🗑️ Eliminar - Enlaza a `/delete_purchase/{id}`
- Mejorada presentación de la tabla

### 5. **static/admin.css**
**Nuevos estilos:**
```css
.actions-cell {
  /* Contenedor para botones de acción */
}

.action-btn {
  /* Estilo base para botones */
}

.action-edit {
  /* Botón azul para editar */
}

.action-delete {
  /* Botón rojo para eliminar */
}
```

**Características:**
- Diseño responsivo
- Efectos hover
- Colores distintivos
- Animaciones suaves

---

## 📝 Archivos Nuevos

### 1. **templates/edit_purchase.html**
**Funcionalidad:**
- Formulario para editar compra
- Campos editables:
  - Referencia de pago
  - Monto
  - Email
  - Números
  - Estado
  - Notas
- Validación en frontend
- Botones: Guardar / Cancelar
- Visualización de fecha de creación

**Características:**
- Diseño responsivo
- Mensajes de error claros
- Información contextual
- Interfaz intuitiva

### 2. **templates/delete_purchase.html**
**Funcionalidad:**
- Confirmación antes de eliminar
- Dos opciones de eliminación:
  - 🔒 Soft Delete (Recomendado)
    - Marca como eliminada
    - Permite recuperación
    - Datos permanecen en BD
  - 🗑️ Hard Delete
    - Eliminación permanente
    - No se puede deshacer
    - Remueve completamente
- Visualización de datos de compra
- Advertencia clara de consecuencias

**Características:**
- Confirmación doble de seguridad
- Información detallada
- Opciones claramente explicadas
- Advertencias visuales

### 3. **templates/error.html**
**Funcionalidad:**
- Página de error genérica
- Mensaje personalizable
- Botón de regreso al panel
- Diseño consistente

---

## 🔒 Seguridad Implementada

### 1. **Validación de Entrada**
- Validación de tipos de datos
- Rango de valores
- Formato de email
- Prevención de inyección SQL
- Límites de longitud

### 2. **Autenticación**
- Todas las rutas de admin requieren `@login_required`
- Sesión de usuario requerida
- Validación de credenciales

### 3. **Autorización**
- Solo administradores pueden editar/eliminar
- Protección contra acceso directo

### 4. **Manejo de Errores**
- Mensajes de error seguros
- No exponemos detalles de BD
- Logging detallado para debugging

### 5. **Auditoría**
- Tabla `audit_log` para rastrear cambios
- Función `log_audit()` para registrar acciones
- Timestamp automático

---

## 🎨 Mejoras de UI/UX

### 1. **Tabla de Compras**
- Nueva columna "Acciones"
- Botones intuitivos
- Diseño limpio y ordenado

### 2. **Formularios**
- Campos claramente etiquetados
- Validación en tiempo real (posible mejora futura)
- Mensajes de error contextuales
- Notas de ayuda para cada campo

### 3. **Confirmaciones**
- Dialogo de confirmación antes de eliminar
- Advertencias visuales claras
- Opciones bien explicadas

### 4. **Diseño Responsivo**
- Compatible con móviles
- Adaptable a diferentes tamaños
- Navegación simplificada en móvil

---

## 📊 Flujo de Operaciones

### Editar Compra
```
1. Admin hace clic en ✏️ Editar
2. Se abre formulario de edición (GET /edit_purchase/{id})
3. Admin modifica datos
4. Se validan los datos (validators.validate_purchase_data())
5. Se actualiza la compra (app_db.update_purchase())
6. Se registra en auditoría (log_audit())
7. Redirección a panel de administración
```

### Eliminar Compra
```
1. Admin hace clic en 🗑️ Eliminar
2. Se abre página de confirmación (GET /delete_purchase/{id})
3. Admin elige:
   a. Soft Delete: Marca como eliminada
      - Actualiza status a 'deleted'
      - Marca deleted_at
      - Datos permanecen recuperables
   
   b. Hard Delete: Elimina permanentemente
      - Elimina números asignados
      - Elimina compra de BD
      - No se puede deshacer
4. Se registra en auditoría
5. Redirección a panel de administración
```

---

## 🧪 Pruebas Recomendadas

### 1. **Edición de Compra**
- [ ] Editar referencia de pago
- [ ] Cambiar monto
- [ ] Modificar email
- [ ] Actualizar números
- [ ] Cambiar estado
- [ ] Agregar notas
- [ ] Validar rechaza datos inválidos

### 2. **Eliminación de Compra**
- [ ] Soft delete marca correctamente
- [ ] Hard delete elimina permanentemente
- [ ] Números se recuperan correctamente
- [ ] Confirmación aparece
- [ ] Advertencia es clara

### 3. **Validaciones**
- [ ] Email inválido es rechazado
- [ ] Monto negativo es rechazado
- [ ] Números fuera de rango rechazan
- [ ] Números duplicados se rechazan
- [ ] Referencia vacía se rechaza
- [ ] Mensajes de error son claros

### 4. **Seguridad**
- [ ] No autenticado no puede editar
- [ ] No autenticado no puede eliminar
- [ ] XSS no es posible
- [ ] SQL injection no es posible
- [ ] ID inválido es manejado

### 5. **Base de Datos**
- [ ] Nueva compra crea registro
- [ ] Actualización refleja cambios
- [ ] Soft delete marca deleted_at
- [ ] Hard delete remueve números
- [ ] Índices mejoran rendimiento

---

## 📈 Mejoras Futuras Sugeridas

1. **Auditoría Completa**
   - Implementar logging de todas las acciones
   - Dashboard de auditoría
   - Exportar logs

2. **Validación en Frontend**
   - JavaScript para validación en tiempo real
   - Indicadores visuales de campos válidos
   - Autocomplete para emails previos

3. **Recuperación de Soft Deletes**
   - Opción para recuperar compras eliminadas
   - Historial de cambios
   - Comparador de versiones

4. **Notificaciones**
   - Email al cliente cuando se cambia estado
   - Notificación al admin de cambios
   - Log de cambios en panel

5. **Filtros Avanzados**
   - Filtrar por rango de fechas
   - Filtrar por rango de montos
   - Búsqueda de números

6. **Reportes**
   - Reporte de cambios por período
   - Estadísticas de ediciones
   - Análisis de errores

---

## 🔧 Configuración Requerida

### Variables de Entorno (.env)
```
# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rifa_db
DB_USER=rifa_user
DB_PASSWORD=rifa_password

# Admin
ADMIN_PASSWORD=tu_contraseña_admin
ADMIN_SIM_KEY=tu_clave_simulacion

# Email
EMAIL_SENDER=tu_email@gmail.com
EMAIL_PASSWORD=tu_contraseña_app
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Seguridad
SECRET_KEY=tu_clave_secreta_flask
```

---

## 📞 Soporte y Documentación

Para más información sobre:
- Validaciones: Ver `app/validators.py`
- Base de datos: Ver `app/db.py`
- Rutas: Ver `server.py`
- Templates: Ver `templates/`

---

**Última actualización:** 12 de noviembre de 2025
**Versión:** 2.0
