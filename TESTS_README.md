# Guía de Pruebas de Base de Datos

Este documento explica cómo probar que la base de datos funciona correctamente.

## Scripts Disponibles

### 1. `test_database.py` - Pruebas Automáticas Completas

Ejecuta una suite completa de pruebas automáticas que verifican:
- ✅ Conexión a la base de datos
- ✅ Existencia de tablas
- ✅ Inserción de compras
- ✅ Inserción de números asignados
- ✅ Conteo de números asignados
- ✅ Consultas de compras
- ✅ Lógica de asignación de números
- ✅ Limpieza de datos de prueba

**Uso:**
```bash
python test_database.py
# o
py test_database.py
```

El script mostrará un resumen con colores:
- 🟢 Verde: Prueba pasó
- 🔴 Rojo: Prueba falló
- 🔵 Azul: Información
- 🟡 Amarillo: Advertencia

### 2. `test_database_interactive.py` - Pruebas Interactivas

Script interactivo con menú para probar manualmente diferentes operaciones.

**Uso:**
```bash
python test_database_interactive.py
# o
py test_database_interactive.py
```

**Opciones del menú:**
1. Verificar conexión - Prueba la conexión a la base de datos
2. Ver estado de la base de datos - Muestra estadísticas generales
3. Insertar compra de prueba - Crea una compra de prueba
4. Ver todas las compras - Lista todas las compras en la BD
5. Ver números asignados - Muestra los números que ya están asignados
6. Contar números asignados - Cuenta total de números asignados
7. Simular asignación de números - Simula qué números se asignarían
8. Limpiar datos de prueba - Elimina compras de prueba (test_*)
9. Salir

## Ejemplos de Uso

### Ejecutar todas las pruebas automáticas
```bash
python test_database.py
```

### Probar manualmente la conexión
```bash
python test_database_interactive.py
# Selecciona opción 1
```

### Insertar una compra de prueba
```bash
python test_database_interactive.py
# Selecciona opción 3
# Ingresa los datos cuando se solicite
```

## Verificación de Funcionalidad

### Verificar que la conexión funciona:
```python
from app import db
conn = db.get_postgres_connection()
print("¡Conexión exitosa!")
```

### Verificar que las tablas existen:
```python
from app import db
result = db.run_query("SELECT COUNT(*) FROM purchases", fetchone=True)
print(f"Total de compras: {result[0]}")
```

### Verificar inserción:
```python
from app import db
import uuid

invoice_id = f"test_{uuid.uuid4().hex[:10]}"
db.run_query(
    "INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')",
    params=(invoice_id, 25000, "test@example.com", "1,2,3,4"),
    commit=True
)
print(f"Compra {invoice_id} insertada correctamente")
```

## Solución de Problemas

### Error: "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Error: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Error de conexión a la base de datos
1. Verifica que el archivo `.env` existe y tiene `DATABASE_URL` configurado
2. Verifica que la cadena de conexión es correcta
3. Verifica que tienes acceso a internet (si es Neon/cloud)

### Las pruebas fallan pero la app funciona
- Los scripts de prueba crean datos temporales que se limpian al final
- Si hay un error durante la limpieza, puedes limpiar manualmente:
```sql
DELETE FROM purchases WHERE invoice_id LIKE 'test_%';
DELETE FROM assigned_numbers WHERE invoice_id LIKE 'test_%';
```

## Notas Importantes

- ⚠️ Los scripts de prueba crean datos temporales con prefijo `test_`
- ⚠️ Los datos de prueba se eliminan automáticamente al final de las pruebas
- ✅ Las pruebas no afectan datos de producción
- ✅ Puedes ejecutar las pruebas múltiples veces de forma segura

## Integración con CI/CD

Para usar en pipelines de CI/CD:

```bash
python test_database.py
if [ $? -eq 0 ]; then
    echo "Todas las pruebas pasaron"
    exit 0
else
    echo "Algunas pruebas fallaron"
    exit 1
fi
```

