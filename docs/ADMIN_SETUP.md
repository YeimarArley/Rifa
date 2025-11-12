# 📋 Guía del Panel de Administrador - Rifa

## Acceso y Autenticación

### Entrar al Panel Admin
1. Navega a: `http://localhost:8080/login`
2. Ingresa la contraseña de administrador (por defecto: `admin123`)
3. Se redirige automáticamente a `/administrador`

### Configurar Contraseña Personalizada
Edita tu archivo `.env`:
```env
ADMIN_PASSWORD=tu_contrasena_segura
SECRET_KEY=tu_clave_secreta_para_sesiones
```

Luego reinicia la aplicación.

### Cerrar Sesión
Haz clic en el botón **"Cerrar Sesión"** en la esquina superior derecha del panel.

---

## Funcionalidades del Panel

### 📊 Métricas Principales
Cuatro tarjetas en el inicio muestran:
- **Números asignados**: Cantidad de tickets vendidos
- **Números disponibles**: Tickets restantes (de 2000 total)
- **Total compras**: Cantidad de transacciones registradas
- **Progreso vendido**: Porcentaje de venta (%)

### 📈 Gráficos Interactivos
- **Gráfico de Progreso (Doughnut)**: Visualiza vendidos vs disponibles
- **Gráfico de Estados (Barras)**: Muestra compras confirmadas, pendientes y canceladas

### 🔍 Filtros y Búsqueda
Filtra las compras por:
- **Estado**: Confirmado, Pendiente, Cancelado
- **Email**: Búsqueda parcial del correo del comprador

Botones disponibles:
- **🔍 Buscar**: Aplica los filtros
- **Limpiar**: Reestablece todos los filtros
- **📥 Descargar CSV**: Exporta todas las compras a un archivo CSV

### 📋 Tabla de Compras (Paginada)
Muestra:
- **ID**: Identificador único
- **Referencia**: ID de transacción de pago
- **Monto**: Valor en pesos
- **Email**: Correo del comprador
- **Números**: Los primeros números asignados (primeros 20 caracteres)
- **Estado**: Badge de color según estado
- **Fecha**: Timestamp de la compra

**15 compras por página** con navegación:
- ⏮ Primera, ← Anterior, Siguiente →, Última ⏭

### ⚙️ Acciones Administrativas

#### Simular Compra
Permite crear una transacción de prueba sin usar el sistema de pago:
1. Selecciona cantidad de tickets (4, 8, 12, 16, 20)
2. Ingresa un email de prueba
3. Haz clic en **➕ Simular**

La aplicación asignará números disponibles automáticamente.

---

## Exportar Datos

### Descargar CSV
1. (Opcional) Aplica filtros deseados
2. Haz clic en **📥 Descargar CSV**
3. Se descarga un archivo `compras_YYYYMMDD_HHMMSS.csv`

**Columnas del CSV**:
- ID
- Referencia
- Monto
- Email
- Números
- Estado
- Fecha

### Usar el CSV
Abre el archivo con:
- Excel
- Google Sheets
- Python Pandas
- Cualquier editor de texto

---

## API de Estadísticas

### Endpoint: `/administrador/stats` (JSON)

Retorna datos estructurados para integraciones:

**Petición**:
```bash
curl -X GET http://localhost:8080/administrador/stats
```

**Respuesta**:
```json
{
  "assigned": 30,
  "available": 1970,
  "total": 2000,
  "percentage": 1.5,
  "statuses": {
    "confirmed": 8,
    "pending": 0,
    "cancelled": 0
  }
}
```

---

## Flujo de Compra y Estados

### Estados de Transacción
1. **pending**: Compra iniciada, pero no confirmada por el pago
2. **confirmed**: Pago completado, tickets asignados
3. **cancelled**: Compra cancelada o rechazada

---

## Seguridad

⚠️ **Notas Importantes**:
1. **Cambia la contraseña por defecto** antes de pasar a producción
2. **Usa HTTPS** en producción (no HTTP)
3. **Protege tu `.env`** y no lo subas a control de versiones
4. **SECRET_KEY** debe ser una cadena aleatoria fuerte

Ejemplo de variable de entorno segura:
```bash
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
```

---

## Solución de Problemas

### "Contraseña incorrecta"
- Verifica que escribiste la contraseña correcta
- Comprueba que `ADMIN_PASSWORD` en `.env` es correcta
- Reinicia la aplicación después de cambiar `.env`

### "Sesión expirada"
- Inicia sesión nuevamente
- Las sesiones se basan en `SECRET_KEY`, no tienen expiración automática
- Cerrar el navegador no cierra la sesión en el servidor

### No puedo descargar el CSV
- Verifica que tienes permisos de escritura en la carpeta
- Comprueba que el navegador permite descargas
- Revisa la consola del navegador (F12) para errores

### Los gráficos no se cargan
- Verifica que Chart.js se carga (CDN): https://cdn.jsdelivr.net/npm/chart.js
- Abre la consola del navegador (F12) para errores de JavaScript
- Asegúrate de tener datos en la base de datos

---

## Ejemplos de Uso

### Monitorear Progreso
1. Abre `/administrador`
2. Observa el gráfico doughnut de progreso
3. Actualiza cada hora (F5)

### Buscar una Compra Específica
1. Filtra por **Email**: `usuario@ejemplo.com`
2. Haz clic en **🔍 Buscar**
3. Ve la tabla con compras coincidentes

### Generar Reporte Mensual
1. Abre `/administrador`
2. Haz clic en **📥 Descargar CSV**
3. Abre el archivo en Excel
4. Crea un pivot table o gráficos

---

## Contacto y Soporte

Si encuentras problemas o tienes sugerencias, contacta al equipo de desarrollo.

**Última actualización**: Noviembre 2025
