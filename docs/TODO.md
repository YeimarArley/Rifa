# TODO: Integración de PostgreSQL en Docker y Migración desde SQLite

## Estado Actual
- [x] Proyecto usa SQLite en server.py
- [x] docker-compose-postgres.yml existe pero falta migracion_postgresql.sql
- [x] requirements.txt incluye psycopg2-binary

## Plan de Implementación
- [ ] Crear migracion_postgresql.sql con esquemas de tablas
- [ ] Modificar server.py para usar PostgreSQL en lugar de SQLite
- [ ] Actualizar docker-compose.yml para incluir PostgreSQL y pgAdmin
- [ ] Probar la integración con Docker Compose

## Archivos a Crear/Modificar
- migracion_postgresql.sql: Nuevo archivo con esquemas SQL
- server.py: Cambiar de sqlite3 a psycopg2
- docker-compose.yml: Agregar servicios de PostgreSQL y pgAdmin

## Pasos de Seguimiento
- [ ] Ejecutar docker-compose up y verificar que PostgreSQL inicie
- [ ] Probar endpoints de la aplicación
- [ ] Migrar datos existentes de SQLite a PostgreSQL (opcional)
- [ ] Verificar que la asignación de números funcione correctamente
