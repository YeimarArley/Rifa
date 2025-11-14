# ============================================
# PRUEBA LOCAL SIMPLE - SIN DOCKER
# ============================================

Write-Host ""
Write-Host "🚀 ====================================" -ForegroundColor Cyan
Write-Host "   PRUEBA LOCAL - SIN DOCKER" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que estamos en venv
Write-Host "1️⃣ Verificando entorno virtual..." -ForegroundColor Green
$pythonPath = (Get-Command python).Source
if ($pythonPath -notmatch "venv") {
    Write-Host "❌ No estás en el entorno virtual" -ForegroundColor Red
    Write-Host "Ejecuta primero: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Entorno virtual activo: $pythonPath" -ForegroundColor Green
Write-Host ""

# 2. Verificar archivo .env
Write-Host "2️⃣ Verificando archivo .env..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.local") {
        Write-Host "📋 Copiando .env.local a .env..." -ForegroundColor Yellow
        Copy-Item ".env.local" ".env"
    } elseif (Test-Path ".env.production") {
        Write-Host "⚠️  Solo encontré .env.production" -ForegroundColor Yellow
        $use = Read-Host "¿Usar .env.production para pruebas? (s/N)"
        if ($use -eq "s" -or $use -eq "S") {
            Copy-Item ".env.production" ".env"
        } else {
            Write-Host "❌ Necesitas un archivo .env" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ No se encontró ningún archivo .env" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
Write-Host ""

# 3. Instalar dependencias
Write-Host "3️⃣ Instalando/verificando dependencias..." -ForegroundColor Green
pip install flask-talisman --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error instalando flask-talisman" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencias instaladas" -ForegroundColor Green
Write-Host ""

# 4. Verificar correcciones en server.py
Write-Host "4️⃣ Verificando correcciones en server.py..." -ForegroundColor Green
$serverContent = Get-Content "server.py" -Raw

if ($serverContent -match "from psycopg.extras import") {
    Write-Host "❌ server.py necesita corrección" -ForegroundColor Red
    Write-Host ""
    Write-Host "CORRIGE MANUALMENTE:" -ForegroundColor Yellow
    Write-Host "Línea 10 en server.py" -ForegroundColor Yellow
    Write-Host "Cambiar: from psycopg.extras import RealDictCursor" -ForegroundColor Red
    Write-Host "Por:     from psycopg.rows import dict_row" -ForegroundColor Green
    Write-Host ""
    $continue = Read-Host "¿Ya corregiste el archivo? (s/N)"
    if ($continue -ne "s" -and $continue -ne "S") {
        exit 1
    }
}
Write-Host "✅ server.py parece correcto" -ForegroundColor Green
Write-Host ""

# 5. Iniciar servidor
Write-Host "5️⃣ Iniciando servidor Flask..." -ForegroundColor Green
Write-Host ""
Write-Host "📊 URLs de acceso:" -ForegroundColor Cyan
Write-Host "   • Aplicación:  http://localhost:8080" -ForegroundColor White
Write-Host "   • Admin:       http://localhost:8080/admin/login" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""
Write-Host "───────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Ejecutar servidor
python server.py