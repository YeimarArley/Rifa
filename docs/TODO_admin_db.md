# TODO: Agregar Administración de Base de Datos desde la Web

## Información Recopilada
- Endpoint actual `/database` muestra tabla HTML con compras y números asignados
- Base de datos SQLite con tablas: purchases y assigned_numbers
- Servidor Flask corriendo en 0.0.0.0 para acceso desde otros dispositivos

## Plan de Implementación
- [ ] Modificar endpoint `/database` para incluir botones de acción (Editar/Eliminar)
- [ ] Agregar endpoint `/edit_purchase/<id>` para editar registros
- [ ] Agregar endpoint `/delete_purchase/<id>` para eliminar registros
- [ ] Agregar protección básica con contraseña simple
- [ ] Mejorar el diseño de la página de administración

## Archivos a Modificar
- server.py: Agregar nuevos endpoints y modificar /database

## Pasos de Seguimiento
- [ ] Probar acceso desde otros dispositivos
- [ ] Verificar que las operaciones CRUD funcionen correctamente
- [ ] Agregar validaciones de seguridad adicionales si es necesario
