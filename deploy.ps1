# ============================================
# SCRIPT DE DESPLIEGUE LOCAL - WINDOWS
# ============================================

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Log {
    param($Message)
    Write-ColorOutput Green "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

function Error {
    param($Message)
    Write-ColorOutput Red "[ERROR] $Message"
    exit 1
}

function Warning {
    param($Message)
    Write-ColorOutput Yellow "[WARNING] $Message"
}

Write-Host ""
Write-ColorOutput Cyan "🚀 =================================="
Write-ColorOutput Cyan "   DESPLIEGUE LOCAL - DESARROLLO"
Write-ColorOutput Cyan "=================================="
Write-Host ""

# 1. Verificar Docker
Log "Verificando Docker Desktop..."
try {
    docker --version | Out-Null
    docker-compose --version | Out-Null
} catch {
    Error "Docker Desktop no está instalado o no está corriendo. Abre Docker Desktop primero."
}

# 2. Verificar que Docker está corriendo
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Error "Docker Desktop no está corriendo. Abre Docker Desktop y espera a que inicie."
}
Log "✅ Docker Desktop está corriendo"

# 3. Copiar archivo .env
Log "Configurando archivo .env..."
if (Test-Path ".env") {
    Warning "Ya existe un archivo .env, se usará el existente"
} else {
    if (Test-Path ".env.local") {
        Copy-Item ".env.local" ".env"
        Log "✅ Copiado .env.local a .env"
    } else {
        Error "No se encuentra .env.local. Créalo primero."
    }
}

# 4. Crear directorios necesarios
Log "Creando directorios..."
New-Item -ItemType Directory -Force -Path "nginx/ssl" | Out-Null
New-Item -ItemType Directory -Force -Path "logs/nginx" | Out-Null
New-Item -ItemType Directory -Force -Path "static" | Out-Null

# 5. Verificar certificados SSL (temporales para desarrollo)
if (-not (Test-Path "nginx/ssl/fullchain.pem") -or -not (Test-Path "nginx/ssl/privkey.pem")) {
    Warning "Generando certificados SSL temporales para desarrollo..."
    
    # Verificar si OpenSSL está disponible
    try {
        openssl version | Out-Null
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
            -keyout nginx/ssl/privkey.pem `
            -out nginx/ssl/fullchain.pem `
            -subj "/C=CO/ST=Antioquia/L=Bello/O=Rifa/CN=localhost" 2>$null
        Log "✅ Certificados SSL creados"
    } catch {
        Warning "OpenSSL no está disponible. Los certificados no se generaron."
        Warning "El sitio funcionará en HTTP (puerto 8080) pero no en HTTPS (puerto 443)"
        
        # Crear archivos vacíos para evitar errores
        New-Item -ItemType File -Force -Path "nginx/ssl/fullchain.pem" | Out-Null
        New-Item -ItemType File -Force -Path "nginx/ssl/privkey.pem" | Out-Null
    }
}

# 6. Detener contenedores anteriores
Log "Deteniendo contenedores anteriores..."
docker-compose down --remove-orphans 2>$null

# 7. Limpiar imágenes antiguas (opcional)
$cleanImages = Read-Host "¿Deseas limpiar imágenes antiguas? (s/N)"
if ($cleanImages -eq "s" -or $cleanImages -eq "S") {
    Log "Limpiando imágenes..."
    docker system prune -f
}

# 8. Construir imágenes
Log "Construyendo imagen Docker..."
Log "Esto puede tomar varios minutos la primera vez..."
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Error "Error al construir la imagen Docker. Revisa los logs arriba."
}

# 9. Iniciar servicios
Log "Iniciando servicios..."
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Error "Error al iniciar los servicios. Revisa los logs arriba."
}

# 10. Esperar a que la app esté lista
Log "Esperando a que la aplicación esté lista..."
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -TimeoutSec 5 2>$null
        if ($response.StatusCode -eq 200) {
            $ready = $true
        }
    } catch {
        $attempt++
    }
}

if (-not $ready) {
    Warning "La aplicación tardó mucho en responder. Verifica los logs."
} else {
    Log "✅ Aplicación lista y respondiendo"
}

# 11. Mostrar estado
Write-Host ""
Log "Estado de los servicios:"
docker-compose ps

# 12. Mostrar logs recientes
Write-Host ""
Log "Logs recientes:"
docker-compose logs --tail=20

# 13. Resumen
Write-Host ""
Write-ColorOutput Green "✅ =================================="
Write-ColorOutput Green "   DESPLIEGUE COMPLETADO"
Write-ColorOutput Green "=================================="
Write-Host ""
Write-Host "📊 URLs de acceso:" -ForegroundColor Cyan
Write-Host "   • Aplicación:     http://localhost:8080"
Write-Host "   • Panel Admin:    http://localhost:8080/admin/login"
Write-Host "   • Base de datos:  PostgreSQL en Neon (remota)"
Write-Host ""
Write-Host "📝 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   • Ver logs en vivo:    docker-compose logs -f"
Write-Host "   • Ver logs de app:     docker-compose logs -f app"
Write-Host "   • Reiniciar:           docker-compose restart"
Write-Host "   • Detener:             docker-compose down"
Write-Host "   • Ver estado:          docker-compose ps"
Write-Host "   • Entrar al contenedor: docker-compose exec app bash"
Write-Host ""

# Abrir navegador automáticamente
$openBrowser = Read-Host "¿Deseas abrir el navegador? (S/n)"
if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
    Start-Process "http://localhost:8080"
}