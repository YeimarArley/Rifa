# ✅ Checklist de Pruebas - Sistema de Administración

## 1. Configuración Inicial
- [ ] Verificar que todas las variables de entorno están configuradas (.env)
- [ ] Confirmar conexión a la base de datos
- [ ] Ejecutar script de migración: `bash scripts/migrate_db.sh`
- [ ] Reiniciar servidor: `python server.py`

## 2. Autenticación
- [ ] Acceder a http://localhost:8080/login
- [ ] Ingresar contraseña correcta (ADMIN_PASSWORD)
- [ ] Verificar que se abre el panel de administrador
- [ ] Intentar acceso sin autenticación (debe redirigir a login)
- [ ] Verificar enlace "Cerrar Sesión" funciona

## 3. Panel de Administración
- [ ] Mostrar métricas correctas (números asignados, disponibles, etc.)
- [ ] Gráficos se cargan sin errores
- [ ] Tabla de compras muestra datos
- [ ] Botones de filtro funcionan
- [ ] Paginación funciona correctamente
- [ ] Nueva columna "Acciones" es visible

## 4. Funciones de Edición

### Acceso al Formulario
- [ ] Clic en botón "✏️ Editar" abre formulario
- [ ] URL es `/edit_purchase/{id}`
- [ ] Datos actuales se cargan en el formulario
- [ ] Fecha de creación se muestra correctamente

### Edición de Campos
- [ ] Campo Referencia de Pago editable
- [ ] Campo Monto editable
- [ ] Campo Email editable
- [ ] Campo Números editable
- [ ] Selector de Estado funciona (pending, confirmed, cancelled, deleted)
- [ ] Campo Notas editable

### Validaciones
- [ ] Email vacío muestra error
- [ ] Email inválido muestra error
- [ ] Monto vacío muestra error
- [ ] Monto negativo muestra error
- [ ] Monto con letras muestra error
- [ ] Referencia vacía muestra error
- [ ] Números fuera de rango (>2000 o <1) muestran error
- [ ] Números duplicados muestran error
- [ ] Mensajes de error son claros y útiles

### Guardado
- [ ] Clic en "💾 Guardar Cambios" actualiza la compra
- [ ] Redirige a panel de administrador después de guardar
- [ ] Cambios se reflejan en la tabla
- [ ] El historial (updated_at) se actualiza

### Cancelación
- [ ] Clic en "❌ Cancelar" regresa al panel sin guardar
- [ ] Los cambios NO se guardan si se cancela

## 5. Funciones de Eliminación

### Acceso a Confirmación
- [ ] Clic en botón "🗑️ Eliminar" abre página de confirmación
- [ ] URL es `/delete_purchase/{id}`
- [ ] Datos de la compra se muestran correctamente
- [ ] Advertencia es clara y visible

### Opciones de Eliminación

#### Soft Delete (Marcado)
- [ ] Opción "🔒 Marcar como eliminada" está seleccionada por defecto
- [ ] Descripción explica que es reversible
- [ ] Al confirmar, compra se marca como deleted
- [ ] Campo deleted_at se actualiza
- [ ] Números se recuperan
- [ ] Compra no desaparece de la BD (datos recuperables)

#### Hard Delete (Permanente)
- [ ] Opción "🗑️ Eliminar permanentemente" disponible
- [ ] Descripción advierte que no se puede deshacer
- [ ] Requiere confirmación adicional
- [ ] Al confirmar, compra se elimina completamente
- [ ] Números asignados se eliminan
- [ ] Hard delete requiere confirmación JavaScript extra

### Cancelación
- [ ] Clic en "❌ Cancelar" regresa al panel sin eliminar

## 6. Validaciones de Seguridad

### Inyección de Datos
- [ ] Intentar inyectar HTML en email (debe escaparse)
- [ ] Intentar SQL injection en números (debe validarse)
- [ ] Intentar código malicioso en notas (debe escaparse)

### Acceso No Autorizado
- [ ] Sin sesión: intenta acceder a `/edit_purchase/1` (redirige a login)
- [ ] Sin sesión: intenta acceder a `/delete_purchase/1` (redirige a login)
- [ ] ID inválido (letras): debe mostrar error

### Límites de Datos
- [ ] Email muy largo (>255 chars) - rechaza
- [ ] Referencia muy larga (>255 chars) - rechaza
- [ ] Notas muy largas (>1000 chars) - rechaza
- [ ] Monto muy grande (>999999999.99) - rechaza

## 7. Base de Datos

### Estructura
- [ ] Tabla purchases tiene campos updated_at, deleted_at, notes
- [ ] Tabla admin_users existe
- [ ] Tabla audit_log existe
- [ ] Índices están creados
- [ ] Foreign keys están correctos

### Datos
- [ ] Nueva compra se crea correctamente
- [ ] Actualización de compra refleja cambios
- [ ] Soft delete marca deleted_at
- [ ] Hard delete remueve registro
- [ ] Números se recuperan en delete

### Compatibilidad
- [ ] SQLite funciona sin errores
- [ ] PostgreSQL funciona sin errores
- [ ] Fallback a SQLite si PostgreSQL no está disponible

## 8. Interfaz de Usuario

### Responsividad
- [ ] Tabla visible en desktop (≥1024px)
- [ ] Tabla responsiva en tablet (768px-1023px)
- [ ] Botones accesibles en móvil (<768px)
- [ ] Formularios legibles en todos los tamaños
- [ ] Confirmaciones claras en móvil

### Diseño
- [ ] Colores consistentes (azul edit, rojo delete)
- [ ] Iconos son intuitivos
- [ ] Espaciado adecuado
- [ ] Tipografía legible
- [ ] Sin errores de CSS

### Accesibilidad
- [ ] Labels vinculados con inputs
- [ ] Contraste de color adecuado
- [ ] Botones diferenciados visualmente
- [ ] Mensajes de error accesibles

## 9. Logging y Auditoría

### Logs en Servidor
- [ ] Edición de compra registra: "Purchase X updated by admin"
- [ ] Eliminación suave registra: "Purchase X marked as deleted by admin"
- [ ] Eliminación permanente registra: "Purchase X PERMANENTLY DELETED by admin"
- [ ] Errores registran: error details

### Auditoría en BD
- [ ] Función log_audit() funciona (cuando se implemente completamente)
- [ ] Tabla audit_log se llena (cuando se implemente completamente)

## 10. Rendimiento

### Carga
- [ ] Panel carga en < 2 segundos
- [ ] Tabla con 100 compras carga correctamente
- [ ] Filtros responden rápidamente
- [ ] Paginación es fluida

### Índices
- [ ] Búsqueda por email es rápida (idx_purchases_email)
- [ ] Filtro por estado es rápido (idx_purchases_status)
- [ ] Ordenamiento por fecha es rápido (idx_purchases_created_at)

## 11. Casos Edge

### IDs Especiales
- [ ] ID = 0 muestra error
- [ ] ID = -1 muestra error
- [ ] ID = 999999 (no existe) muestra error
- [ ] ID = "abc" muestra error

### Números Especiales
- [ ] Número 0 rechaza
- [ ] Número 2001 rechaza
- [ ] Números vacíos rechazan
- [ ] Espacios en blancos se manejan correctamente

### Estados Especiales
- [ ] Cambiar de pending a confirmed funciona
- [ ] Cambiar de confirmed a cancelled funciona
- [ ] Cambiar a deleted funciona
- [ ] Estado inválido rechaza

## 12. Navegación

### Enlaces
- [ ] "← Volver al Panel" regresa a /administrador
- [ ] "← Inicio" regresa a /
- [ ] "Cerrar Sesión" limpia sesión
- [ ] Botones de paginación funcionan

### Flujos
- [ ] Edit → Guardar → Panel (correcto)
- [ ] Edit → Cancelar → Panel (correcto)
- [ ] Delete → Soft Delete → Panel (correcto)
- [ ] Delete → Hard Delete → Panel (correcto)
- [ ] Delete → Cancelar → Panel (correcto)

## Resumen de Estado

**Total de pruebas:** 150+
**Completadas:** ___
**Fallidas:** ___
**Pendientes:** ___

**Fecha de prueba:** ___
**Tester:** ___
**Observaciones:** 

```

```

---

## ✅ Aprobación

- [ ] Todas las pruebas pasadas
- [ ] No hay errores críticos
- [ ] Funcionalidad completa
- [ ] Seguridad validada
- [ ] UI/UX aceptable

**Aprobado por:** _______________
**Fecha:** _______________
