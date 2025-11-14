# ============================================
# CHECKLIST PRE-DEPLOY A RAILWAY
# ============================================

Write-Host ""
Write-Host "🔍 VERIFICANDO ARCHIVOS PARA RAILWAY..." -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# 1. Verificar Dockerfile
Write-Host "1️⃣ Verificando Dockerfile..." -NoNewline
if (Test-Path "Dockerfile") {
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ❌ FALTA" -ForegroundColor Red
    $allGood = $false
}

# 2. Verificar requirements.txt
Write-Host "2️⃣ Verificando requirements.txt..." -NoNewline
if (Test-Path "requirements.txt") {
    $content = Get-Content "requirements.txt" -Raw
    if ($content -match "flask-talisman") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  Falta flask-talisman" -ForegroundColor Yellow
        Write-Host "   Agregando flask-talisman..." -ForegroundColor Yellow
        Add-Content "requirements.txt" "`nflask-talisman==1.1.0"
        Write-Host "   ✅ Agregado" -ForegroundColor Green
    }
} else {
    Write-Host " ❌ FALTA" -ForegroundColor Red
    $allGood = $false
}

# 3. Verificar server.py
Write-Host "3️⃣ Verificando server.py..." -NoNewline
if (Test-Path "server.py") {
    $content = Get-Content "server.py" -Raw
    if ($content -match "from psycopg.extras import") {
        Write-Host " ⚠️  Necesita corrección" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   ❌ ENCONTRADO: from psycopg.extras import RealDictCursor" -ForegroundColor Red
        Write-Host "   ✅ CAMBIAR A: from psycopg.rows import dict_row" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Línea ~10 en server.py" -ForegroundColor Yellow
        $allGood = $false
    } else {
        Write-Host " ✅" -ForegroundColor Green
    }
} else {
    Write-Host " ❌ FALTA" -ForegroundColor Red
    $allGood = $false
}

# 4. Verificar .env.production
Write-Host "4️⃣ Verificando .env.production..." -NoNewline
if (Test-Path ".env.production") {
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ⚠️  No existe (crearemos uno)" -ForegroundColor Yellow
}

# 5. Verificar .dockerignore
Write-Host "5️⃣ Verificando .dockerignore..." -NoNewline
if (Test-Path ".dockerignore") {
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Recomendado crear uno" -ForegroundColor Yellow
}

# 6. Verificar estructura app/
Write-Host "6️⃣ Verificando carpeta app/..." -NoNewline
if (Test-Path "app") {
    if (Test-Path "app/db.py") {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  Falta app/db.py" -ForegroundColor Yellow
        $allGood = $false
    }
} else {
    Write-Host " ❌ FALTA carpeta app/" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""

if ($allGood) {
    Write-Host "✅ TODO LISTO PARA RAILWAY" -ForegroundColor Green
    Write-Host ""
    Write-Host "Siguiente paso: Sube tu código a GitHub" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  CORRIGE LOS ERRORES ANTES DE CONTINUAR" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Después ejecuta este script de nuevo" -ForegroundColor Cyan
}

Write-Host ""