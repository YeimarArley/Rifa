# ============================================
# DESPLIEGUE CON DOCKER - WINDOWS
# ============================================

$ErrorActionPreference = "Stop"

function Write-Log {
    param($Message, $Color = "Green")
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

Write-Host ""
Write-Host "🐳 ====================================" -ForegroundColor Cyan
Write-Host "   DESPLIEGUE CON DOCKER" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Docker Desktop
Write-Log "Verificando Docker Desktop..."
try {
    docker --version | Out-Null
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no está corriendo"
    }
} catch {
    Write-Host "❌ Docker Desktop no está corriendo" -ForegroundColor Red
    Write-Host "1. Abre Docker Desktop" -ForegroundColor Yellow
    Write-Host "2. Espera a que el icono esté verde" -ForegroundColor Yellow
    Write-Host "3. Ejecuta este script de nuevo" -ForegroundColor Yellow
    exit 1
}
Write-Log "✅ Docker Desktop está corriendo"
Write-Host ""

# 2. Verificar .env
Write-Log "Verificando configuración..."
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.production") {
        Write-Host "📋 Usando .env.production" -ForegroundColor Yellow
        Copy-Item ".env.production" ".env"
    } else {
        Write-Host "❌ No se encontró archivo .env" -ForegroundColor Red
        exit 1
    }
}
Write-Log "✅ Configuración lista"
Write-Host ""

# 3. Crear directorios
Write-Log "Creando directorios..."
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
Write-Log "✅ Directorios creados"
Write-Host ""

# 4. Detener contenedores anteriores
Write-Log "Deteniendo contenedores anteriores..."
docker-compose down 2>$null
Write-Host ""

# 5. Limpiar (opcional)
$clean = Read-Host "¿Limpiar imágenes antiguas? (s/N)"
if ($clean -eq "s" -or $clean -eq "S") {
    Write-Log "Limpiando sistema Docker..." "Yellow"
    docker system prune -f
}
Write-Host ""

# 6. Construir imagen
Write-Log "Construyendo imagen Docker..."
Write-Host "Esto puede tomar 3-5 minutos..." -ForegroundColor Yellow
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error construyendo imagen" -ForegroundColor Red
    exit 1
}
Write-Log "✅ Imagen construida"
Write-Host ""

# 7. Iniciar contenedores
Write-Log "Iniciando contenedores..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error iniciando contenedores" -ForegroundColor Red
    exit 1
}
Write-Log "✅ Contenedores iniciados"
Write-Host ""

# 8. Esperar a que la app responda
Write-Log "Esperando a que la aplicación esté lista..."
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
        }
    } catch {
        $attempt++
        Write-Host "." -NoNewline
    }
}

Write-Host ""
if ($ready) {
    Write-Log "✅ Aplicación lista y respondiendo"
} else {
    Write-Host "⚠️  La aplicación tardó en responder" -ForegroundColor Yellow
    Write-Host "Verifica los logs: docker-compose logs app" -ForegroundColor Yellow
}
Write-Host ""

# 9. Estado final
Write-Log "Estado de contenedores:"
docker-compose ps
Write-Host ""

Write-Log "Logs recientes:"
docker-compose logs --tail=15 app
Write-Host ""

# 10. Resumen
Write-Host "✅ ====================================" -ForegroundColor Green
Write-Host "   DESPLIEGUE COMPLETADO" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 URLs de acceso:" -ForegroundColor Cyan
Write-Host "   • Aplicación:  http://localhost:8080" -ForegroundColor White
Write-Host "   • Admin:       http://localhost:8080/admin/login" -ForegroundColor White
Write-Host ""
Write-Host "📝 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f        # Ver logs en vivo" -ForegroundColor White
Write-Host "   docker-compose logs -f app    # Solo logs de la app" -ForegroundColor White
Write-Host "   docker-compose restart        # Reiniciar" -ForegroundColor White
Write-Host "   docker-compose down           # Detener todo" -ForegroundColor White
Write-Host ""

$open = Read-Host "¿Abrir navegador? (S/n)"
if ($open -ne "n" -and $open -ne "N") {
    Start-Process "http://localhost:8080"
}