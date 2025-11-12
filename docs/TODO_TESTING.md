# TODO - Pruebas del Flujo Completo ePayco

## Estado Actual
- ✅ Servidor corriendo en localhost:8080
- ✅ Ngrok configurado y funcionando: https://hypnotically-scissile-jazlyn.ngrok-free.app
- ✅ Credenciales de email configuradas en .env
- ✅ URLs de response y confirmation actualizadas en index.html
- ✅ Email de prueba enviado exitosamente

## Próximas Tareas de Prueba

### 1. Verificar Acceso a la Página Principal
- [ ] Acceder a https://hypnotically-scissile-jazlyn.ngrok-free.app/
- [ ] Verificar que la página carga correctamente
- [ ] Confirmar que los botones "COMPRAR CON PSE" están visibles

### 2. Probar Endpoints API
- [ ] GET / - Página principal
- [ ] GET /response - Página de respuesta de pago
- [ ] POST /confirmation - Webhook de confirmación ePayco
- [ ] Verificar que todos respondan correctamente

### 3. Simular Transacción ePayco
- [ ] Enviar POST simulado a /confirmation con datos de prueba
- [ ] Verificar que se guarde en base de datos
- [ ] Confirmar que se envíe email de confirmación

### 4. Probar Flujo Completo Manual
- [ ] Abrir página en navegador
- [ ] Hacer clic en botón de compra
- [ ] Verificar modal de ePayco
- [ ] Completar pago de prueba (requiere credenciales ePayco)

### 5. Verificar Integración Email
- [ ] Confirmar envío automático de emails tras confirmación
- [ ] Verificar contenido del email (números asignados)

## Notas Importantes
- Para pruebas reales de pago, configurar credenciales ePayco en .env
- El servidor debe estar corriendo durante todas las pruebas
- Ngrok debe estar activo para acceso externo
