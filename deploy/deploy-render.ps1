# Deploy PyForge to Render via API
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
$Root = (Get-Location).Path

foreach ($keysFile in @(
    (Join-Path $Root "api-keys.txt"),
    "D:\DividendFlowPK\api-keys.txt"
)) {
    if (-not $env:RENDER_API_KEY -and (Test-Path $keysFile)) {
        Get-Content $keysFile | ForEach-Object {
            if ($_ -match '^\s*RENDER_API_KEY=(.+)$') { $env:RENDER_API_KEY = $matches[1].Trim() }
        }
        if ($env:RENDER_API_KEY) { break }
    }
}

if (-not $env:RENDER_API_KEY) {
    Write-Host "RENDER_API_KEY not set. Add to api-keys.txt or environment." -ForegroundColor Red
    exit 1
}

$groqKey = $env:GROQ_API_KEY
if (-not $groqKey -and (Test-Path ".env")) {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*GROQ_API_KEY=(.+)$') { $groqKey = $matches[1].Trim() }
    }
}

$headers = @{
    Authorization  = "Bearer $env:RENDER_API_KEY"
    Accept         = "application/json"
    "Content-Type" = "application/json"
}

$repo = "https://github.com/AmmarJamshed/pyforge"
$branch = "main"
$ownerId = "tea-d0s1f0e3jp1c73e7qri0"
$serviceNames = @("pyforge-api", "pyforge-web")

Write-Host "=== PyForge Render deploy ===" -ForegroundColor Cyan

$resp = Invoke-RestMethod -Uri "https://api.render.com/v1/services?limit=100" -Headers $headers -Method Get
$services = if ($resp -is [array]) { $resp } else { @($resp) }

if (-not ($services | Where-Object { $_.service.name -eq "pyforge-api" })) {
    Write-Host "Creating pyforge-api ..." -ForegroundColor Green
    $apiBody = @{
        type       = "web_service"
        name       = "pyforge-api"
        ownerId    = $ownerId
        repo       = $repo
        branch     = $branch
        autoDeploy = "yes"
        rootDir    = "backend"
        envVars    = @(
            @{ key = "GROQ_API_KEY"; value = $groqKey }
            @{ key = "DOCKER_BUILDS_ENABLED"; value = "false" }
            @{ key = "CORS_ORIGINS"; value = "https://pyforge-web.onrender.com,*" }
        )
        serviceDetails = @{
            runtime         = "docker"
            plan            = "free"
            region          = "oregon"
            healthCheckPath = "/api/health"
            dockerfilePath  = "Dockerfile.cloud"
            dockerContext   = "."
        }
    } | ConvertTo-Json -Depth 6
    Invoke-RestMethod -Uri "https://api.render.com/v1/services" -Headers $headers -Method Post -Body $apiBody | Out-Null
    $resp = Invoke-RestMethod -Uri "https://api.render.com/v1/services?limit=100" -Headers $headers -Method Get
    $services = if ($resp -is [array]) { $resp } else { @($resp) }
}

if (-not ($services | Where-Object { $_.service.name -eq "pyforge-web" })) {
    Write-Host "Creating pyforge-web ..." -ForegroundColor Green
    $webBody = @{
        type       = "static_site"
        name       = "pyforge-web"
        ownerId    = $ownerId
        repo       = $repo
        branch     = $branch
        autoDeploy = "yes"
        rootDir    = "frontend"
        envVars    = @(
            @{ key = "VITE_API_URL"; value = "https://pyforge-api.onrender.com" }
            @{ key = "VITE_WS_URL"; value = "https://pyforge-api.onrender.com" }
        )
        serviceDetails = @{
            buildCommand = "npm install && npm run build"
            publishPath  = "dist"
        }
    } | ConvertTo-Json -Depth 6
    Invoke-RestMethod -Uri "https://api.render.com/v1/services" -Headers $headers -Method Post -Body $webBody | Out-Null
    $resp = Invoke-RestMethod -Uri "https://api.render.com/v1/services?limit=100" -Headers $headers -Method Get
    $services = if ($resp -is [array]) { $resp } else { @($resp) }
}

foreach ($name in $serviceNames) {
    $wrap = $services | Where-Object { $_.service.name -eq $name } | Select-Object -First 1
    if (-not $wrap) { continue }
    $sid = $wrap.service.id
    if ($name -eq "pyforge-api" -and $groqKey) {
        $envBody = @{ value = $groqKey } | ConvertTo-Json
        try {
            Invoke-RestMethod -Uri "https://api.render.com/v1/services/$sid/env-vars/GROQ_API_KEY" -Headers $headers -Method Put -Body $envBody | Out-Null
        } catch { }
    }
    Write-Host "Deploying $name ($sid) ..." -ForegroundColor Green
    Invoke-RestMethod -Uri "https://api.render.com/v1/services/$sid/deploys" -Headers $headers -Method Post -Body "{}" | Out-Null
}

Write-Host "`nLive URLs:" -ForegroundColor Cyan
Write-Host "  App:  https://pyforge-web.onrender.com"
Write-Host "  API:  https://pyforge-api.onrender.com/docs"
