# Guía de despliegue y uso - Rifa Profesional

## 1. Estructura del proyecto

```
python/
  ├── server.py                # Backend Flask principal
  ├── templates/
  │     └── index.html         # Plantilla principal (Jinja2)
  └── static/
        ├── css/
        │     ├── styles_rifa.css
        │     ├── footer.css
        │     └── loading.css
        ├── js/
        │     └── loading.js
        └── img/               # Imágenes y logos
```

## 2. Requisitos
- Python 3.8+
- pip
- (Opcional) Docker

## 3. Instalación local

1. Ve a la carpeta `python/`:
   ```sh
   cd python
   ```
2. Instala dependencias:
   ```sh
   pip install flask flask-wtf python-dotenv
   ```
3. Crea un archivo `.env` con tus claves:
   ```env
   SECRET_KEY=tu_clave_secreta
   EPAYCO_SECRET=tu_clave_epayco
   ```
4. Ejecuta el servidor:
   ```sh
   python server.py
   ```
5. Accede a `http://localhost:8080` en tu navegador.

## 4. Despliegue con Docker

1. Desde la raíz del proyecto:
   ```sh
   docker build -t rifa-app ./python
   docker run -d -p 8080:8080 --env-file python/.env rifa-app
   ```

## 5. Seguridad y buenas prácticas
- CSRF y validación de datos ya implementados.
- Webhook de ePayco protegido con firma HMAC.
- No expongas tu `.env` ni claves en repositorios públicos.

## 6. Personalización
- Edita `python/templates/index.html` para cambiar la UI.
- Agrega imágenes en `python/static/img/`.
- Modifica estilos en `python/static/css/`.

## 7. Contacto y soporte
- Para dudas, revisa el código fuente o contacta al desarrollador.

---

¡Listo para usar y desplegar tu rifa profesional!
