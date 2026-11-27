# Instalador de Kiara para Windows.
# Se ejecuta con doble clic en instalar.bat. Se puede volver a correr sin problema: salta lo que ya está listo.
$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
Set-Location $raiz

function Titulo($t) { Write-Host ""; Write-Host "== $t ==" -ForegroundColor Magenta }
function Ok($t)     { Write-Host "  [OK] $t" -ForegroundColor Green }
function Aviso($t)  { Write-Host "  [!]  $t" -ForegroundColor Yellow }
function Pregunta-SiNo($t) {
  do { $r = (Read-Host "  $t (s/n)").Trim().ToLower() } until ($r -in @("s", "si", "sí", "n", "no"))
  return $r.StartsWith("s")
}
function Leer-Secreto($t) {
  $seguro = Read-Host "  $t" -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr).Trim() }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
function Existe($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Host ""
Write-Host "  Instalador de Kiara" -ForegroundColor Cyan
Write-Host "  Asistente de IA con avatar Live2D y voz" -ForegroundColor Cyan

# ---------- 1. Python y Node.js ----------
Titulo "1/5  Programas necesarios"
$faltan = @()
if (Existe "python") { Ok ("Python: " + (python --version 2>&1)) } else { $faltan += @{ nombre = "Python"; id = "Python.Python.3.12" } }
if (Existe "node")   { Ok ("Node.js: " + (node --version)) }      else { $faltan += @{ nombre = "Node.js"; id = "OpenJS.NodeJS.LTS" } }
if ($faltan.Count -gt 0) {
  foreach ($f in $faltan) { Aviso "Falta $($f.nombre)" }
  if ((Existe "winget") -and (Pregunta-SiNo "¿Los instalo con winget?")) {
    foreach ($f in $faltan) { winget install -e --id $f.id --accept-package-agreements --accept-source-agreements }
    Write-Host ""
    Aviso "Listo. CIERRA esta ventana y vuelve a abrir instalar.bat para continuar."
  } else {
    Aviso "Instálalos desde https://www.python.org/downloads/ y https://nodejs.org (marca 'Add to PATH') y vuelve a abrir instalar.bat."
  }
  Read-Host "  Presiona Enter para salir"; exit 1
}

# ---------- 2. Dependencias ----------
Titulo "2/5  Dependencias"
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Falló pip install" }
Ok "Paquetes de Python (anthropic, flask, pillow)"
Push-Location escritorio
if (-not (Test-Path "node_modules\electron\dist\electron.exe")) {
  Write-Host "  Descargando Electron (unos 100 MB, puede tardar)..."
  npm install --silent --no-fund --no-audit
  node node_modules\electron\install.js   # esta versión de Electron baja el programa aparte
}
Pop-Location
if (-not (Test-Path "escritorio\node_modules\electron\dist\electron.exe")) { throw "Falló la instalación de Electron" }
Ok "Electron (modo escritorio)"

# ---------- 3. Archivos de Live2D ----------
Titulo "3/5  Avatar Live2D"
$core = "static\lib\live2dcubismcore.min.js"
$modelo = "static\modelos\miara\runtime\miara_pro_t03.model3.json"
if ((Test-Path $core) -and (Test-Path $modelo)) {
  Ok "Ya estaban descargados"
} else {
  Write-Host "  Kiara usa archivos oficiales de Live2D Inc. que no vienen en el proyecto por su licencia:"
  Write-Host "   - Live2D Cubism Core (motor del avatar)"
  Write-Host "   - Modelo de muestra 'Miara' (Free Material License Agreement)"
  Write-Host "  Licencias: https://www.live2d.com/en/download/sample-data/"
  Write-Host "  Uso personal permitido. No se pueden redistribuir ni presentar como personaje propio."
  if (Pregunta-SiNo "¿Aceptas las licencias de Live2D y los descargo?") {
    New-Item -ItemType Directory -Force "static\lib", "static\modelos" | Out-Null
    if (-not (Test-Path $core)) {
      Invoke-WebRequest "https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js" -OutFile $core -UseBasicParsing
    }
    if (-not (Test-Path $modelo)) {
      $tmp = Join-Path $env:TEMP "kiara_miara_$(Get-Random)"
      New-Item -ItemType Directory -Force $tmp | Out-Null
      Write-Host "  Descargando modelo Miara (40 MB)..."
      Invoke-WebRequest "https://cubism.live2d.com/sample-data/bin/miara/miara_en.zip" -OutFile "$tmp\miara_en.zip" -UseBasicParsing
      Expand-Archive "$tmp\miara_en.zip" -DestinationPath "static\modelos\miara" -Force
      Remove-Item $tmp -Recurse -Force
    }
    if ((Test-Path $core) -and (Test-Path $modelo)) { Ok "Avatar listo" } else { throw "No se pudieron descargar los archivos de Live2D" }
  } else {
    Aviso "Sin estos archivos Kiara usará un avatar dibujado sencillo. Puedes volver a correr el instalador después."
  }
}

# ---------- 4. Configuración (.env) ----------
Titulo "4/5  Configuración"
$crear = $true
if (Test-Path ".env") { $crear = Pregunta-SiNo "Ya existe una configuración (.env). ¿La reemplazo?" }
if ($crear) {
  $nombre = (Read-Host "  ¿Cómo quieres que te llame Kiara? (tu nombre o apodo)").Trim()
  if (-not $nombre) { $nombre = "amigo" }

  Write-Host ""
  Write-Host "  Clave de la API de Claude (necesaria para que Kiara conteste)."
  Write-Host "  Sácala en https://console.anthropic.com -> API Keys (empieza con sk-ant-). Es prepago por uso."
  Write-Host "  No se ve mientras la pegas; pégala con clic derecho y Enter. Déjala vacía para ponerla después."
  $claude = Leer-Secreto "Clave de Claude"

  Write-Host ""
  Write-Host "  Clave de ElevenLabs (opcional, para la voz de Liz). Sin ella usa la voz de Windows."
  Write-Host "  Sácala en https://elevenlabs.io -> Developers -> API Keys, y agrega la voz Liz a 'My Voices'."
  $eleven = Leer-Secreto "Clave de ElevenLabs (Enter para omitir)"

  Write-Host ""
  Write-Host "  ¿Qué modelo de Claude usar?"
  Write-Host "   1) Haiku 5.5  - rápido y muy barato (~1 dólar al mes platicando diario). Recomendado para probar."
  Write-Host "   2) Opus 5.5   - más inteligente, ~15-45 dólares al mes platicando diario."
  do { $m = (Read-Host "  Elige 1 o 2").Trim() } until ($m -in @("1", "2"))
  $modeloClaude = if ($m -eq "1") { "claude-haiku-5-5" } else { "claude-opus-5-5" }

  $env_ = @"
# Configuración de Kiara (generada por instalar.bat). No compartas este archivo: tiene tus claves.
KIARA_USUARIO=$nombre
ANTHROPIC_API_KEY=$claude
KIARA_MODELO=$modeloClaude
ELEVENLABS_API_KEY=$eleven
# ELEVENLABS_VOZ=Liz
# KIARA_ESPONTANEO_MIN=8
# KIARA_ESPONTANEO_MAX=20
"@
  [IO.File]::WriteAllText((Join-Path $raiz ".env"), $env_, (New-Object Text.UTF8Encoding($false)))
  Ok "Configuración guardada en .env"
  if (-not $claude) { Aviso "Sin clave de Claude, Kiara no podrá contestar. Agrégala después en el archivo .env" }
}

# ---------- 5. Listo ----------
Titulo "5/5  ¡Listo!"
Write-Host "  Para abrir a Kiara:"
Write-Host "   - Sobre tus programas:   doble clic en iniciar-escritorio.bat"
Write-Host "   - En el navegador:       doble clic en iniciar.bat (aquí funciona el micrófono, usa Chrome o Edge)"
if (Pregunta-SiNo "¿La abro ahora en modo escritorio?") {
  Start-Process -FilePath (Join-Path $raiz "escritorio\node_modules\electron\dist\electron.exe") -ArgumentList "." -WorkingDirectory (Join-Path $raiz "escritorio")
}
