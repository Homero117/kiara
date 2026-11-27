# Kiara: contexto para Claude

Asistente personal de IA para Windows: personaje con personalidad (Kiara, 24 años), avatar Live2D animado, voz de ElevenLabs y comentarios espontáneos sobre lo que hace el usuario. Cerebro: API de Claude. Proyecto personal de Homero (GitHub `Homero117/kiara`, privado). Versión actual: **v0.2, prototipo en pausa**.

## Cómo trabajar con el dueño

- Habla siempre en **español** (México). El dueño no es programador de oficio: explica en lenguaje simple, sin jerga.
- Windows 11, pantalla con **escala 125 %** (lógico 1536×960, físico 1920×1200). Las capturas con `PIL.ImageGrab` están en píxeles físicos.
- Usa Zen (basado en Firefox) como navegador, así que el micrófono no funciona ahí. Para probar la página usa Chrome.
- **Nunca le pidas las claves en el chat.** Van en `.env`; dile cómo pegarlas él.
- Sube a GitHub solo cuando lo pida. Mensajes de commit en español.

## Arquitectura

```
app.py             Flask en 127.0.0.1:5000. Chat (SSE), memoria, comentarios espontáneos, voz ElevenLabs
personalidad.md    System prompt. Usa {usuario}, que se reemplaza con KIARA_USUARIO
static/index.html  Toda la interfaz en un archivo: Live2D, animación/expresiones, chat, voz, micrófono, modo escritorio
static/lib/        pixi.min.js (6.5.10), cubism4.min.js (pixi-live2d-display 0.4.0), live2dcubismcore.min.js (no en git)
static/modelos/    Modelo Miara (no en git)
escritorio/        Electron 45: main.js (ventana transparente + arranca app.py si no corre), preload.js
datos/             historial.json y memoria.json (no en git, datos personales)
instalar.ps1/.bat  Instalador para amigos (deps, Electron, descarga Live2D con aceptación de licencia, genera .env)
```

### Endpoints

| Ruta | Qué hace |
|---|---|
| `POST /api/chat` | Mensaje del usuario → respuesta en streaming (eventos SSE `texto`, `memoria`, `error`, `fin`) |
| `POST /api/espontaneo` | `{captura: bool}` → comentario por iniciativa propia; 204 si la ventana activa es la propia Kiara |
| `POST /api/voz` | Texto → MP3 de ElevenLabs; 503 si no hay clave (la página cae a la voz del sistema) |
| `GET /api/voz/estado`, `/api/config`, `/api/historial` | Estado de la voz, config (frecuencia, nombre), historial visible |

### Decisiones y por qué

- **Modelo**: `claude-opus-5-5` por defecto (`KIARA_MODELO`), `effort: low`, `client.beta.messages.stream` con `fallbacks="default"` (beta `server-side-fallback-2026-07-01`). Opus 5.5 no permite desactivar el thinking ni forzar `tool_choice`.
- **El historial se guarda solo como texto** (sin bloques de thinking ni tool_use): así se puede recortar a los últimos 60 mensajes sin romper el chequeo de edición de historial de *preserved thinking*. Dentro de un mismo turno sí se reenvía `final.content` completo.
- **Los avisos de comentario espontáneo van como mensaje `user`** con texto `[Aviso automático: ...]` y `"auto": true` en el historial (no se muestran). No se usa un mensaje `system` a mitad de conversación porque el historial termina en `assistant`, y ahí la API no lo permite.
- **Emociones por etiquetas** `[feliz]`, `[risa]`... al inicio de frase. La página las quita del texto visible y del TTS, y cambia la cara justo cuando esa frase empieza a sonar. Si no hay etiqueta, `emocionDe()` adivina por palabras clave.
- **Live2D sin las animaciones del modelo**: las escenas de Miara (Scene1-3) mueven todo el cuerpo y lo sacaban del cuadro. Se desactiva el grupo idle y toda la animación es procedural en `animar()`.
- **El hada del modelo está oculta** (`MOSTRAR_HADA = false`): tapaba la cara.
- **Archivos de Live2D fuera de git** por licencia (Free Material License / Cubism Core). El instalador los descarga tras pedir aceptación. URL del modelo: `https://cubism.live2d.com/sample-data/bin/miara/miara_en.zip`.

## Trampas conocidas (ya costaron tiempo)

- **pixi-live2d-display**: el método es `updateNaturalMovements` (plural) y se llama **antes** de la física. Por eso `animar()` lo reemplaza: así el pelo reacciona a la cabeza. `beforeModelUpdate` va después de la física.
- **Leer un parámetro después de un cuadro devuelve el valor viejo**: el SDK hace `loadParameters()` al final de cada cuadro. Para verificar la boca o las expresiones, mira la imagen, no `getParameterValueById`.
- **El modelo no trae grupos LipSync/EyeBlink** (vienen vacíos): el parpadeo y la boca los maneja `animar()`.
- **Servidores huérfanos en el puerto 5000**: detener una tarea en segundo plano puede dejar vivo `python app.py`, y Electron se queda con un servidor viejo que no tiene las rutas nuevas. Antes de probar, mata todos: `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? CommandLine -match 'app\.py' | % { Stop-Process -Id $_.ProcessId -Force }`.
- **Lanzar Electron**: usa `escritorio\node_modules\electron\dist\electron.exe .` con `Start-Process`. `npx electron .` en segundo plano se cerraba solo.
- **Electron 45 descarga su binario aparte**: después de `npm install` hay que correr `node node_modules\electron\install.js`.
- **El micrófono no funciona en Electron** (`webkitSpeechRecognition` necesita los servicios de Google Chrome). Solo funciona en la versión de navegador.
- **Al editar `index.html` con scripts**: hay varios `<script src=...></script>` antes del script principal. Busca `</script>` *después* de tu marcador o duplicarás la página (ya pasó).
- **Scripts largos por Bash heredoc** con comillas o backticks fallan; escríbelos a un archivo en el scratchpad y ejecútalos.
- **`instalar.ps1` debe guardarse con BOM UTF-8** (Windows PowerShell 5.1 rompe los acentos sin él), y escribe `.env` **sin** BOM (si no, la primera variable no se lee).
- El conector de ElevenLabs de Claude puede pedir volver a iniciar sesión (`/mcp`); la app no depende de él (usa su propia clave).

## Cómo probar

- **Backend sin gastar API**: `python -c "import app; c=app.app.test_client(); ..."`. Sin clave, `/api/chat` responde con un evento `error` claro, nunca 500.
- **JavaScript**: extrae el último `<script>` de `index.html` y corre `node --check`.
- **Visual en escritorio**: lanza Electron y toma capturas con `PIL.ImageGrab`. La ventana mide 600×780 lógicos en la esquina inferior derecha.
- **Visual en navegador**: Chrome en `http://localhost:5000` con la extensión Claude in Chrome.

## Estado y pendientes (v0.2)

Probado: carga del avatar, animación, encuadre sin cortes, ventana transparente sobre los programas, detección de ventana activa, capturas, errores sin claves, `.env` generado por el instalador, descargas del instalador.

**Nunca probado con claves reales**: conversación con Claude, comentarios espontáneos, emociones en vivo, voz de Liz.

Pendientes:
- [ ] Probar con claves reales y ajustar los valores de `EMOCIONES` si se ven exagerados
- [ ] Probar clics que traspasan, arrastre y botones del modo escritorio
- [ ] Caché del historial de conversación (ahora solo el system prompt tiene `cache_control`)
- [ ] Micrófono en escritorio (opción: Speech to Text de ElevenLabs vía `/api/escuchar`)
- [ ] Recordar posición de la ventana
- [ ] Modelo Live2D propio para Kiara (Miara es de muestra; su licencia no permite presentarla como personaje propio)
