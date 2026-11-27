# Kiara

Asistente personal de IA con personalidad propia, avatar animado Live2D y voz. Corre en tu computadora como una página web local y usa la API de Claude como cerebro.

> **Estado: prototipo en pausa (v0.1).** El código está completo para una primera versión, pero **todavía no se ha probado una conversación real** porque faltan las claves de API. Ver [Etapa actual](#etapa-actual).

## Qué es

Kiara es una chica de 24 años: curiosa, inteligente, amable, algo mandona con cariño, muy chistosa, friki de la cultura pop, fan de la informática, de los datos curiosos y de la música de los 80s, 90s y 2000s. Le gusta contar cómo va su día, ayudar y preocuparse por ti.

| Pieza | Cómo funciona |
|---|---|
| **Cerebro** | API de Claude (`claude-opus-5-5` por defecto), con respuestas en streaming |
| **Personalidad** | `personalidad.md`, se carga como *system prompt*; se puede editar en cualquier momento |
| **Memoria** | Historial de la conversación guardado en disco + herramienta `recordar` con la que Kiara guarda datos importantes sobre ti |
| **Apariencia** | Modelo Live2D (muestra oficial *Miara*) que ocupa casi toda la ventana, de la cintura para arriba, con boca sincronizada a la voz. Si no carga, se usa un avatar SVG de respaldo |
| **Voz** | ElevenLabs (voz *Liz - Sweet & Warm Storyteller*) con sincronización de labios según el volumen del audio. Si no hay clave, usa la voz del navegador |
| **Oído** | Reconocimiento de voz del navegador (Chrome/Edge), con modo manos libres |

## Estructura

```
Kiara/
├── app.py              # Servidor Flask: chat con Claude, memoria y voz de ElevenLabs
├── personalidad.md     # Quién es Kiara (system prompt)
├── static/
│   ├── index.html      # Interfaz: avatar Live2D, chat, voz y micrófono
│   ├── lib/            # PixiJS + pixi-live2d-display (+ Cubism Core, se descarga aparte)
│   └── modelos/        # Modelo Live2D (se descarga aparte)
├── datos/              # Historial y memoria (se crea solo, no se sube a git)
├── .env.example        # Plantilla de configuración
├── iniciar.bat         # Abre Kiara en Windows con doble clic
└── requirements.txt
```

## Instalación

Requisitos: Python 3.10+ y Chrome o Edge (para el micrófono).

1. **Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

2. **Claves**: copia `.env.example` como `.env` y llena:
   - `ANTHROPIC_API_KEY`: en [console.anthropic.com](https://console.anthropic.com) → API Keys. Es prepago por uso, independiente de la suscripción de Claude.
   - `ELEVENLABS_API_KEY` (opcional): en [elevenlabs.io](https://elevenlabs.io) → Developers → API Keys. Agrega antes la voz *Liz* a **My Voices**.

3. **Archivos de Live2D** (no vienen en el repo por su licencia):
   - **Cubism Core**: descarga [live2dcubismcore.min.js](https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js) y guárdalo en `static/lib/`.
   - **Modelo Miara**: descárgalo de [Live2D Sample Data](https://www.live2d.com/en/download/sample-data/) y descomprímelo en `static/modelos/miara/`, de modo que exista `static/modelos/miara/runtime/miara_pro_t03.model3.json`.

4. **Ejecutar**
   ```bash
   python app.py
   ```
   y abre <http://localhost:5000>. En Windows también puedes usar `iniciar.bat`.

## Etapa actual

**v0.1, prototipo funcional en pausa.**

Hecho y verificado:
- [x] Personalidad de Kiara definida
- [x] Servidor con chat en streaming, memoria persistente y herramienta `recordar`
- [x] Avatar Live2D cargando sin errores, encuadre de la cintura para arriba, boca que se abre y cierra al hablar
- [x] Integración con ElevenLabs y respaldo con la voz del navegador
- [x] Mensajes claros cuando faltan claves (sin errores 500)

Pendiente:
- [ ] **Probar con claves reales**: no se ha probado aún una conversación con Claude ni la voz de ElevenLabs
- [ ] Confirmar que la voz *Liz* se encuentra por nombre y suena bien en español (si no, elegir una voz nativa en español)
- [ ] Decidir el modelo por costo: Opus 5.5 (~1–3 ¢ por mensaje) o Haiku 5.5 (mucho más barato y rápido)
- [ ] Activar caché del historial de conversación para bajar el costo de la API
- [ ] Ocultar al hada del modelo Miara, que en la animación de reposo pasa frente a la cara
- [ ] A futuro: modelo Live2D propio para Kiara (Miara es un modelo de muestra)

## Limitaciones conocidas

- El micrófono no funciona en Firefox ni en navegadores basados en él (Zen, etc.): usa Chrome o Edge.
- Con la voz del navegador, la boca se mueve al azar; con ElevenLabs sigue el volumen real del audio.

## Créditos y licencias

- Modelo **Miara**: muestra oficial de Live2D Inc. (ilustración: Sasamotoroko), bajo el [Free Material License Agreement](https://www.live2d.com/en/download/sample-data/). No se incluye en este repositorio.
- **Live2D Cubism Core**: © Live2D Inc., bajo su propia licencia. No se incluye en este repositorio.
- [PixiJS](https://pixijs.com) y [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display): licencia MIT.
