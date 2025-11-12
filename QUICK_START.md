# 🚀 QUICK START - Guía Rápida de Instalación

## 1️⃣ Actualizar Base de Datos (1 minuto)

### Opción A: PostgreSQL
```bash
# Ejecutar script de migración
bash scripts/migrate_db.sh

# O ejecutar manualmente en psql
psql -U tu_usuario -d tu_base_de_datos -f migracion_postgresql.sql
```

### Opción B: SQLite
```bash
# Ejecutar en Python (automático)
python3 -c "from app import db; db.init_db()"
```

---

## 2️⃣ Reiniciar Servidor (1 minuto)

```bash
# Detener servidor actual (Ctrl+C)
# Reiniciar
python server.py

# O con ambiente virtual
source venv/bin/activate  # En macOS/Linux
python server.py
```

---

## 3️⃣ Verificar Instalación (2 minutos)

### Acceder al Panel
```
http://localhost:8080/administrador
```

### Login
- **Usuario:** admin
- **Contraseña:** (definida en `.env` como `ADMIN_PASSWORD`)

### Pruebas Rápidas

1. **Ver tabla de compras**
   - [ ] Botones "✏️ Editar" y "🗑️ Eliminar" visibles

2. **Probar edición**
   - [ ] Clic en "✏️ Editar"
   - [ ] Modificar un campo (ej: notas)
   - [ ] Clic "💾 Guardar Cambios"
   - [ ] Verificar cambio guardado

3. **Probar soft delete**
   - [ ] Clic en "🗑️ Eliminar"
   - [ ] Seleccionar "🔒 Marcar como eliminada"
   - [ ] Clic "Confirmar Eliminación"
   - [ ] Compra desaparece de lista (status = 'deleted')

---

## 4️⃣ Validación de Errores (5 minutos)

### Probar Validaciones

#### Email inválido
1. Editar compra
2. Cambiar email a: `email-invalido`
3. Guardar → Debe mostrar error

#### Número fuera de rango
1. Editar compra
2. Cambiar números a: `5000`
3. Guardar → Debe mostrar error

#### Monto negativo
1. Editar compra
2. Cambiar monto a: `-100`
3. Guardar → Debe mostrar error

---

## 📋 Checklist de Configuración

- [ ] Base de datos actualizada
- [ ] Servidor reiniciado
- [ ] Panel accesible en `/administrador`
- [ ] Botones de editar/eliminar visibles
- [ ] Edición funciona
- [ ] Soft delete funciona
- [ ] Validaciones funcionan
- [ ] Errores se muestran correctamente

---

## 🆘 Solución de Problemas

### "Módulo validators no encontrado"
```bash
# Asegurar que app/validators.py existe
ls -la app/validators.py

# Si no existe, crear manualmente desde docs/
```

### "Tabla audit_log no existe"
```bash
# Ejecutar migración nuevamente
bash scripts/migrate_db.sh

# O manualmente en SQLite
python3 -c "from app import db; db.init_db()"
```

### "Error de sintaxis en Python"
```bash
# Validar sintaxis
python3 -m py_compile app/db.py app/validators.py server.py

# Buscar errores específicos
python3 server.py
```

### "No puedo editar compras"
```bash
# Verificar sesión
# - Estás logueado? (/login primero)
# - Contraseña correcta?
# - Session cookie activa?
```

---

## 📚 Documentación Completa

Para más detalles, consulta:

| Archivo | Contenido |
|---------|-----------|
| `CAMBIOS_REALIZADOS.md` | Resumen de todas las mejoras |
| `docs/ADMIN_IMPROVEMENTS.md` | Documentación técnica detallada |
| `docs/TEST_CHECKLIST.md` | Lista completa de pruebas (150+) |
| `app/validators.py` | Código de validaciones con comentarios |
| `app/db.py` | Funciones de BD con documentación |

---

## 🎯 Próximos Pasos

### Si Todo Funciona ✅
1. Ejecutar pruebas del checklist completo
2. Probar en producción con datos reales
3. Implementar mejoras futuras

### Si Hay Errores ❌
1. Revisar logs del servidor
2. Consultar "Solución de Problemas"
3. Verificar que todos los archivos están en su lugar
4. Contactar soporte con el error específico

---

## 💾 Backup

Antes de cambios en producción, hacer backup:

```bash
# PostgreSQL
pg_dump -U usuario base_de_datos > backup.sql

# SQLite
cp rifa.db rifa.db.backup

# Archivos
cp -r templates/ templates.backup/
cp -r static/ static.backup/
```

---

## ✅ ¡Listo!

Si completaste todos los pasos anteriores, **¡tu sistema está actualizado y funcionando!** 🎉

Para dudas o problemas, consulta la documentación detallada en `docs/ADMIN_IMPROVEMENTS.md`

---

**Última actualización:** 12 de noviembre de 2025
**Versión:** 2.0
