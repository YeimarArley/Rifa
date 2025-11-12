# Rifa Familiones — Plataforma de Rifas

## Estructura profesional
- `app/` — Lógica de base de datos (Postgres/SQLite fallback)
- `templates/` — Plantillas HTML (Jinja2)
- `static/` — Archivos estáticos (CSS, imágenes)
- `server.py` — Servidor Flask principal
- `requirements.txt` — Dependencias Python
- `docker-compose-postgres.yml` — Servicio Postgres listo para desarrollo

## Arranque rápido (desarrollo local)

```zsh
cd "/Users/yeimararley/Desktop/aplicaciones/Rifa copia"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 server.py
```

- Accede a: http://127.0.0.1:8080/
- El progreso de ventas se actualiza automáticamente en la UI.

## Variables de entorno útiles

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — para usar Postgres (si no, usa SQLite por defecto)
- `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_SMTP_SERVER`, `EMAIL_SMTP_PORT` — para notificaciones por correo
- Puedes usar un archivo `.env` (usa [python-dotenv](https://pypi.org/project/python-dotenv/))

## Usar Postgres con Docker Compose

```zsh
docker-compose -f docker-compose-postgres.yml up -d
# Espera a que el servicio esté disponible
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=rifa_db
export DB_USER=rifa_user
export DB_PASSWORD=rifa_password
python3 server.py
```

### Inicializar la base de datos y seed (opcional)

Se incluyen scripts para crear el usuario/BDD y aplicar la migración SQL, y para seedear los números 1..2000.

Con Docker Compose (recomendado):

```zsh
docker-compose -f docker-compose-postgres.yml up -d
# Rellenar .env o exportar variables
make init-db   # ejecuta scripts/init_db.sh
make seed      # agrega números 1..2000 (si lo deseas)
```

También puedes usar el Makefile para tareas comunes:

```zsh
make setup   # crea venv e instala deps
make run     # ejecuta servidor (dev)
make test    # ejecuta tests
```

## Endpoint de simulación de compras (admin)

- POST `/admin/simulate_purchase` con clave y cantidad de números:
```zsh
curl -X POST http://127.0.0.1:8080/admin/simulate_purchase \
  -d 'key=CLAVEADMIN&amount=4&email=test@demo.com'
```
- Cambia `CLAVEADMIN` por la clave definida en el código.

## Pruebas rápidas

- Testea `/progress`:
```zsh
curl http://127.0.0.1:8080/progress
```
- Testea helpers de base de datos:
```zsh
python3 -m unittest discover tests
```

## Troubleshooting
- Si no tienes Postgres, la app usará `rifa.db` (SQLite) automáticamente.
- Si cambias de SQLite a Postgres, asegúrate de crear las tablas o deja que el sistema las cree al arrancar.
- Para producción, usa un servidor WSGI (gunicorn/uvicorn) y configura correctamente las variables de entorno.

---

Desarrollado por NOVA51 — Yeimar Arley, Yeiver & Faider Asprilla
