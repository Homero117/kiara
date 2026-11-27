# Kiara

Asistente personal de IA con personalidad propia, avatar animado Live2D y voz. Vive en tu escritorio, encima de tus programas y sin fondo, y de vez en cuando comenta por su cuenta lo que estás haciendo. Usa la API de Claude como cerebro.

> **Estado: prototipo en pausa (v0.2).** El código está completo y el avatar se probó en el escritorio, pero **todavía no se ha probado una conversación real** porque faltan las claves de API. Ver [Etapa actual](#etapa-actual).

## Qué es

Kiara es una chica de 24 años: curiosa, inteligente, amable, algo mandona con cariño, muy chistosa, friki de la cultura pop, fan de la informática, de los datos curiosos y de la música de los 80s, 90s y 2000s. Le gusta contar cómo va su día, ayudar y preocuparse por ti.

| Pieza | Cómo funciona |
|---|---|
| **Cerebro** | API de Claude (`claude-opus-5-5` por defecto), con respuestas en streaming |
| **Personalidad** | `personalidad.md`, se carga como *system prompt*; se puede editar en cualquier momento |
| **Memoria** | Historial de la conversación guardado en disco + herramienta `recordar` con la que Kiara guarda datos importantes sobre ti |
| **Apariencia** | Modelo Live2D (muestra oficial *Miara*) con animación propia: respira, parpadea, mueve los ojos, sigue el mouse con la mirada, balancea la cabeza y asiente al hablar |
| **Expresiones** | Kiara marca su emoción en cada frase (`[feliz]`, `[risa]`, `[sorpresa]`, `[pensando]`, `[curiosa]`, `[triste]`, `[preocupada]`, `[picara]`, `[enojada]`) y su cara cambia al decirla. Las etiquetas no se ven ni se leen en voz alta |
| **Voz** | ElevenLabs (voz *Liz - Sweet & Warm Storyteller*) con boca sincronizada al volumen del audio. Si no hay clave, usa la voz del sistema |
| **Oído** | Reconocimiento de voz del navegador (Chrome/Edge), con modo manos libres |
| **Iniciativa** | Cada 8–20 min mira qué programa y ventana tienes activos y suelta un dato curioso, un chiste, un comentario o una opinión. Opcionalmente ve una captura de pantalla |

## Dos formas de usarla

- **De escritorio** (`iniciar-escritorio.bat`): ventana transparente y siempre encima de tus programas, en la esquina inferior derecha. Los clics en las partes vacías pasan a los programas de abajo. Al pasar el mouse arriba de ella aparece una barra: ✥ mover, ⌨️ chat, 🔊 voz, 💬 comentarios espontáneos, 📸 capturas, ✕ cerrar. Lo que dice aparece en un globo de texto.
- **En el navegador** (`iniciar.bat` o <http://localhost:5000>): ventana completa con Kiara grande y un chat abajo. Aquí sí funciona el micrófono.

## Estructura

```
Kiara/
├── app.py                  # Servidor Flask: chat con Claude, memoria, comentarios espontáneos y voz de ElevenLabs
├── personalidad.md         # Quién es Kiara (system prompt)
├── static/
│   ├── index.html          # Interfaz: avatar Live2D, expresiones, chat, voz, micrófono y modo escritorio
│   ├── lib/                # PixiJS + pixi-live2d-display (+ Cubism Core, se descarga aparte)
│   └── modelos/            # Modelo Live2D (se descarga aparte)
├── escritorio/             # App de Electron: ventana transparente sobre tus programas
│   ├── main.js
│   └── preload.js
├── datos/                  # Historial y memoria (se crea solo, no se sube a git)
├── .env.example            # Plantilla de configuración
├── iniciar.bat             # Abre Kiara en el navegador
├── iniciar-escritorio.bat  # Abre Kiara sobre tus programas
└── requirements.txt
```

## Instalación

Requisitos: Windows, Python 3.10+, Node.js 18+ (para el modo escritorio) y Chrome o Edge (para el micrófono).

1. **Dependencias**
   ```bash
   pip install -r requirements.txt
   cd escritorio && npm install
   ```

2. **Claves**: copia `.env.example` como `.env` y llena:
   - `ANTHROPIC_API_KEY`: en [console.anthropic.com](https://console.anthropic.com) → API Keys. Es prepago por uso, independiente de la suscripción de Claude.
   - `ELEVENLABS_API_KEY` (opcional): en [elevenlabs.io](https://elevenlabs.io) → Developers → API Keys. Agrega antes la voz *Liz* a **My Voices**.

3. **Archivos de Live2D** (no vienen en el repo por su licencia):
   - **Cubism Core**: descarga [live2dcubismcore.min.js](https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js) y guárdalo en `static/lib/`.
   - **Modelo Miara**: descárgalo de [Live2D Sample Data](https://www.live2d.com/en/download/sample-data/) y descomprímelo en `static/modelos/miara/`, de modo que exista `static/modelos/miara/runtime/miara_pro_t03.model3.json`.

4. **Ejecutar**: doble clic en `iniciar-escritorio.bat` (arranca el servidor solo) o en `iniciar.bat` para la versión de navegador.

### Ajustes en `.env`

| Variable | Para qué |
|---|---|
| `KIARA_MODELO` | Modelo de Claude. `claude-haiku-5-5` es mucho más barato y rápido |
| `KIARA_ESPONTANEO_MIN` / `KIARA_ESPONTANEO_MAX` | Cada cuántos minutos comenta por su cuenta (por defecto 8 a 20) |
| `ELEVENLABS_VOZ` / `ELEVENLABS_VOICE_ID` | Qué voz usar (por defecto busca "Liz") |
| `ELEVENLABS_MODELO` | `eleven_multilingual_v2` (calidad) o `eleven_flash_v2_5` (rapidez) |

## Privacidad

- Los comentarios espontáneos envían a Claude el **nombre del programa y el título de la ventana activa**.
- Con 📸 activado (apagado por defecto) también envían una **captura de tu pantalla**, que puede incluir información privada. Úsalo con cuidado.
- El historial y la memoria se guardan solo en tu computadora (`datos/`).

## Etapa actual

**v0.2, prototipo funcional en pausa.**

Hecho y verificado:
- [x] Personalidad de Kiara definida, con etiquetas de emoción
- [x] Servidor con chat en streaming, memoria persistente y herramienta `recordar`
- [x] Avatar Live2D con animación propia y expresiones; sin cortes al moverse
- [x] Modo escritorio: ventana transparente sobre los programas (probado en Windows)
- [x] Detección de la ventana activa y capturas de pantalla para los comentarios espontáneos
- [x] Integración con ElevenLabs y respaldo con la voz del sistema
- [x] Mensajes claros cuando faltan claves (sin errores 500)

Pendiente:
- [ ] **Probar con claves reales**: aún no se ha probado una conversación con Claude, los comentarios espontáneos ni la voz de ElevenLabs
- [ ] Revisar en vivo que las expresiones se vean bien (los valores de cada emoción son estimados)
- [ ] Probar los clics que traspasan la ventana, el arrastre y los botones del modo escritorio
- [ ] Confirmar que la voz *Liz* se encuentra por nombre y suena bien en español
- [ ] Decidir el modelo por costo: Opus 5.5 (~1–3 ¢ por mensaje) o Haiku 5.5 (mucho más barato y rápido)
- [ ] Activar caché del historial de conversación para bajar el costo de la API
- [ ] Micrófono en el modo escritorio (Electron no trae el reconocimiento de voz de Chrome; opción: Speech to Text de ElevenLabs)
- [ ] Recordar la posición de la ventana al cerrarla
- [ ] A futuro: modelo Live2D propio para Kiara (Miara es un modelo de muestra)

## Limitaciones conocidas

- El micrófono solo funciona en la versión de navegador con Chrome o Edge (no en Firefox, Zen ni en el modo escritorio).
- Con la voz del sistema, la boca se mueve al azar; con ElevenLabs sigue el volumen real del audio.
- El hada que trae el modelo Miara está oculta (le tapaba la cara); se activa con `MOSTRAR_HADA` en `static/index.html`.

## Créditos y licencias

- Modelo **Miara**: muestra oficial de Live2D Inc. (ilustración: Sasamotoroko), bajo el [Free Material License Agreement](https://www.live2d.com/en/download/sample-data/). No se incluye en este repositorio.
- **Live2D Cubism Core**: © Live2D Inc., bajo su propia licencia. No se incluye en este repositorio.
- [PixiJS](https://pixijs.com) y [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display): licencia MIT.
- [Electron](https://www.electronjs.org): licencia MIT.
