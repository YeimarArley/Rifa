# 📖 Guía de Instalación Paso a Paso

## ⏱️ Tiempo total: 10-15 minutos

---

## PASO 1️⃣: Revisar Cambios (2 minutos)

**Antes de empezar, lee:**
- `CAMBIOS_REALIZADOS.md` - Resumen de todas las mejoras
- `ESTRUCTURA_ARCHIVOS.md` - Qué archivos son nuevos

```bash
# Navegar a carpeta del proyecto
cd "/Users/yeimararley/Desktop/aplicaciones/Rifa copia"

# Ver cambios (opcional)
cat CAMBIOS_REALIZADOS.md | head -50
```

---

## PASO 2️⃣: Hacer Backup (2 minutos)

**Esto es IMPORTANTE antes de cualquier cambio en producción.**

```bash
# Crear carpeta de backup
mkdir -p backups/$(date +%Y%m%d_%H%M%S)

# Backup de BD SQLite
cp rifa.db backups/$(date +%Y%m%d_%H%M%S)/rifa.db.backup

# Backup de archivos importantes
cp -r templates/ backups/$(date +%Y%m%d_%H%M%S)/
cp -r static/ backups/$(date +%Y%m%d_%H%M%S)/
cp server.py backups/$(date +%Y%m%d_%H%M%S)/

echo "✅ Backup completado"
```

**Para PostgreSQL:**
```bash
# Si usas PostgreSQL, haz dump de la BD
pg_dump -U tu_usuario tu_base_datos > backups/db_backup.sql
```

---

## PASO 3️⃣: Validar Sintaxis de Python (1 minuto)

**Verificar que no hay errores en los archivos Python.**

```bash
# Compilar archivos para detectar errores
python3 -m py_compile app/db.py app/validators.py server.py

# Si no hay output = sin errores ✅
```

---

## PASO 4️⃣: Actualizar Base de Datos (2 minutos)

### Opción A: Usar Script Automático (Recomendado)

```bash
# Hacer ejecutable el script
chmod +x scripts/migrate_db.sh

# Ejecutar
bash scripts/migrate_db.sh

# Ver output para confirmar
```

### Opción B: Manual con SQLite

```bash
# Python ejecutará init_db() automáticamente
python3 -c "from app import db; db.init_db()"

# Verificar que se crearon tablas
sqlite3 rifa.db ".tables"
# Debe mostrar: admin_users  assigned_numbers  audit_log  purchases
```

### Opción C: Manual con PostgreSQL

```bash
# En tu terminal PostgreSQL
psql -U tu_usuario -d tu_base_datos

# Ejecutar SQL:
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agregar campos nuevos a tabla purchases
ALTER TABLE purchases ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE purchases ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE purchases ADD COLUMN IF NOT EXISTS notes TEXT;

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases(email);
CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at);

# Salir
\q
```

---

## PASO 5️⃣: Configurar Variables de Entorno (1 minuto)

**Verificar que .env tiene las configuraciones necesarias:**

```bash
# Editar archivo .env (si existe)
cat .env

# Debe contener (agregar si faltan):
ADMIN_PASSWORD=tu_contraseña_admin
ADMIN_SIM_KEY=tu_clave_simulacion
SECRET_KEY=tu_clave_secreta_flask
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rifa_db
DB_USER=rifa_user
DB_PASSWORD=rifa_password
```

---

## PASO 6️⃣: Reiniciar Servidor (2 minutos)

```bash
# Detener servidor actual (si está corriendo)
# Presiona: Ctrl + C

# Reiniciar servidor
python server.py

# Debe mostrar:
# * Running on http://0.0.0.0:8080
# * Initialized Postgres/sqlite tables
# * DEBUG = False
```

**Si hay error:** Ver sección "Solucionar Problemas" al final.

---

## PASO 7️⃣: Acceder al Panel (1 minuto)

**Abrir navegador:**

```
http://localhost:8080/administrador
```

**Si te pide login:**
- Email: (no necesario para login simple)
- Contraseña: Tu `ADMIN_PASSWORD` (ver .env)

**Debe mostrar:**
- ✅ Tabla de compras con botones "✏️ Editar" y "🗑️ Eliminar"
- ✅ Métricas principales
- ✅ Gráficos
- ✅ Filtros

---

## PASO 8️⃣: Probar Funcionalidad (3 minutos)

### Prueba 1: Editar Compra

```
1. Haz clic en botón "✏️ Editar"
2. Se abre formulario con datos actuales
3. Modifica un campo (ej: Notas)
4. Haz clic "💾 Guardar Cambios"
5. Verifica que cambio se guardó
✅ Si llegaste aquí = EDICIÓN FUNCIONA
```

### Prueba 2: Validaciones

```
1. Haz clic en "✏️ Editar"
2. Cambia email a: "email-invalido" (sin @)
3. Intenta guardar
4. Debe mostrar error: "Formato de email inválido"
✅ Si ves error = VALIDACIONES FUNCIONAN
```

### Prueba 3: Soft Delete

```
1. Haz clic en "🗑️ Eliminar"
2. Se abre página de confirmación
3. Asegúrate que "🔒 Marcar como eliminada" está seleccionado
4. Haz clic "Confirmar Eliminación"
5. Compra desaparece de la lista
✅ Si desapareció = SOFT DELETE FUNCIONA
```

### Prueba 4: Hard Delete (Opcional - Cuidado)

```
1. Haz clic en "🗑️ Eliminar" en otra compra
2. Selecciona "🗑️ Eliminar permanentemente"
3. Lee la advertencia (NO SE PUEDE DESHACER)
4. Haz clic "Confirmar Eliminación"
5. Solicita confirmación extra (alert)
6. Compra se elimina permanentemente
✅ Si se eliminó = HARD DELETE FUNCIONA
```

---

## PASO 9️⃣: Verificar Logs (1 minuto)

**En la consola donde corre el servidor, debes ver:**

```
[INFO] Purchase X updated by admin
[INFO] Purchase X marked as deleted by admin
[WARNING] Purchase X PERMANENTLY DELETED by admin
```

**Si ves estos logs = LOGGING FUNCIONA ✅**

---

## 🔟 (Opcional) Ejecutar Checklist Completo

**Para verificación exhaustiva, ejecuta:**

```bash
# Ver documento de pruebas
cat docs/TEST_CHECKLIST.md

# Seguir todas las 150+ pruebas
# Marcar ✅ cuando cada una pase
```

---

## ✅ Checklist de Instalación

- [ ] He leído `CAMBIOS_REALIZADOS.md`
- [ ] He hecho backup de la BD
- [ ] He validado sintaxis de Python
- [ ] He ejecutado migración de BD
- [ ] He verificado .env
- [ ] He reiniciado servidor
- [ ] Puedo acceder a `/administrador`
- [ ] Botones de editar/eliminar son visibles
- [ ] Edición de compra funciona
- [ ] Validaciones funcionan
- [ ] Soft delete funciona
- [ ] Veo logs en consola

**Si TODOS tienen ✅ = INSTALACIÓN EXITOSA 🎉**

---

## 🆘 Solucionar Problemas

### "AttributeError: module 'app' has no attribute 'validators'"

**Solución:**
```bash
# Verificar que archivo existe
ls -la app/validators.py

# Si no existe, copiar desde docs/ o crear
touch app/validators.py
```

### "Error: table admin_users does not exist"

**Solución:**
```bash
# Ejecutar migración nuevamente
bash scripts/migrate_db.sh

# O manualmente
python3 -c "from app import db; db.init_db()"
```

### "SyntaxError: unexpected EOF while parsing"

**Solución:**
```bash
# Validar sintaxis
python3 -m py_compile app/db.py app/validators.py

# Ver línea exacta del error
python3 -m py_compile app/validators.py 2>&1 | grep -A 5 "SyntaxError"
```

### "No puedo editar compras"

**Verificar:**
1. ¿Estás logueado? (Intenta ir a `/login`)
2. ¿La contraseña es correcta?
3. ¿La sesión es válida?

```bash
# Revisar en servidor
# Busca línea: "ERROR" o "401"
```

### "Botones de editar/eliminar no aparecen"

**Verificar:**
1. ¿Actualizó `administrador.html`?
2. ¿Limpió caché del navegador? (Ctrl+Shift+Delete)
3. ¿Los templates se cargaron correctamente?

```bash
# Ver en navegador
# Abre Developer Tools (F12)
# Tab "Elements" → busca "actions-cell"
```

---

## 📞 Información de Contacto

Si tienes problemas después de seguir esta guía:

1. **Revisar documentación:**
   - `docs/ADMIN_IMPROVEMENTS.md` - Técnico
   - `docs/TEST_CHECKLIST.md` - Pruebas

2. **Verificar logs:**
   ```bash
   # Ver logs del servidor
   # Buscar mensajes de ERROR
   ```

3. **Validar archivos:**
   ```bash
   # Verificar que todos los archivos existen
   ls -la app/
   ls -la templates/ | grep -E "edit_purchase|delete_purchase|error.html"
   ```

---

## 🎉 ¡Felicidades!

Si completaste todos los pasos y las pruebas pasaron, **tu sistema de administración está completamente actualizado y funcionando correctamente.**

**Próximos pasos recomendados:**

1. ✅ Hacer backup regular
2. ✅ Monitorear logs en producción
3. ✅ Implementar mejoras futuras
4. ✅ Entrenar a otros admins

---

**Versión de guía:** 2.0
**Fecha:** 12 de noviembre de 2025
**Estado:** ✅ Listo para implementación
